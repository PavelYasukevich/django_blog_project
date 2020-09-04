import datetime as dt

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "index.html", {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "group.html",
        {"group": group, "page": page, "paginator": paginator},
    )


@login_required
def new_post(request):
    is_new_post = True
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect("index")
    return render(
        request,
        "posts/new_post.html",
        {"form": form, "is_new_post": is_new_post},
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        try:
            Follow.objects.get(user=request.user, author=author)
            following = True
        except Follow.DoesNotExist:
            pass

    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/profile.html",
        {
            "author": author,
            "page": page,
            "paginator": paginator,
            "following": following,
        },
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        "posts/view_post.html",
        {"author": author, "post": post, "items": comments, "form": form},
    )


@login_required
def post_edit(request, username, post_id):
    is_new_post = False
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id
    )
    author = post.author
    if request.user != author:
        return redirect("post_view", username=author.username, post_id=post.id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if form.is_valid():
        form.save()
        return redirect("post_view", username=author.username, post_id=post.id)
    return render(
        request,
        "posts/new_post.html",
        {
            "form": form,
            "is_new_post": is_new_post,
            "author": author,
            "post": post,
        },
    )


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id
    )
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
        return redirect("post_view", username=author.username, post_id=post.id)
    return render(
        request,
        "posts/view_post.html",
        {"form": form, "author": author, "post": post, "items": comments},
    )


@login_required
def follow_index(request):
    follow_list = [
        follow.author for follow in Follow.objects.filter(user=request.user)
    ]
    post_list = Post.objects.filter(author__in=follow_list)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "posts/follow.html", {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user.username)
    if (
        author != user
        and Follow.objects.filter(author=author, user=user).count() == 0
    ):
        Follow.objects.create(author=author, user=user).save()
    return redirect("profile", username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user.username)
    Follow.objects.get(author=author, user=user).delete()
    return redirect("profile", username=author.username)
