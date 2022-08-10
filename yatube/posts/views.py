from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .settings import POST_NUM_ON_PAGE


def paginate_posts(request, posts):
    """Вспомогательная функция для создания объекта Paginator"""
    return Paginator(posts, POST_NUM_ON_PAGE).get_page(request.GET.get('page'))


def index(request):
    """Отображение всех постов по POST_NUM_ON_PAGE постов на странице"""
    return render(request, 'posts/index.html', {
        'page_obj': paginate_posts(request, Post.objects.all())
    })


def group_posts(request, slug):
    """Отображение постов конкретной группы"""
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginate_posts(request, group.posts.all()),
    })


def profile(request, username):
    """Отображение профиля конкретного пользователя"""
    following = False
    author = get_object_or_404(User, username=username)
    if request.user or request.user != author:
        following = Follow.objects.filter(author=author)
    return render(request, 'posts/profile.html', {
        'page_obj': paginate_posts(request, author.posts.all()),
        'author': author,
        'following': following
    })


def post_detail(request, post_id):
    """Отображение информации конкретного поста"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание нового поста"""
    form = PostForm(request.POST or None, request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    """Изменение поста"""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if not form.is_valid():
        context = {
            'post': post,
            'form': form,
        }
        return render(request, 'posts/create_post.html', context)
    post = form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Вывод всех постов автора на которого подписан пользователь"""
    context = {
        'page_obj': paginate_posts(
            request,
            Post.objects.filter(
                author__following__user=request.user
            )
        ),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Возможность подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Возможность отписаться от автора."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        get_object_or_404(
            Follow, user=request.user, author__username=username).delete()
    return redirect('posts:profile', username)
