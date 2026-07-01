from django.db.models import Count, Q

from .models import Category, Post, Tag


def taxonomy_navigation(request):
    return {
        'nav_categories': Category.objects.annotate(
            posts_count=Count(
                'posts',
                filter=Q(posts__status=Post.Status.PUBLISHED),
                distinct=True,
            ),
        ),
        'nav_tags': Tag.objects.annotate(
            posts_count=Count(
                'posts',
                filter=Q(posts__status=Post.Status.PUBLISHED),
                distinct=True,
            ),
        )[:12],
    }
