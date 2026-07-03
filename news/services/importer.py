from datetime import datetime
from time import mktime

import feedparser
from django.db import transaction
from django.utils import timezone

from news.models import ImportedArticle, NewsSource


def import_source(source):
    if source.source_type != NewsSource.SourceType.RSS:
        raise ValueError('Only RSS sources are supported for now.')

    feed = feedparser.parse(source.url)

    created_count = 0
    skipped_count = 0

    for entry in feed.entries:
        article_url = entry.get('link')

        if not article_url:
            skipped_count += 1
            continue

        article, created = ImportedArticle.objects.get_or_create(
            url=article_url,
            defaults={
                'source': source,
                'title': entry.get('title', '')[:255],
                'summary': entry.get('summary', ''),
                'image_url': get_entry_image_url(entry),
                'published_at': get_entry_published_at(entry),
            },
        )

        if created:
            created_count += 1
        else:
            skipped_count += 1


    return {
        'created': created_count,
        'skipped': skipped_count,
    }

def get_entry_published_at(entry):
    published = entry.get('published_parsed') or entry.get('updated_parsed')

    if not published:
        return None

    naive_datetime = datetime.fromtimestamp(mktime(published))
    return timezone.make_aware(naive_datetime)

def get_entry_image_url(entry):
    media_content = entry.get('media_content')

    if media_content:
        return media_content[0].get('url', '')

    media_thumbnail = entry.get('media_thumbnail')

    if media_thumbnail:
        return media_thumbnail[0].get('url', '')

    return ''
