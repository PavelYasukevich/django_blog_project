from django.conf import settings
from django.conf.urls import handler404, handler500
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views as flatpages_views
from django.urls import include, path

from posts import views as posts_views

urlpatterns = [
    path("404", posts_views.page_not_found),
    path("500", posts_views.server_error),
    path("admin/", admin.site.urls),
    path("", posts_views.index, name="index"),
    path("", include("posts.urls")),
    path("about/", include("django.contrib.flatpages.urls")),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
]

urlpatterns += [
    path(
        "about-author/",
        flatpages_views.flatpage,
        {"url": "/about-author/"},
        name="about_author",
    ),
    path(
        "about-spec/",
        flatpages_views.flatpage,
        {"url": "/about-spec/"},
        name="about_spec",
    ),
    # path('terms/', flatpages_views.flatpage, {'url': '/terms/'}, name='terms'),
]

handler404 = "posts.views.page_not_found" # noqa
handler500 = "posts.views.server_error" # noqa

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
