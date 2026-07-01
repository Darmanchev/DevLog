from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('new/', views.PostCreateView.as_view(), name='post_create'),
    path('my-posts/', views.MyPostListView.as_view(), name='my_posts'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('<slug:slug>/comment/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    path('comments/<int:pk>/partial/', views.comment_partial, name='comment_partial'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
]
