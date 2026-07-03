from django.shortcuts import render
from django.views.generic import ListView
from .models import ImportedArticle



class NewsListView(ListView):
    model = ImportedArticle
    template_name = 'news/news_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        return ImportedArticle.objects.select_related('source').filter(
            status=ImportedArticle.Status.PUBLISHED,
        )