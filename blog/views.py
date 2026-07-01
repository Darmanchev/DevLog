from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from .models import Category, Comment, Post, Tag
from .forms import PostForm, CommentForm
from .search import SORT_OPTIONS, normalize_sort, published_posts_queryset, search_posts


def is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def sort_options_for_request(request, current_sort):
    options = []
    for value, label in SORT_OPTIONS.items():
        params = request.GET.copy()
        params.pop('page', None)
        params['sort'] = value
        options.append({
            'value': value,
            'label': label,
            'url': f'{request.path}?{params.urlencode()}',
            'is_active': value == current_sort,
        })
    return options


class PostListView(ListView):
    # Как переменная будет называться в шаблоне (по умолчанию object_list)
    context_object_name = 'posts'
    # Какой шаблон использовать
    template_name = 'blog/post_list.html'
    paginate_by = 6

    def get_queryset(self):
        self.current_sort = normalize_sort(self.request.GET.get('sort', ''))
        return search_posts(
            query=self.request.GET.get('q', ''),
            category_slug=self.request.GET.get('category', ''),
            tag_slug=self.request.GET.get('tag', ''),
            sort=self.current_sort,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['current_sort'] = getattr(self, 'current_sort', normalize_sort(self.request.GET.get('sort', '')))
        context['sort_options'] = sort_options_for_request(self.request, context['current_sort'])
        category_slug = self.request.GET.get('category', '').strip()
        tag_slug = self.request.GET.get('tag', '').strip()
        context['selected_category'] = Category.objects.filter(slug=category_slug).first()
        context['selected_tag'] = Tag.objects.filter(slug=tag_slug).first()
        context['results_count'] = context['paginator'].count if context.get('paginator') else len(context['posts'])
        context['canonical_url'] = self.request.build_absolute_uri(self.request.path)
        context['meta_description'] = 'Свежие публикации, заметки и обсуждения сообщества BlogPortal.'
        return context


class CategoryPostListView(PostListView):
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_category'] = self.category
        context['selected_tag'] = None
        return context


class TagPostListView(PostListView):
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return super().get_queryset().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_category'] = None
        context['selected_tag'] = self.tag
        return context


class AuthorPostListView(ListView):
    context_object_name = 'posts'
    template_name = 'blog/author_detail.html'
    paginate_by = 6

    def dispatch(self, request, *args, **kwargs):
        self.author = get_object_or_404(
            get_user_model(),
            username=self.kwargs['username'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.current_sort = normalize_sort(self.request.GET.get('sort', ''))
        return search_posts(
            query=self.request.GET.get('q', ''),
            sort=self.current_sort,
            queryset=published_posts_queryset().filter(author=self.author),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.author, 'profile', None)
        context['author_profile'] = profile
        context['profile_user'] = self.author
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['current_sort'] = self.current_sort
        context['sort_options'] = sort_options_for_request(self.request, self.current_sort)
        context['results_count'] = context['paginator'].count if context.get('paginator') else len(context['posts'])
        context['author_posts_count'] = published_posts_queryset().filter(author=self.author).count()
        context['author_comments_count'] = Comment.objects.filter(
            post__author=self.author,
            is_deleted=False,
        ).count()
        context['canonical_url'] = self.request.build_absolute_uri(self.request.path)
        context['meta_description'] = f'Публикации автора {self.author.username} на BlogPortal.'
        return context


class PostDetailView(DetailView):
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    # Переопределяем выборку, чтобы по прямому URL нельзя было открыть черновик
    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'category').prefetch_related('tags')
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user)
            )
        return queryset.filter(status=Post.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.filter(is_deleted=False).select_related('author')
        context['likes_count'] = self.object.likes.count()
        context['is_liked'] = (
            self.request.user.is_authenticated
            and self.object.likes.filter(pk=self.request.user.pk).exists()
        )
        related_filter = Q()
        tag_ids = list(self.object.tags.values_list('id', flat=True))
        if self.object.category_id:
            related_filter |= Q(category=self.object.category)
        if tag_ids:
            related_filter |= Q(tags__in=tag_ids)
        if related_filter:
            context['related_posts'] = Post.objects.filter(
                related_filter,
                status=Post.Status.PUBLISHED,
            ).exclude(
                pk=self.object.pk,
            ).select_related(
                'author',
                'category',
            ).prefetch_related('tags').distinct()[:3]
        else:
            context['related_posts'] = Post.objects.none()
        return context



class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault('status', Post.Status.PUBLISHED)
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('blog:post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


@login_required
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if is_htmx(request):
                return render(request, 'blog/partials/comment_create_response.html', {
                    'comment': comment,
                    'post': post,
                    'comment_form': CommentForm(),
                    'comments_count': post.comments.filter(is_deleted=False).count(),
                })
        elif is_htmx(request):
            response = render(request, 'blog/partials/comment_form.html', {
                'post': post,
                'comment_form': form,
            })
            response['HX-Retarget'] = '#comment-form'
            response['HX-Reswap'] = 'outerHTML'
            return response
    return redirect(post.get_absolute_url())

@login_required
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk, is_deleted=False)

    if comment.author != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        old_body = comment.body
        form = CommentForm(request.POST, instance=comment)

        if form.is_valid():
            comment = form.save(commit=False)
            if comment.body != old_body:
                comment.edited_at = timezone.now()
            comment.save()

            return render(request, 'blog/partials/comment.html', {
                'comment': comment,
            })

    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/partials/comment_edit_form.html', {
        'comment': comment,
        'form': form,
    })

@login_required
def comment_partial(request, pk):
    comment = get_object_or_404(Comment, pk=pk, is_deleted=False)

    return render(request, 'blog/partials/comment.html', {
        'comment': comment,
    })

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs['pk'], is_deleted=False)

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.is_deleted = True
        comment.save(update_fields=['is_deleted', 'updated_at'])
        if is_htmx(request):
            return render(request, 'blog/partials/comment_delete_response.html', {
                'comments_count': comment.post.comments.filter(is_deleted=False).count(),
            })
        return redirect(comment.post.get_absolute_url())


class MyPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/my_posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(
            author=self.request.user,
        ).select_related('category').prefetch_related('tags').order_by('-created_at')


@login_required
@require_POST
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk, status=Post.Status.PUBLISHED)
    is_liked = post.likes.filter(pk=request.user.pk).exists()
    if is_liked:
        post.likes.remove(request.user)
        is_liked = False
    else:
        post.likes.add(request.user)
        is_liked = True

    # We return a small HTML snippet with the updated heart icon and count
    html = render_to_string('blog/partials/like_button.html', {
        'post': post,
        'is_liked': is_liked,
        'likes_count': post.likes.count(),
    }, request=request)
    return HttpResponse(html)
