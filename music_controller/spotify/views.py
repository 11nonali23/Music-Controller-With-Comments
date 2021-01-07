from django.shortcuts import render, redirect
from .credentials import    REDIRECT_URI, CLIENT_SECRET, CLIENT_ID
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from requests import Request, post
from .util import *
from api.models import Room
from .models import Vote

# this views classes will contain the logic to authenticate to spotify

# for the comments refer Tim's diagram

# (1) request authorization to access data 
class AuthURL(APIView):
    def get(self, request, fornat=None):
        scopes = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'

        url = Request('GET', 'https://accounts.spotify.com/authorize', params={
            'scope': scopes,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID
        }).prepare().url

        return Response({'url': url}, status=status.HTTP_200_OK)

# (1/2) after user logs in, we get the code to request the token and redirect the user to frontend
def spotify_callback(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')

    #request information from spotify
    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')

    if not request.session.exists(request.session.session_key):
        request.session.create()

    update_or_create_user_tokens(request.session.session_key, access_token, token_type, expires_in, refresh_token)

    # If I want to redirect the user to a different app name_app:url
    # blank column because the index has a blank name
    return redirect('frontend:')

# view to check if the user is auth to spotify and call utils to refresh the token
class IsAuthenticated(APIView):
    def get(self, request, format=None):
        is_authenticated = is_spotify_authenticated(
            self.request.session.session_key)
        return Response({'status': is_authenticated}, status=status.HTTP_200_OK)
    

# view to return information about the current song
# since this endpoint is called every second the music player would be updated every time
class CurrentSong(APIView):
    def get(self, request, format=None):
        room_code = self.request.session.get('room_code')
        room = Room.objects.filter(code=room_code)
        if room.exists():
            room = room[0]
        else:
            return Response({'Error': "unexisting room"}, status=status.HTTP_404_NOT_FOUND)
        host = room.host
        endpoint = "player/currently-playing"
        response = execute_spotify_api_request(host, endpoint)

        if 'Error' in response or 'item' not in response:
            return Response({'Error': "unexisting content"}, status=status.HTTP_204_NO_CONTENT)

        item = response.get('item')
        duration = item.get('duration_ms')
        progress = response.get('progress_ms')
        album_cover = item.get('album').get('images')[0].get('url')
        is_playing = response.get('is_playing')
        song_id = item.get('id')

        artist_string = ""

        for i, artist in enumerate(item.get('artists')):
            if i > 0:
                artist_string += ", "
            name = artist.get('name')
            artist_string += name

        # we say to the frontend how much votes the current song has
        num_votes = len(Vote.objects.filter(room=room, song_id=song_id))


        song = {
            'title': item.get('name'),
            'artist': artist_string,
            'duration': duration,
            'time': progress,
            'image_url': album_cover,
            'is_playing': is_playing,
            'votes': num_votes,
            'votes_required': room.votes_to_skip,
            'id': song_id
        }

        #print("song",song)

        self.update_room_song(room, song_id)

        return Response(song, status=status.HTTP_200_OK)

    def update_room_song(self, room, song_id):
        current_song = room.current_song
        # check if we're not updating the same song
        if current_song != song_id:
            room.current_song = song_id
            room.save(update_fields=['current_song'])
            # a new song need to refresh the votes, we have the room as foreign key :)
            votes = Vote.objects.filter(room=room).delete()
        

# Can we request the play and pause from the frontend ?
# Maybe we can, but it's unsecure. It's better to call from the backend beacuse we have the access token in it
class PauseSong(APIView):
    def put(self, response, format=None):
        # getting the corresponding room
        room_code = self.request.session.get('room_code')
        room = Room.objects.filter(code=room_code)
        if room.exists():
            room = room[0]
        else:
            return Response({'Error': "unexisting room"}, status=status.HTTP_404_NOT_FOUND)
        
        # checking if the user has the permission to pause the song
        if self.request.session.session_key == room.host or room.guest_can_pause:
            pause_song(room.host)
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class PlaySong(APIView):
    def put(self, response, format=None):
        # getting the corresponding room
        room_code = self.request.session.get('room_code')
        room = Room.objects.filter(code=room_code)
        # chhecking if the room exist is a good practice, not doing it won't break the application
        if room.exists():
            room = room[0]
        else:
            return Response({'Error': "unexisting room"}, status=status.HTTP_404_NOT_FOUND)
        
        # checking if the user has the permission to pause the song
        if self.request.session.session_key == room.host or room.guest_can_pause:
            play_song(room.host)
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class SkipSong(APIView):
    def post(self, request, format=None):
        room_code = self.request.session.get('room_code')
        room = Room.objects.filter(code=room_code)
        # chhecking if the room exist is a good practice, not doing it won't break the application
        if room.exists():
            room = room[0]
        else:
            return Response({'Error': "unexisting room"}, status=status.HTTP_404_NOT_FOUND)
        # get votes for the current song in the room
        # we want to make sure that we select older votes, so we need also the current song
        # edge case: if the song is played twice it will be skipped,
        # but if you skipped once maybe you would skip it twice
        votes = Vote.objects.filter(room=room, song_id=room.current_song)
        votes_needed = room.votes_to_skip

        # we also check the amount of votes and skip the song if the votes are greater than needed
        if self.request.session.session_key == room.host or len(votes) + 1 >= votes_needed:
            # clear the votes if the song is skipped
            votes.delete()
            skip_song(room.host)
        # create the vote if the user has pressed skip song
        else:
            vote = Vote(user=self.request.session.session_key,
                        room=room, song_id=room.current_song)
            vote.save()

        return Response({}, status.HTTP_204_NO_CONTENT)