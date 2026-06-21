from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from .models import Post
from .forms import PostForm


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
        return Post.objects.filter(status=Post.Status.PUBLISHED)


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