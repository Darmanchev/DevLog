from encodings.punycode import selective_find

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


class AuthTest(TestCase):

    def test_signup_create_user(self):
        response = self.client.post(reverse('blog:signup'), {
            'username': 'test',
            'password1': 'Blog$Secret2026',
            'password2': 'Blog$Secret2026',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='test').exists())

    def test_login(self):
        User.objects.create_user(username='test', password='Blog$Secret2026')
        logged_in = self.client.login(username='test', password='Blog$Secret2026')
        self.assertTrue(logged_in)


class PostSlugTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='tester', password='Blog$Secret2026')

    def test_slug_generation(self):
        post = Post.objects.create(
            title='Мой первый пост',
            author=self.user,
            body='text post',
        )
        self.assertEqual(post.slug, 'moi-pervyi-post')

    def test_slug_collision_gets_suffix(self):
        p1 = Post.objects.create(
            title='Мой первый пост',
            author=self.user,
            body='1',
        )
        p2 = Post.objects.create(
            title='Мой первый пост',
            author=self.user,
            body='2',
        )
        self.assertEqual(p1.slug, 'moi-pervyi-post')
        self.assertEqual(p2.slug, 'moi-pervyi-post-2')

    def test_slug_not_overwritten_on_edit(self):
        post = Post.objects.create(
            title='Мой первый пост',
            author=self.user,
            body='text post',
        )
        original_slug = post.slug
        post.title = 'Новый заголовок'
        post.save()
        self.assertEqual(post.slug, original_slug)

class PostPermissionTest(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='Blog$Secret2026'
        )
        self.other = User.objects.create_user(
            username = 'other',
            password = 'Blog$Secret2026'
        )
        self.post = Post.objects.create(
            title = 'Пост автора',
            author = self.author,
            body = 'текст',
            status = Post.Status.PUBLISHED,
        )

    def test_anonymous_cannot_create(self):
        response = self.client.get(reverse('blog:post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_author_can_edit_own(self):
        self.client.login(
            username='author',
            password='Blog$Secret2026'
        )
        response = self.client.get(reverse('blog:post_edit', args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)

    def test_other_cannot_edit(self):
        self.client.login(username='other', password='Blog$Secret2026')
        response = self.client.get(reverse('blog:post_edit', args=[self.post.slug]))
        self.assertEqual(response.status_code, 403)

    def test_other_cannot_delete(self):
        self.client.login(username='other', password='Blog$Secret2026')
        response = self.client.post(reverse('blog:post_delete', args=[self.post.slug]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())