from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
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

class PostViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester',
                                             password='pass12345')
        self.published = Post.objects.create(
            title='Опубликованный', slug='published',
            author=self.user, body='текст',
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            title='Черновик', slug='draft',
            author=self.user, body='текст',
            status=Post.Status.DRAFT,
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_only_published(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'Черновик')

    def test_detail_returns_200(self):
        response = self.client.get(self.published.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_detail_draft_returns_404(self):
        response = self.client.get(reverse('blog:post_detail', args=['draft']))
        self.assertEqual(response.status_code, 404)