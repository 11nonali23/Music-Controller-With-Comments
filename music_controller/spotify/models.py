from django.db import models

# we need to store this token in a database,
# we can associate the token to the session key of the user
# remember: token are only to room hosts

class SpotifyToken(models.Model):
    # user session key
    user = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    refresh_token = models.CharField(max_length=150)
    access_token = models.CharField(max_length=150)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50)