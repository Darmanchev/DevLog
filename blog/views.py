from django.views.generic import ListView, DetailView
from .models import Post

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
