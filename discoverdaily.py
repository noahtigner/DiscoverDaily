import os
import sys
import argparse
from datetime import datetime
import random
from functools import wraps

from utils.utilities import my_print as print
from utils.utilities import my_input as input
from utils.utilities import ProgressBar, CountDown, print_json

import spotipy
import spotipy.util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.client import SpotifyException
import spotipy.oauth2 as oauth2

import pandas as pd
import sqlite3
from sqlite3 import Error

from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ----------------------------------------------------------------

def db_connection(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        db = db_create_connection('records.db')
        return f(*args, **kwargs, db=db)

    return wrapper

def db_create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print('Error: ' + str(e), color='red')
        return None

@db_connection
def db_create_table(db=None, table_name='tracks'):
    try:
        statement = f""" CREATE TABLE IF NOT EXISTS {table_name} (
                            id TEXT UNIQUE PRIMARY KEY,

                            name TEXT NOT NULL,
                            artist1 TEXT NOT NULL,
                            artist1ID TEXT NOT NULL,
                            artist2 TEXT,
                            artist2ID TEXT,
                            popularity INTEGER NOT NULL,
                            liked BOOLEAN NOT NULL,

                            acousticness DECIMAL(1, 5) NOT NULL,
                            danceability DECIMAL(1, 5) NOT NULL,
                            duration_ms  INTEGER NOT NULL,
                            energy DECIMAL(1, 5) NOT NULL,
                            instrumentalness DECIMAL(1, 5) NOT NULL,
                            key INTEGER NOT NULL,
                            liveness DECIMAL(1, 5) NOT NULL,
                            loudness INTEGER NOT NULL,
                            mode INTEGER NOT NULL,
                            speechiness DECIMAL(1, 5) NOT NULL,
                            valence DECIMAL(1, 5) NOT NULL,
                            tempo INTEGER NOT NULL,
                            time_signature INTEGER NOT NULL
                        );
                    """
        cursor = db.cursor()
        cursor.execute(statement)
        db.commit()
    except Error as e:
        print('Error: ' + str(e), color='red')

@db_connection
def db_has_track(db=None, track_id=None):
    cursor = db.cursor()
    cursor.execute('SELECT count(*) FROM tracks WHERE id = ?', (track_id,))
    data = cursor.fetchone()[0]

    if data == 0:
        return False
    return True

@db_connection
def db_insert_track(db=None, track=None):
    try:
        statement = """ INSERT INTO tracks (id, name, artist1, artist1ID, artist2, artist2ID, 
                                            popularity, liked, 
                                            acousticness, danceability, duration_ms, energy, instrumentalness, 
                                            key, liveness, loudness, mode, speechiness, valence, tempo, time_signature)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """
        cursor = db.cursor()
        cursor.execute(statement, track)
        db.commit()
        return cursor.lastrowid
    except Error as e:
        print('Error: ' + str(e), color='red')

@db_connection
def db_select_track(db=None, liked=None):
    try:
        statement = """ SELECT *
                        FROM tracks
                        WHERE liked = ?
                    """
        cursor = db.cursor()
        cursor.execute(statement, (liked,))
        rows = cursor.fetchall()

        return rows

    except Error as e:
        print('Error: ' + str(e), color='red')

@db_connection
def db_get_all(db=None):
    try:
        statement = """ SELECT *
                        FROM tracks
                    """

        cursor = db.cursor()
        cursor.execute(statement)
        rows = cursor.fetchall()

        return rows

    except Error as e:
        print('Error: ' + str(e), color='red')

# ----------------------------------------------------------------

class SPConnection:
    username = ''
    scope = 'user-library-read user-library-modify playlist-modify-public playlist-modify-private user-read-private user-read-playback-state user-modify-playback-state'
    client_id = ''
    client_secret = ''
    redirect_uri = 'http://google.com/'
    sp = None

    def __init__(self):
        self.username = SPConnection.username
        self.scope = SPConnection.scope
        self.client_id = SPConnection.client_id
        self.client_secret = SPConnection.client_secret
        self.redirect_uri = SPConnection.redirect_uri

    def set_all(self, username, client_id, client_secret):
        SPConnection.username = username
        SPConnection.scope = 'user-library-read user-library-modify playlist-modify-public playlist-modify-private user-read-private user-read-playback-state user-modify-playback-state'
        SPConnection.client_id = client_id
        SPConnection.client_secret = client_secret
        SPConnection.redirect_uri = 'http://google.com/'

    def reset_connection(self):
        token = spotipy.util.prompt_for_user_token(SPConnection.username, SPConnection.scope, SPConnection.client_id, SPConnection.client_secret, SPConnection.redirect_uri)
        sp = spotipy.Spotify(auth=token)
        return sp

    def get_connection(self):
        if SPConnection.sp:
            return SPConnection.sp
        else:
            return SPConnection().reset_connection()

def sp_connection(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        sp = SPConnection().get_connection()
        return f(*args, **kwargs, sp=sp)

    return wrapper

@sp_connection
def load_playlist_tracks(sp=None, playlist_id=None, liked=0):
    user = sp.current_user()['id']
    index = 0
    playlist_length = sp.user_playlist_tracks(user=user, playlist_id=playlist_id, limit=1)['total']
    
    while index < playlist_length:
        batch = sp.user_playlist_tracks(user=user, playlist_id=playlist_id, offset=index)
        
        for track in batch['items']:
            if not db_has_track(track_id=track['track']['id']):

                features = sp.audio_features(track['track']['id'])[0]

                track_data = (track['track']['id'], track['track']['name'], [artist['name'] for artist in track['track']['artists']][0], [artist['id'] for artist in track['track']['artists']][0], 
                            [artist['name'] for artist in track['track']['artists']][1] if len([artist['name'] for artist in track['track']['artists']]) > 1 else None,
                            [artist['id'] for artist in track['track']['artists']][1] if len([artist['id'] for artist in track['track']['artists']]) > 1 else None,
                            track['track']['popularity'], liked,
                            features['acousticness'], 
                            features['danceability'], features['duration_ms'],
                            features['energy'], features['instrumentalness'], features['key'],
                            features['liveness'], features['loudness'], features['mode'],
                            features['speechiness'], features['valence'], features['tempo'], features['time_signature'],
                            )

                db_insert_track(track=track_data)

        index += 100

@sp_connection
def load_saved_tracks(sp=None):
    index = 0
    saved_length = sp.current_user_saved_tracks(limit=1)['total']

    while index < saved_length:
        batch = sp.current_user_saved_tracks(offset=index)
        
        for track in batch['items']:
            if not db_has_track(track_id=track['track']['id']):

                features = sp.audio_features(track['track']['id'])[0]

                track_data = (track['track']['id'], track['track']['name'], [artist['name'] for artist in track['track']['artists']][0], [artist['id'] for artist in track['track']['artists']][0], 
                              [artist['name'] for artist in track['track']['artists']][1] if len([artist['name'] for artist in track['track']['artists']]) > 1 else None,
                              [artist['id'] for artist in track['track']['artists']][1] if len([artist['id'] for artist in track['track']['artists']]) > 1 else None,
                              track['track']['popularity'], 1,
                              features['acousticness'], 
                              features['danceability'], features['duration_ms'],
                              features['energy'], features['instrumentalness'], features['key'],
                              features['liveness'], features['loudness'], features['mode'],
                              features['speechiness'], features['valence'], features['tempo'], features['time_signature'],
                              )

                db_insert_track(track=track_data)


        index += 20

@sp_connection
def get_recommendations(sp=None, data=None):

    liked = data[data['liked'] == 1]['id'].values.tolist()
    disliked = data[data['liked'] == 0]['id'].values.tolist()

    samples = data[data['liked'] == 1].sample(n=10)
    samples = [row for index, row in samples.iterrows()]
    
    all_tracks = []
    all_ids = set()

    for sample in samples:
        for artist_id in [sample['artist1ID'], sample['artist2ID']]:
            if artist_id:

                related_artists = sp.artist_related_artists(artist_id)['artists'][:5]
                related_artists = [artist['id'] for artist in related_artists]

                for related_id in related_artists:
                    top_tracks = sp.artist_top_tracks(related_id)['tracks'][:5]

                    for track in top_tracks:
                        if track['id'] not in liked and track['id'] not in disliked and track['id'] not in all_ids:

                            features = sp.audio_features(track['id'])[0]

                            t = {
                                # MetaData
                                'id': track['id'],
                                'name': track['name'],
                                'artist1': [artist['name'] for artist in track['artists']][0],
                                'artist1ID': [artist['id'] for artist in track['artists']][0],
                                'artist2': [artist['name'] for artist in track['artists']][1] if len([artist['name'] for artist in track['artists']]) > 1 else None,
                                'artist2ID': [artist['id'] for artist in track['artists']][1] if len([artist['id'] for artist in track['artists']]) > 1 else None,
                                'popularity': track['popularity'],
                                'liked': None,

                                # Audio Features
                                'danceability': features['danceability'],
                                'energy': features['energy'],
                                'key': features['key'],
                                'loudness': features['loudness'],
                                'mode': features['mode'],
                                'speechiness': features['speechiness'],
                                'acousticness': features['acousticness'],
                                'instrumentalness': features['instrumentalness'],
                                'liveness': features['liveness'],
                                'valence': features['valence'],
                                'tempo': features['tempo'],
                                'duration_ms': features['duration_ms'],
                                'time_signature': features['time_signature']
                            }

                            all_ids.add(track['id'])
                            all_tracks.append(t)
            
    return all_tracks

@sp_connection
def create_playlist(sp=None, title='', description=''):
    user = sp.current_user()['id']
    playlist_id = sp.user_playlist_create(user=user, name=title, description=description)['id']
    return playlist_id

@sp_connection
def playlist_add_tracks(sp=None, playlist_id=None, tracks=None):
    user = sp.current_user()['id']
    sp.user_playlist_add_tracks(user=user, playlist_id=playlist_id, tracks=tracks)

# ----------------------------------------------------------------

def main(playlist_length, username, client_id, client_secret, redirect_uri, width=8):

    p1 = ProgressBar('Gathering Your Liked and Disliked Songs', steps=5, width=width, completion='Songs Gathered')

    p1.update(step_name='Connecting to Spotify')
    SPConnection().set_all(username, client_id, client_secret)
    # SPConnection().get_connection()

    p1.update(step_name='Connecting to the Database')
    connection = db_create_connection('records.db')
    db_create_table()

    p1.update(step_name='Collecting Your Saved Tracks')
    load_saved_tracks()

    p1.update(step_name='Collecting Your Disliked Tracks')
    load_playlist_tracks(playlist_id='6sd1N50ZULzrgoWX0ViDwC', liked=0)

    p1.update(step_name='Pulling Track Details from the Database')
    all_tracks = db_get_all()

    data = pd.DataFrame(all_tracks, columns=['id','name','artist1','artist1ID','artist2','artist2ID','popularity','liked','danceability','duration_ms','energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','time_signature'])
    print(data.head())

    # ----------------------------------------------------------------  

    p2 = ProgressBar('Decision Tree Classifier', steps=3, width=width, completion='Classifier Trained')

    train, test = train_test_split(data, test_size=0.15)

    p2.update(step_name='Building Tree')
    tree = DecisionTreeClassifier(min_samples_split=100)

    data_features = ['popularity', 
                    'danceability', 
                    'energy', 
                    'key', 
                    'loudness', 
                    'mode', 
                    'speechiness', 
                    'acousticness', 
                    'instrumentalness', 
                    'liveness', 
                    'valence', 
                    'tempo', 
                    'duration_ms', 
                    'time_signature']

    x_train = train[data_features]
    y_train = train['liked']

    x_test = test[data_features]
    y_test = test['liked']

    p2.update(step_name=f'Training Tree with {len(train)} samples')
    dt = tree.fit(x_train, y_train)

    p2.update(step_name=f'Testing Tree with {len(test)} samples')
    y_pred = tree.predict(x_test)

    score = accuracy_score(y_test, y_pred) * 100
    print(f'Decision Tree Accuracy: {round(score, 2)}')

    # ----------------------------------------------------------------

    p3 = ProgressBar('Generating Recommendations', steps=4, width=width, completion='Daily Playlist Created')
    
    p3.update(step_name='Gathering a Variety of Songs')
    new_tracks = get_recommendations(data=data)

    # ----------------------------------------------------------------

    date = datetime.strftime(datetime.now(), '%m/%d')
    playlist_title = f'Discover Daily {date}'
    p3.update(step_name=f'Creating Playlist {playlist_title}')
    playlist_description = f"Generated {str(date)} by Noah Tigner's Recommender Engine"

    playlist_id = create_playlist(title=playlist_title, description=playlist_description)

    # ----------------------------------------------------------------

    p3.update(step_name='Testing the Songs With the Classifier')
    t = pd.DataFrame(new_tracks)
    pred = t[data_features]
    predictions = tree.predict(pred)

    chosen = []
    for i in range(len(predictions)):
        if predictions[i] == 1:
            chosen.append(t.iloc[i]['id'])

    playlist_length = min([playlist_length, len(chosen) - 1, 100])
    p3.update(step_name=f'Filling the Playlist with {playlist_length} songs you might like')
    
    choices = random.sample(chosen, k=playlist_length)
    playlist_add_tracks(playlist_id=playlist_id, tracks=choices)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('playlist_length', help='Number of Tracks to Generate')

    try:
        args = parser.parse_args()
        playlist_length = int(args.playlist_length)
        
    except SystemExit as e:
        print()
        playlist_length = int(input('Enter The Number of Tracks to Generate: ', default=25, color='yellow'))

    try:
        username = os.environ['SPOTIPY_USERNAME']
        client_id = os.environ['SPOTIPY_CLIENT_ID']
        client_secret = os.environ['SPOTIPY_CLIENT_SECRET']
        redirect_uri = os.environ['SPOTIPY_REDIRECT_URI']
    except KeyError:
        print(f"In the future, consider setting the following up as environment variables.\nSee: https://spotipy.readthedocs.io/en/latest/#authorization-code-flow", color='red')
        username = input('Enter your Spotify username: ', color='yellow')
        client_id = input('Enter your Spotify Client ID: ', color='yellow')
        client_secret = input('Enter your Spotify Client Secret: ', color='yellow')
        redirect_uri = input('Enter your Redirect URI: ', color='yellow')

    main(playlist_length, username, client_id, client_secret, redirect_uri, width=8)
