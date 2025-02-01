from flask import Flask, request, redirect, session, url_for, jsonify
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
    return redirect(url_for('select_playlists')) 


@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('select_playlists'))  


@app.route('/select_playlists')
def select_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp.current_user_playlists()
    
    playlist_options = ""
    for playlist in playlists['items']:
        playlist_options += f'<input type="checkbox" name="playlists" value="{playlist["id"]}"> {playlist["name"]}<br>'

    return f"""
        <form method="post" action="/get_selected_playlists">
            <h3>Select Playlists to Analyze</h3>
            {playlist_options}
            <button type="submit">Submit</button>
        </form>
    """

@app.route('/get_selected_playlists', methods=['POST'])
def get_selected_playlists(): 
    selected_playlist_ids = request.form.getlist('playlists')

    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    artist_counter = Counter()
    genre_counter = Counter()
    tracks_info = []

    for playlist_id in selected_playlist_ids: 
        playlist_items = sp.playlist_items(playlist_id)

        for item in playlist_items['items']:
            track = item.get('track')
            if track:
                track_name = track.get('name', 'Unknown Track Name')
                artist_names = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track.get('external_urls', {}).get('spotify', '#')

                tracks_info.append(f"{track_name} by {artist_names}: {track_url}")

                for artist in track['artists']:
                    artist_name = artist['name']
                    artist_counter[artist_name] += 1

                    artist_data = sp.artist(artist['id'])
                    artist_genres = artist_data.get('genres', [])
                    
                    if artist_genres:
                        for genre in artist_genres:
                            genre_counter[genre] += 1

    data = {
        "artists": dict(artist_counter),
        "genres": dict(genre_counter)
    }

    return jsonify(data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=3000)