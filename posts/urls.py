from django.urls import path

from . import views as posts_views

urlpatterns = [
    path("group/<slug:slug>/", posts_views.group_posts, name="group_posts"),
    path("new/", posts_views.new_post, name="new_post"),
    path("follow/", posts_views.follow_index, name="follow_index"),
    path("<str:username>/", posts_views.profile, name="profile"),
    path(
        "<str:username>/<int:post_id>/",
        posts_views.post_view,
        name="post_view",
    ),
    path(
        "<str:username>/<int:post_id>/edit/",
        posts_views.post_edit,
        name="post_edit",
    ),
    path(
        "<username>/<int:post_id>/comment",
        posts_views.add_comment,
        name="add_comment",
    ),
    path(
        "<str:username>/follow/",
        posts_views.profile_follow,
        name="profile_follow",
    ),
    path(
        "<str:username>/unfollow/",
        posts_views.profile_unfollow,
        name="profile_unfollow",
    ),
]
