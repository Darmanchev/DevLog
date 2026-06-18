from django.shortcuts import render, get_object_or_404
from .models import Post

def post_list(request):
    posts = Post.objects.filter(status=Post.Status.PUBLISHED)
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    return render(request, 'blog/post_detail.html', {'post': post})