from django.db.models import Case, Count, IntegerField, Q, Value, When

from .models import Post


SORT_NEW = 'new'
SORT_POPULAR = 'popular'
SORT_DISCUSSED = 'discussed'
SORT_RELEVANCE = 'relevance'

SORT_OPTIONS = {
    SORT_NEW: 'Новые',
    SORT_POPULAR: 'Популярные',
    SORT_DISCUSSED: 'Обсуждаемые',
    SORT_RELEVANCE: 'Релевантные',
}


def published_posts_queryset():
    return Post.objects.filter(
        status=Post.Status.PUBLISHED,
    ).select_related(
        'author',
        'category',
    ).prefetch_related('tags').annotate(
        comments_count=Count(
            'comments',
            filter=Q(comments__is_deleted=False),
            distinct=True,
        ),
        likes_count=Count('likes', distinct=True),
    )


def normalize_sort(sort):
    if sort in SORT_OPTIONS:
        return sort
    return SORT_NEW


def search_posts(query='', category_slug='', tag_slug='', sort=SORT_NEW, queryset=None):
    if queryset is None:
        queryset = published_posts_queryset()
    query = query.strip()
    category_slug = category_slug.strip()
    tag_slug = tag_slug.strip()
    sort = normalize_sort(sort)

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(body__icontains=query)
            | Q(author__username__icontains=query)
            | Q(category__name__icontains=query)
            | Q(tags__name__icontains=query)
        )
        queryset = queryset.annotate(
            search_rank=Case(
                When(title__icontains=query, then=Value(4)),
                When(tags__name__icontains=query, then=Value(3)),
                When(category__name__icontains=query, then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)

    queryset = queryset.distinct()

    if sort == SORT_RELEVANCE and query:
        return queryset.order_by('-search_rank', '-created_at')
    if sort == SORT_POPULAR:
        return queryset.order_by('-likes_count', '-created_at')
    if sort == SORT_DISCUSSED:
        return queryset.order_by('-comments_count', '-created_at')
    return queryset.order_by('-created_at')
