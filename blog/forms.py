from django import forms
from .models import Post, Comment


MAX_POST_TAGS = 5


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Без категории'
        self.fields['category'].help_text = 'Категория — один главный раздел поста.'
        self.fields['tags'].help_text = f'Выберите до {MAX_POST_TAGS} тегов из готового списка.'

    class Meta:
        model = Post
        fields = ['title', 'body', 'cover_image', 'category', 'tags', 'status']
        widgets = {
            'title': forms.Textarea(attrs={
                'class': 'portal-compose-title-input',
                'placeholder': 'Введите заголовок...',
                'rows': 1,
                'data-autoresize': '',
            }),
            'body': forms.Textarea(attrs={
                'class': 'portal-compose-body-textarea',
                'placeholder': 'Напишите вашу историю...',
                'rows': 16,
                'data-autoresize': '',
            }),
            'cover_image': forms.ClearableFileInput(attrs={
                'class': 'portal-file-input',
            }),
            'category': forms.Select(attrs={
                'class': 'portal-select',
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'portal-check-list',
            }),
            'status': forms.Select(attrs={
                'class': 'portal-select',
            }),
        }

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags and tags.count() > MAX_POST_TAGS:
            raise forms.ValidationError(
                f'Можно выбрать не больше {MAX_POST_TAGS} тегов.'
            )
        return tags


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
