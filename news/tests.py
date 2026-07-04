from datetime import UTC, datetime
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .admin import ImportedArticleAdmin
from .models import ImportedArticle, NewsSource
from .services.importer import clean_html_spam, get_entry_published_at


class ImportBgNewsCommandTest(TestCase):
    def test_success_updates_last_imported_at_and_clears_error(self):
        source = NewsSource.objects.create(
            name='RSS',
            source_type=NewsSource.SourceType.RSS,
            url='https://example.com/feed.xml',
            last_error='old error',
        )

        with patch(
            'news.management.commands.import_bg_news.import_source',
            return_value={'created': 1, 'skipped': 2},
        ):
            call_command('import_bg_news')

        source.refresh_from_db()
        self.assertIsNotNone(source.last_imported_at)
        self.assertEqual(source.last_error, '')


class ImportedArticleAdminTest(TestCase):
    def test_configured_publish_action_exists(self):
        admin = ImportedArticleAdmin(ImportedArticle, AdminSite())

        self.assertIn('publish_articles', admin.actions)
        self.assertTrue(hasattr(admin, 'publish_articles'))


class NewsListViewTest(TestCase):
    def setUp(self):
        self.source = NewsSource.objects.create(
            name='RSS',
            source_type=NewsSource.SourceType.RSS,
            url='https://example.com/feed.xml',
        )

    def test_pagination_preserves_selected_category(self):
        for number in range(13):
            ImportedArticle.objects.create(
                source=self.source,
                title=f'Politics {number}',
                url=f'https://example.com/politics/{number}',
                source_category='Politics',
                status=ImportedArticle.Status.PUBLISHED,
            )

        response = self.client.get(reverse('news:news_list'), {'category': 'Politics'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '?category=Politics&amp;page=2')

    def test_detail_cleans_existing_dir_bg_donation_html(self):
        article = ImportedArticle.objects.create(
            source=self.source,
            title='Article',
            url='https://example.com/article',
            full_text="""
            <p>Реален текст.</p>
            <div><svg><path></path></svg></div>
            <p>
                Днес, повече от всякога, независимата журналистика има нужда от вас.
                В мисията си да предоставяме обективни, достоверни и навременни
                новини разчитаме на вашата подкрепа.
            </p>
            """,
            status=ImportedArticle.Status.PUBLISHED,
        )

        response = self.client.get(reverse('news:news_detail', args=[article.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Реален текст.')
        self.assertNotContains(response, 'независимата журналистика има нужда от вас')
        self.assertNotContains(response, '<svg>')


class RssImporterTest(TestCase):
    def test_clean_html_spam_keeps_actualno_showcase_prompt_on_one_line(self):
        html = """
        <div>
            <p>Реален текст.</p>
            <div id="end-of-main-content">
                <p> Последвайте ни в </p>
                <a href="https://news.google.com/example" rel="nofollow" target="_blank">
                    Google News Showcase
                </a>
                <p>, за да получавате още актуални новини.</p>
            </div>
        </div>
        """

        cleaned_html = clean_html_spam(html)

        self.assertIn(
            '<p>Последвайте ни в <a href="https://news.google.com/example" '
            'rel="nofollow" target="_blank">Google News Showcase</a>, за да получавате '
            'още актуални новини.</p>',
            cleaned_html,
        )
        self.assertNotIn('<p> Последвайте ни в </p>', cleaned_html)
        self.assertNotIn('<p>, за да получавате още актуални новини.</p>', cleaned_html)

    def test_clean_html_spam_removes_dir_bg_donation_block(self):
        html = """
        <div>
            <p>Реален текст на статията.</p>
            <div class="quote-icon"><svg><path></path></svg></div>
            <p>
                Днес, повече от всякога, независимата журналистика има нужда от вас.
                В мисията си да предоставяме обективни, достоверни и навременни
                новини разчитаме на вашата подкрепа.
            </p>
            <div class="quote-icon"><svg><path></path></svg></div>
            <p>Финален абзац.</p>
        </div>
        """

        cleaned_html = clean_html_spam(html)

        self.assertIn('Реален текст на статията.', cleaned_html)
        self.assertIn('Финален абзац.', cleaned_html)
        self.assertNotIn('независимата журналистика има нужда от вас', cleaned_html)
        self.assertNotIn('<svg>', cleaned_html)

    def test_published_at_is_interpreted_as_utc(self):
        entry = {
            'published_parsed': (2026, 7, 4, 12, 30, 0, 5, 185, 0),
        }

        published_at = get_entry_published_at(entry)

        self.assertEqual(published_at, datetime(2026, 7, 4, 12, 30, tzinfo=UTC))
