from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import ImportedArticle
from django.db.models import Count


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