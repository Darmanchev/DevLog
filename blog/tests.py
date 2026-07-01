from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .forms import PostForm
from .models import Category, Comment, Post, Tag, UserProfile
from .templatetags.blog_extras import markdown_format, markdown_plain_text, read_time

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

    def test_list_can_filter_by_category(self):
        django = Category.objects.create(name='Django')
        python = Category.objects.create(name='Python')
        self.published.category = django
        self.published.save(update_fields=['category'])
        Post.objects.create(
            title='Python пост',
            slug='python-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
            category=python,
        )

        response = self.client.get(reverse('blog:post_list'), {'category': django.slug})

        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'Python пост')

    def test_category_page_uses_pretty_url(self):
        django = Category.objects.create(name='Django')
        python = Category.objects.create(name='Python')
        self.published.category = django
        self.published.save(update_fields=['category'])
        Post.objects.create(
            title='Python пост',
            slug='python-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
            category=python,
        )

        response = self.client.get(reverse('blog:category_posts', args=[django.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'Python пост')

    def test_list_can_filter_by_tag(self):
        htmx = Tag.objects.create(name='HTMX')
        ui = Tag.objects.create(name='UI')
        self.published.tags.add(htmx)
        other = Post.objects.create(
            title='UI пост',
            slug='ui-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        other.tags.add(ui)

        response = self.client.get(reverse('blog:post_list'), {'tag': htmx.slug})

        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'UI пост')

    def test_tag_page_uses_pretty_url(self):
        htmx = Tag.objects.create(name='HTMX')
        ui = Tag.objects.create(name='UI')
        self.published.tags.add(htmx)
        other = Post.objects.create(
            title='UI пост',
            slug='ui-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        other.tags.add(ui)

        response = self.client.get(reverse('blog:tag_posts', args=[htmx.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'UI пост')

    def test_create_post_saves_category_and_tags(self):
        category = Category.objects.create(name='Django')
        tag = Tag.objects.create(name='Forms')
        self.client.login(username='tester', password='pass12345')

        response = self.client.post(reverse('blog:post_create'), {
            'title': 'Пост с метками',
            'body': 'текст',
            'category': category.pk,
            'tags': [tag.pk],
            'status': Post.Status.PUBLISHED,
        })

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(title='Пост с метками')
        self.assertEqual(post.category, category)
        self.assertIn(tag, post.tags.all())

    def test_create_form_defaults_to_published_status(self):
        self.client.login(username='tester', password='pass12345')

        response = self.client.get(reverse('blog:post_create'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].initial['status'],
            Post.Status.PUBLISHED,
        )

    def test_post_form_rejects_more_than_five_tags(self):
        tags = [
            Tag.objects.create(name=f'Tag {number}')
            for number in range(6)
        ]

        form = PostForm(data={
            'title': 'Пост с лишними тегами',
            'body': 'текст',
            'tags': [tag.pk for tag in tags],
            'status': Post.Status.PUBLISHED,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('tags', form.errors)

    def test_post_form_includes_cover_image(self):
        form = PostForm()

        self.assertIn('cover_image', form.fields)

    def test_detail_shows_related_posts_by_category_or_tag(self):
        category = Category.objects.create(name='Django')
        tag = Tag.objects.create(name='Forms')
        self.published.category = category
        self.published.save(update_fields=['category'])
        self.published.tags.add(tag)
        by_category = Post.objects.create(
            title='Похожий по категории',
            slug='related-category',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
            category=category,
        )
        by_tag = Post.objects.create(
            title='Похожий по тегу',
            slug='related-tag',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        by_tag.tags.add(tag)
        Post.objects.create(
            title='Не похожий',
            slug='not-related',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )

        response = self.client.get(self.published.get_absolute_url())

        related_posts = list(response.context['related_posts'])
        self.assertIn(by_category, related_posts)
        self.assertIn(by_tag, related_posts)
        self.assertNotContains(response, 'Не похожий')

    def test_list_is_paginated(self):
        for number in range(7):
            Post.objects.create(
                title=f'Пост {number}',
                slug=f'post-{number}',
                author=self.user,
                body='текст',
                status=Post.Status.PUBLISHED,
            )

        response = self.client.get(reverse('blog:post_list'))

        self.assertTrue(response.context['is_paginated'])
        self.assertContains(response, 'page=2')

    def test_list_can_sort_by_discussed(self):
        quiet = Post.objects.create(
            title='Тихий пост',
            slug='quiet-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        discussed = Post.objects.create(
            title='Обсуждаемый пост',
            slug='discussed-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        Comment.objects.create(post=discussed, author=self.user, body='Комментарий')

        response = self.client.get(reverse('blog:post_list'), {'sort': 'discussed'})

        posts = list(response.context['posts'])
        self.assertEqual(posts[0], discussed)
        self.assertIn(quiet, posts)

    def test_list_can_sort_by_popular_likes(self):
        quiet = Post.objects.create(
            title='Тихий пост',
            slug='quiet-liked-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        popular = Post.objects.create(
            title='Популярный пост',
            slug='popular-liked-post',
            author=self.user,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        popular.likes.add(self.user)

        response = self.client.get(reverse('blog:post_list'), {'sort': 'popular'})

        posts = list(response.context['posts'])
        self.assertEqual(posts[0], popular)
        self.assertIn(quiet, posts)

    def test_list_shows_active_search_filter(self):
        response = self.client.get(reverse('blog:post_list'), {'q': 'Опубликованный'})

        self.assertContains(response, 'Поиск: Опубликованный')
        self.assertContains(response, '1 публикаций')

    def test_author_page_shows_profile_and_posts(self):
        UserProfile.objects.create(user=self.user, bio='Пишу про Django.')

        response = self.client.get(reverse('blog:author_posts', args=[self.user.username]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пишу про Django.')
        self.assertContains(response, 'Опубликованный')
        self.assertNotContains(response, 'Черновик')

    def test_detail_has_open_graph_meta(self):
        response = self.client.get(self.published.get_absolute_url())

        self.assertContains(response, 'property="og:type" content="article"')


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


class TemplateFilterTest(TestCase):

    def test_read_time_rounds_up(self):
        text = ' '.join(['word'] * 201)

        self.assertEqual(read_time(text), 2)

    def test_markdown_escapes_raw_html(self):
        html = markdown_format('<script>alert("x")</script> **жирный**')

        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('<strong>жирный</strong>', html)

    def test_markdown_renders_tables(self):
        html = markdown_format(
            '| Название | Статус |\n'
            '| --- | --- |\n'
            '| Django формы | Опубликован |'
        )

        self.assertIn('<table>', html)
        self.assertIn('<th>Название</th>', html)
        self.assertIn('<td>Опубликован</td>', html)

    def test_markdown_renders_fenced_code_without_html_entities(self):
        html = markdown_format('```python\nprint("hello")\n```')

        self.assertIn('<pre><code class="language-python">', html)
        self.assertIn('print(&quot;hello&quot;)', html)
        self.assertNotIn('&amp;quot;', html)

    def test_markdown_plain_text_unescapes_entities(self):
        text = markdown_plain_text('```python\nprint("hello")\n```')

        self.assertIn('print("hello")', text)
        self.assertNotIn('&quot;', text)


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


class LikeViewTest(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            password='Blog$Secret2026'
        )
        self.reader = User.objects.create_user(
            username='reader',
            password='Blog$Secret2026'
        )
        self.post = Post.objects.create(
            title='Публичный пост',
            author=self.author,
            body='текст',
            status=Post.Status.PUBLISHED,
        )
        self.draft = Post.objects.create(
            title='Черновик',
            author=self.author,
            body='секрет',
            status=Post.Status.DRAFT,
        )

    def test_toggle_like_requires_post(self):
        self.client.login(username='reader', password='Blog$Secret2026')

        response = self.client.get(reverse('blog:toggle_like', args=[self.post.pk]))

        self.assertEqual(response.status_code, 405)

    def test_toggle_like_adds_and_removes_like(self):
        self.client.login(username='reader', password='Blog$Secret2026')

        response = self.client.post(reverse('blog:toggle_like', args=[self.post.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.post.likes.filter(pk=self.reader.pk).exists())
        self.assertContains(response, 'aria-pressed="true"')

        response = self.client.post(reverse('blog:toggle_like', args=[self.post.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.post.likes.filter(pk=self.reader.pk).exists())
        self.assertContains(response, 'aria-pressed="false"')

    def test_toggle_like_rejects_drafts(self):
        self.client.login(username='reader', password='Blog$Secret2026')

        response = self.client.post(reverse('blog:toggle_like', args=[self.draft.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.draft.likes.filter(pk=self.reader.pk).exists())

    def test_like_htmx_post_accepts_csrf_header(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST='localhost')
        client.login(username='reader', password='Blog$Secret2026')
        client.get(self.post.get_absolute_url())
        csrf_token = client.cookies['csrftoken'].value

        response = client.post(
            reverse('blog:toggle_like', args=[self.post.pk]),
            HTTP_HX_REQUEST='true',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.post.likes.filter(pk=self.reader.pk).exists())


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
