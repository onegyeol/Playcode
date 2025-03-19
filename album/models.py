from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from song.models import Song

class Album(models.Model):
    spotify_id = models.CharField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    image_url = models.URLField()

    def __str__(self):
        return self.name

class Track(models.Model):
    album = models.ForeignKey(Album, related_name='tracks', on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    duration = models.IntegerField()
    song = models.OneToOneField(Song, on_delete=models.SET_NULL, null=True, blank=True)  # Song과 연결  

    def __str__(self):
        return self.title

class Review(models.Model):
    album = models.ForeignKey('Album', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review on {self.album.name}"