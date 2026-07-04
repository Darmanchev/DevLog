from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import NewsSource
from news.services.importer import import_source


class Command(BaseCommand):
    help = 'Import articles from active Bulgarian Rss news sources.'

    def handle(self, *args, **options):
        sources = NewsSource.objects.filter(
            is_active=True,
            source_type=NewsSource.SourceType.RSS,
        )

        total_created = 0
        total_skipped = 0

        for source in sources:
            self.stdout.write(f'Importing from {source.name}...')

            try:
                result = import_source(source)
            except Exception as error:
                source.last_error = str(error)
                source.save(update_fields=['last_error'])

                self.stderr.write(
                    self.style.ERROR(f'{source.name}: failed {error}')
                )
                continue

            source.last_imported_at = timezone.now()
            source.last_error = ''
            source.save(update_fields=['last_imported_at', 'last_error'])

            total_created += result['created']
            total_skipped += result['skipped']

            self.stdout.write(
                self.style.SUCCESS(
                    f'{source.name}: created {result["created"]}, skipped {result["skipped"]}'
                )
            )


        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Created: {total_created}, skipped: {total_skipped}'
            )
        )


