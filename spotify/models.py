from django.db import models

class SpotifyToken(models.Model):
    user = models.CharField(max_length=100)
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50)

    def __str__(self):
        return f"Token for {self.user}"
