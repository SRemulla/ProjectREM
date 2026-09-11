from dotenv import load_dotenv
import os
import base64
from requests import post, get
from urllib.parse import urlencode, quote
import json
from google import genai
import webbrowser
import numpy as np
import scipy as sp
import pandas as pd
import math


load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

def get_token():
    auth_base_url = 'https://accounts.spotify.com/authorize'
    token_url = 'https://accounts.spotify.com/api/token'

    prms = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope':'playlist-read-private playlist-read-collaborative'
    }
    print(redirect_uri)

    auth_url = f'{auth_base_url}?{urlencode(prms,quote_via=quote)}'
    webbrowser.open_new_tab(auth_url)
    auth_code = input('Code: ')
    if 'code=' in auth_code:
        auth_code = auth_code.split('code=')[1].split('&')[0]

    auth_string = client_id + ':' + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.urlsafe_b64encode(auth_bytes),'utf-8')

    headers = {
        'Authorization': 'Basic ' + auth_base64,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri
            }
    access_token_request = post(token_url,data=data,headers=headers)
    json_token_request = json.loads(access_token_request.content)
    token = json_token_request['access_token']
    
    return token

def get_auth_header(token):
    return {'Authorization': 'Bearer ' + token}

def get_playlist_id(playlist_url):
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    return playlist_id

def get_playlist_items(token,playlist_id):
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/items'
    headers = get_auth_header(token)
    limit = 100
    query = f'fields=total,next,items(item(name,album(name)))&limit={limit}'

    query_url = url + '?' + query
    response = get(query_url,headers=headers) # need to add ability to grab next section with offset
    json_result = json.loads(response.content)
    items_dict = json_result['items']
    playlist_len = json_result['total']
    next_query = json_result['next']

    while next_query is not None:
        response_next = get(next_query,headers=headers)
        json_result_next = json.loads(response_next.content)
        items_dict += json_result_next['items']
        next_query = json_result_next['next']

    playlist_items = pd.DataFrame(columns=['album','song'])
    for i,spotify_song_dict in enumerate(items_dict):
        album = spotify_song_dict['item']['album']['name']
        song = spotify_song_dict['item']['name']
        playlist_items.loc[i] = [album,song]

    return playlist_items

if __name__ == "__main__":
    token = get_token()
    # playlist_url = input('Playlist URL: ')
    playlist_url = 'https://open.spotify.com/playlist/6TBCowiTw2LyXm37J24otI?si=ddc0a5a7e99f4696'
    playlist_id = get_playlist_id(playlist_url)
    playlist_items = get_playlist_items(token,playlist_id)

    print(playlist_items)
    print('Length of playlist: ',len(playlist_items))
