from django.core.management.base import BaseCommand

from news.models import NewsSource


SOURCES = [
    {
        'name': 'Dir.bg',
        'url': 'https://dir.bg/feeds/rss',
        'language': 'bg',
    },
    {
        'name': 'Vesti.bg',
        'url': 'https://www.vesti.bg/rss',
        'language': 'bg',
    },
    {
        'name': 'Actualno',
        'url': 'https://www.actualno.com/rss',
        'language': 'bg',
    },
    {
        'name': 'Darik News',
        'url': 'https://dariknews.bg/rss.php',
        'language': 'bg',
    },
    {
        'name': 'Nova',
        'url': 'https://nova.bg/rss/latest',
        'language': 'bg',
    },
    {
        'name': 'bTV Novinite',
        'url': 'https://btvnovinite.bg/lbin/v3/rss.php',
        'language': 'bg',
    },
    {
        'name': '24 Chasa',
        'url': 'https://www.24chasa.bg/rss',
        'language': 'bg',
    },
    {
        'name': 'Sega',
        'url': 'https://www.segabg.com/rss',
        'language': 'bg',
    },
]


class Command(BaseCommand):
    help = 'Create default Bulgarian RSS news sources.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for source_data in SOURCES:
            source, created = NewsSource.objects.update_or_create(
                name=source_data['name'],
                defaults={
                    'source_type': NewsSource.SourceType.RSS,
                    'url': source_data['url'],
                    'country': 'BG',
                    'language': source_data['language'],
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {source.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'Updated: {source.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Created: {created_count}, updated: {updated_count}'
            )
        )