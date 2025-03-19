from django.db import models

class Song(models.Model):
    """
    Spotify에서 가져온 곡 정보를 저장하는 모델
    """
    track_id = models.CharField(max_length=100, unique=True)  # Spotify 트랙 ID
    title = models.CharField(max_length=255)  # 노래 제목
    artist = models.CharField(max_length=255)  # 가수
    album = models.ForeignKey('album.Album', related_name='songs', on_delete=models.SET_NULL, null=True, blank=True)  # 앨범과의 연결
    cover_url = models.URLField(blank=True, null=True)  # 앨범 이미지 URL
    lyrics = models.TextField(blank=True, null=True)  # 가사 (Musixmatch API 활용)
    preview_url = models.URLField(blank=True, null=True)  # 미리 듣기 URL (Spotify 제공)
    created_at = models.DateTimeField(auto_now_add=True)  # 데이터 저장 시간

    def __str__(self):
        return f"{self.title} - {self.artist}"
    
    
