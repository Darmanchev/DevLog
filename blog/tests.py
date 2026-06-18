from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()


class PostModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username = 'test',
            password = 'pass12345',
        )

    def test_create_post(self):
        post = Post.objects.create(
            title = 'My first post',
            slug = 'my-first-post',
            author = self.user,
            body = 'text post',
        )
        self.assertEqual(post.title, 'My first post')
        self.assertEqual(Post.objects.count(), 1)

    def test_default_status_is_draft(self):
        post = Post.objects.create(
        title = 'Черновик',
        slug = 'chernovik',
        author = self.user,
        body = '...',
        )
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_str_returns_title(self):
        post = Post.objects.create(
        title = 'Заголовок',
        slug = 'zagolovok',
        author = self.user,
        body = '...',
        )
        self.assertEqual(str(post), 'Заголовок')

    def test_ordering(self):
        post = Post.objects.create(
            title='My first post',
            slug='my-first-post',
            author=self.user,
            body='text post',
        )
        post2 = Post.objects.create(
            title='My second post',
            slug='my-second-post',
            author=self.user,
            body='text post',
        )
        self.assertEqual(Post.objects.first(), post2)
