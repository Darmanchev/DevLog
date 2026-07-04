from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import ImportedArticle
from django.db.models import Count
from .services.importer import clean_html_spam


class NewsListView(ListView):
    model = ImportedArticle
    template_name = 'news/news_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        queryset = ImportedArticle.objects.select_related('source').filter(
            status=ImportedArticle.Status.PUBLISHED,
        )

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(source_category=category)

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_category'] = self.request.GET.get('category', '')
        page_params = self.request.GET.copy()
        page_params.pop('page', None)
        pagination_query = page_params.urlencode()
        context['pagination_query'] = f'{pagination_query}&' if pagination_query else ''
        context['categories'] = (
            ImportedArticle.objects.filter(
                status=ImportedArticle.Status.PUBLISHED,
            )
            .exclude(source_category='')
            .values('source_category')
            .annotate(article_count=Count('id'))
            .order_by('source_category')
        )

        return context

class NewsDetailView(DetailView):
    model = ImportedArticle
    template_name = 'news/news_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return ImportedArticle.objects.select_related('source').filter(
            status=ImportedArticle.Status.PUBLISHED,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['article_body_html'] = clean_html_spam(
            self.object.full_text or self.object.summary
        )
        return context
