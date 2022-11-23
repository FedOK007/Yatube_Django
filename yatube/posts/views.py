from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .models import Follow, Group, Post
from .forms import CommentForm, PostForm
from .utils import page_obj

User = get_user_model()


def index(request):
    posts_list = (Post.objects
                  .select_related('group', 'author')
                  .all())

    return render(request,
                  'posts/index.html',
                  {'page_obj': page_obj(request,
                                        posts_list,
                                        settings.POSTS_ON_PAGE),
                   })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = (Post.objects
                  .select_related('group', 'author')
                  .filter(group__slug=slug))

    return render(request,
                  'posts/group_list.html',
                  {'group': group,
                   'page_obj': page_obj(request,
                                        posts_list,
                                        settings.POSTS_ON_PAGE),
                   })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = (
        Post.objects
        .select_related('group', 'author')
        .filter(author=author))

    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        following = (
            Follow.objects.filter(user=user, author=author).exists()
        )
    else:
        following = None

    return render(request,
                  'posts/profile.html',
                  {'author': author,
                   'following': following,
                   'page_obj': page_obj(request,
                                        posts_list,
                                        settings.POSTS_ON_PAGE),
                   })


def post_detail(request, post_id):
    posts = (
        Post.objects
        .select_related('group', 'author')
    )
    post = get_object_or_404(posts, id=post_id)
    form = CommentForm(request.POST or None)
    comment_list = post.comments.select_related('author').all()
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
            'form': form,
            'page_obj': page_obj(
                request,
                comment_list,
                settings.POSTS_ON_PAGE
            ),
        })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    posts = (
        Post.objects
        .select_related('group', 'author')
    )
    post = get_object_or_404(posts, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
            'is_edit': True,
            'post_id': post_id,
        })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def follow_index(request):
    user = get_object_or_404(User, id=request.user.id)
    posts = (
        Post.objects
        .select_related('group', 'author')
        .filter(author_id__in=user.follower.values('author'))
    )
    return render(
        request,
        'posts/follow.html',
        {
            'page_obj': page_obj(
                request,
                posts,
                settings.POSTS_ON_PAGE
            ),
        })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        request.user != author
        and not request.user.follower.filter(author=author)
    ):
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    get_object_or_404(request.user.follower.filter(author=author)).delete()
    return redirect('posts:profile', username=username)
