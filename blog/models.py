from django.db import models
from django.conf import settings
from django.urls import reverse
from slugify import slugify


class UniqueSlugMixin(models.Model):
    # This mixin automatically generates a unique slug based on the slug_source_field.
    slug_source_field = 'name'  # Default source field

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            source_text = getattr(self, self.slug_source_field)
            base = slugify(source_text)
            slug = base
            counter = 2
            ModelClass = self.__class__
            while ModelClass.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile: {self.user}'


class Category(UniqueSlugMixin, models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    slug_source_field = 'name'

    class Meta:
        ordering = ['name']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category_posts', args=[self.slug])


class Tag(UniqueSlugMixin, models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    
    slug_source_field = 'name'

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag_posts', args=[self.slug])


class Post(UniqueSlugMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликован'
        
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    body = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts',
    )
    cover_image = models.ImageField(
        upload_to='post_covers/',
        blank=True,
        null=True,
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='liked_posts',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    slug_source_field = 'title'

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Comment(models.Model):

    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author}: {self.body[:30]}'

    class Meta:
        ordering = ['created_at']
