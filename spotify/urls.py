from django.urls import path
from .views import spotify_login, spotify_callback, refresh_token, get_user_profile

urlpatterns = [
    path("login/", spotify_login, name="spotify_login"),
    path("callback/", spotify_callback, name="spotify_callback"),
    path("refresh/", refresh_token, name="refresh_token"),
    path("profile/", get_user_profile, name="get_user_profile"),
]
