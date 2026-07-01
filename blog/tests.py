from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Comment, Post

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

    def test_author_can_view_own_draft(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.get(reverse('blog:post_detail', args=['draft']))
        self.assertEqual(response.status_code, 200)


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


class CommentPermissionTest(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='Blog$Secret2026'
        )
        self.other = User.objects.create_user(
            username='other',
            password='Blog$Secret2026'
        )
        self.post = Post.objects.create(
            title='Пост',
            author=self.author,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body='Первый комментарий',
        )

    def test_author_can_edit_own_comment(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_edit', args=[self.comment.pk]),
            {'body': 'Обновленный комментарий'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Обновленный комментарий')

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, 'Обновленный комментарий')
        self.assertIsNotNone(self.comment.edited_at)

    def test_edit_without_text_change_does_not_mark_as_edited(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_edit', args=[self.comment.pk]),
            {'body': 'Первый комментарий'},
        )
        self.assertEqual(response.status_code, 200)

        self.comment.refresh_from_db()
        self.assertIsNone(self.comment.edited_at)

    def test_author_gets_inline_edit_form(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.get(reverse('blog:comment_edit', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<textarea')
        self.assertContains(response, 'hx-post=')
        self.assertContains(response, 'data-autoresize')

    def test_htmx_comment_create_returns_comment_partial(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_create', args=[self.post.slug]),
            {'body': 'Новый комментарий'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новый комментарий')
        self.assertContains(response, 'hx-get=')
        self.assertContains(response, 'hx-swap-oob="true"')
        self.assertContains(response, 'id="comments-count"')
        self.assertTrue(Comment.objects.filter(body='Новый комментарий').exists())

    def test_regular_comment_create_still_redirects(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_create', args=[self.post.slug]),
            {'body': 'Обычный комментарий'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(body='Обычный комментарий').exists())

    def test_other_cannot_edit_comment(self):
        self.client.login(username='other', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_edit', args=[self.comment.pk]),
            {'body': 'Чужая правка'},
        )
        self.assertEqual(response.status_code, 403)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, 'Первый комментарий')

    def test_author_can_soft_delete_own_comment(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(reverse('blog:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 302)

        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_htmx_delete_returns_empty_response(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.post(
            reverse('blog:comment_delete', args=[self.comment.pk]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="comments-count"')

        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_deleted_comment_is_hidden_on_post_detail(self):
        self.comment.is_deleted = True
        self.comment.save(update_fields=['is_deleted'])

        response = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(response, 'Первый комментарий')

    def test_other_cannot_delete_comment(self):
        self.client.login(username='other', password='Blog$Secret2026')
        response = self.client.post(reverse('blog:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)

        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_deleted)

class MyPostListViewTest(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='Blog$Secret2026'
        )
        self.other = User.objects.create_user(
            username='other',
            password='Blog$Secret2026'
        )
        self.author_post = Post.objects.create(
            title='Пост автора',
            author=self.author,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        self.other_post = Post.objects.create(
            title='Чужой пост',
            author=self.other,
            body='текст',
            status=Post.Status.PUBLISHED,
        )

    def test_anonymous_cannot_view_my_posts(self):
        response = self.client.get(reverse('blog:my_posts'))
        self.assertEqual(response.status_code, 302)

    def test_user_sees_only_own_posts(self):
        self.client.login(username='author', password='Blog$Secret2026')
        response = self.client.get(reverse('blog:my_posts'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пост автора')
        self.assertNotContains(response, 'Чужой пост')