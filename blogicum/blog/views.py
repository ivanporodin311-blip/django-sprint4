from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, UserChangeForm
from .models import Category, Comment, Post

User = get_user_model()


def published_posts():
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    )


def index(request):
    template = 'blog/index.html'
    post_list = (
        published_posts()
        .select_related('category', 'location', 'author')
    )
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = (
        published_posts()
        .filter(category=category)
        .select_related('location', 'author')
    )
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        id=id,
    )
    
    is_visible = (
        post.is_published and 
        post.category.is_published and 
        post.pub_date <= timezone.now()
    )
    
    if not is_visible and request.user != post.author:
        raise Http404("Пост не найден")
        
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'blog/create.html'
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def edit_post(request, id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=id)
        return render(request, template, {'form': form, 'post': post})
    form = PostForm(instance=post)
    return render(request, template, {'form': form, 'post': post})


@login_required
def delete_post(request, id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, template, {'form': None, 'post': post})


@login_required
def add_comment(request, id):
    post = get_object_or_404(published_posts(), id=id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', id=id)
    return redirect('blog:post_detail', id=id)


@login_required
def edit_comment(request, id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id, post_id=id)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=id)
    else:
        form = CommentForm(instance=comment)
    return render(
        request,
        template,
        {'form': form, 'post': comment.post, 'comment': comment},
    )


@login_required
def delete_comment(request, id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id, post_id=id)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=id)
    return render(
        request,
        template,
        {'post': comment.post, 'comment': comment},
    )


def profile(request, username):
    template = 'blog/profile.html'
    profile_user = get_object_or_404(User, username=username)
    
    if request.user == profile_user:
        post_list = profile_user.posts.select_related('category', 'location').all()
    else:
        post_list = (
            published_posts()
            .filter(author=profile_user)
            .select_related('category', 'location')
        )
    
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': profile_user,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def edit_profile(request):
    template = 'blog/user.html'
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, template, {'form': form})