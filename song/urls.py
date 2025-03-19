from django.urls import path
from .views import song_detail

urlpatterns = [
    path('<str:song_id>/', song_detail, name='song_detail'),
]
