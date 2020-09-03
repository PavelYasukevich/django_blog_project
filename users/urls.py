from django.urls import path

from . import views as users_views

urlpatterns = [
    path("signup/", users_views.SignUp.as_view(), name="signup"),
]
