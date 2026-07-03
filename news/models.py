from django.db import models
from django.utils import timezone


class NewsSource(models.Model):
    class SourceType(models.TextChoices):
        RSS = 'rss', 'RSS'
        API = 'api', 'API'

    name = models.CharField(max_length=120)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    url = models.URLField()
    country = models.CharField(max_length=2, default='BG')
    language = models.CharField(max_length=5, default='bg')
    is_active = models.BooleanField(default=True)
    last_imported_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ImportedArticle(models.Model):
    class Status(models.TextChoices):
        IMPORTED = 'imported', 'Imported'
        REVIEWED = 'reviewed', 'Reviewed'
        PUBLISHED = 'published', 'Published'
        IGNORED = 'ignored', 'Ignored'

    source = models.ForeignKey(
        NewsSource,
        on_delete=models.CASCADE,
        related_name='articles',
    )
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    full_text = models.TextField(blank=True)
    source_category = models.CharField(max_length=50, blank=True)
    url = models.URLField(unique=True)
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IMPORTED,
    )

    class Meta:
        ordering = ['-published_at', '-imported_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['source', '-published_at']),
        ]

    def __str__(self):
        return self.title
