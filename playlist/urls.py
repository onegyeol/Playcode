from django.urls import path
from .views import display_playlists, get_playlist_tracks

urlpatterns = [
    path("", display_playlists, name="playlist-home"),  # 플레이리스트 홈 (/playlist/)
   path("<str:playlist_id>/", get_playlist_tracks, name="playlist-tracks"),  # 곡 목록
]
