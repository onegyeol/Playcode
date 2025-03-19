from django.urls import path
from .views import album_detail

urlpatterns = [
    path('<str:album_id>/', album_detail, name='album_detail'),
]
