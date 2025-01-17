from flask import Flask, request, redirect, session, url_for
import os 
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from collections import Counter

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = 'http://localhost:3000/callback'
scope = 'playlist-read-private'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)
sp = Spotify(auth_manager=sp_oauth)

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))


@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))


@app.route('/get_playlists')
def get_playlists(): 
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp.current_user_playlists()
    playlists_html = '<br>'.join([f'<a href="/get_playlist_tracks/{pl["id"]}">{pl["name"]}</a>' for pl in playlists['items']])

    return f"<h1>Playlists</h1>{playlists_html}"

@app.route('/get_playlist_tracks/<playlist_id>')
def get_playlist_tracks(playlist_id):
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlist_items = sp.playlist_items(playlist_id)
    artist_counter = Counter()

    tracks_info = []

    for item in playlist_items['items']:
        track = item['track']
        track_name = track['name']
        artist_names = ', '.join([artist['name'] for artist in track['artists']])
        track_url = track['external_urls']['spotify']
        tracks_info.append(f"{track_name} by {artist_names}: {track_url}")

        for artist in track['artists']:
            artist_name = artist['name']
            artist_counter[artist_name] += 1

    artist_stats = "<br>".join([f"{artist}: {count} times" for artist, count in artist_counter.items()])
    tracks_html = "<br>".join(tracks_info)

    return f"""
        <h1>Tracks in Playlist</h1>
        <div>{tracks_html}</div>
        <h2>Artist Statistics</h2>
        <div>{artist_stats}</div>
    """


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=3000)