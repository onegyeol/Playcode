from django.db import models
from album.models import Album

class Playlist(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True)  # Spotify에서 제공하는 고유 ID
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)    # 플레이리스트를 만든 사용자
    track_count = models.IntegerField()
    image_url = models.URLField(null=True, blank=True)  # 플레이리스트 이미지 (없을 수도 있음)

    def __str__(self):
        return self.name

class Track(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="tracks")
    spotify_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    image_url = models.URLField(null=True, blank=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True)