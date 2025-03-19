# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # 로그인 URL 연결
    path('', include('main.urls')),  # 홈 페이지 URL 연결
    path("playlist/", include("playlist.urls")),  # 플레이리스트 앱 URL 포함
    path("spotify/", include("spotify.urls")),  # Spotify 앱 URL 포함
    path('song/', include('song.urls')),          # 노래 정보 관련 로직
    path('album/', include('album.urls')),        # 앨범 정보 관련 로직
]
