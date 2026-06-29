from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Comment
from .forms import PostForm, CommentForm


def is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


class PostListView(ListView):
    # Какую выборку данных использовать
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED)
    # Как переменная будет называться в шаблоне (по умолчанию object_list)
    context_object_name = 'posts'
    # Какой шаблон использовать
    template_name = 'blog/post_list.html'

class PostDetailView(DetailView):
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    # Переопределяем выборку, чтобы по прямому URL нельзя было открыть черновик
    def get_queryset(self):
        queryset = Post.objects.select_related('author')
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user)
            )
        return queryset.filter(status=Post.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.filter(is_deleted=False).select_related('author')
        return context



class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

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
            return render(request, 'blog/partials/comment_form.html', {
                'post': post,
                'comment_form': form,
            })
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
