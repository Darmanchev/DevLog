from django.contrib import admin

from .models import ImportedArticle, NewsSource


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'country', 'language', 'is_active']
    list_filter = ['source_type', 'country', 'language', 'is_active']
    search_fields = ['name', 'url']


@admin.register(ImportedArticle)
class ImportedArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'status', 'published_at', 'imported_at']
    list_filter = ['status', 'source']
    search_fields = ['title', 'summary', 'url']
    readonly_fields = ['imported_at']
