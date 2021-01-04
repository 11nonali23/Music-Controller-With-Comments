from django.db import models
from api.models import Room

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

# The user vote to skip the current song.
# So we need to clear the votes when the song is skipped.
# Vote need to know the person and the room and the song related to the vote.
class Vote(models.Model):
    # user session key
    user = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    song_id = models.CharField(max_length=50)
    # We can pass a room object to this model to access it information
    # If we only store the code it would have been slower to query room info, cause we need to search the room model
    # cascade = any vote referencing to this room would be deleted if the room is deleted
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

