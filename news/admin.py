from django.contrib import admin

from .models import ImportedArticle, NewsSource


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'country', 'language', 'is_active', 'last_imported_at', 'has_error']
    list_filter = ['source_type', 'country', 'language', 'is_active']
    search_fields = ['name', 'url']
    readonly_fields = ['last_imported_at', 'last_error']

    @admin.display(boolean=True, description='Error')
    def has_error(self, obj):
        return bool(obj.last_error)


@admin.register(ImportedArticle)
class ImportedArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'source_category', 'status', 'published_at', 'imported_at']
    list_filter = ['status', 'source', 'source_category']
    search_fields = ['title', 'summary', 'url']
    readonly_fields = ['imported_at']
    actions = ['publish_article', 'ignore_articles']

    @admin.action(description='Publish selected articles')
    def publish_articles(self, request, queryset):
        updated_count = queryset.update(
            status=ImportedArticle.Status.PUBLISHED,
        )

        self.message_user(
            request,
            f'Published {updated_count} articles.',
        )

    @admin.action(description='Ignore selected articles')
    def ignore_articles(self, request, queryset):
        updated_count = queryset.update(
            status=ImportedArticle.Status.IGNORED,
        )

        self.message_user(
            request,
            f'Ignored {updated_count} articles.',
        )