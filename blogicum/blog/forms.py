from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'category', 'location', 'image')
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M',
                attrs={'type': 'datetime-local'},
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class UserChangeForm(forms.ModelForm):
    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username', 'email')
