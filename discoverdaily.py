import os
import sys
import argparse
from datetime import datetime
import random
from ast import literal_eval

from utils.utilities import my_print as print
from utils.utilities import my_input as input
from utils.utilities import ProgressBar, CountDown, print_json

import spotipy
import spotipy.util
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.oauth2 as oauth2

import pandas as pd

from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def get_connection(username, client_id, client_secret, redirect_uri):
    scope = 'user-library-read user-read-private user-read-playback-state user-modify-playback-state'
    redirect_uri = 'http://google.com/'

    token = spotipy.util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    sp = spotipy.Spotify(auth=token)

    return sp

def get_playlist_tracks(sp, user=None, playlist_id=None, liked=None):
    index = 0
    playlist_tracks = []
    playlist_length = sp.user_playlist_tracks(user=user, playlist_id=playlist_id, limit=1)['total']
    
    while index < playlist_length:
        batch = sp.user_playlist_tracks(user=user, playlist_id=playlist_id, offset=index)
    
        for track in batch['items']:
            
            features = sp.audio_features(track['track']['id'])[0]
        
            t = {
                # MetaData
                'id': track['track']['id'],
                'name': track['track']['name'],
                'artist(s)': [artist['name'] for artist in track['track']['artists']],
                'artist_id(s)': [artist['id'] for artist in track['track']['artists']],
                'popularity': track['track']['popularity'],
                'liked': liked,

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

            playlist_tracks.append(t)
        
        index += 100
        
    return playlist_tracks

def get_saved_tracks(sp):
    index = 0
    saved_tracks = []
    saved_length = sp.current_user_saved_tracks(limit=1)['total']

    while index < saved_length:
        batch = sp.current_user_saved_tracks(offset=index)
        
        for track in batch['items']:
            
            features = sp.audio_features(track['track']['id'])[0]
            
            t = {
                # MetaData
                'id': track['track']['id'],
                'name': track['track']['name'],
                'artist(s)': [artist['name'] for artist in track['track']['artists']],
                'artist_id(s)': [artist['id'] for artist in track['track']['artists']],
                'popularity': track['track']['popularity'],
                'liked': 1,
                
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
        
            saved_tracks.append(t)

        index += 20
        
    assert len(saved_tracks) == saved_length

    return saved_tracks

def get_new_songs(sp, data):

    samples = data[data['liked'] == 1].sample(n=10)
    samples = [row for index, row in samples.iterrows()]
    
    all_tracks = []

    for sample in samples:
        for artist_id in literal_eval(sample['artist_id(s)']):

            related_artists = sp.artist_related_artists(artist_id)['artists'][:5]
            related_artists = [artist['id'] for artist in related_artists]

            for related_id in related_artists:
                top_tracks = sp.artist_top_tracks(related_id)['tracks'][:2]

                for track in top_tracks:
                    if track['id'] not in liked and track['id'] not in disliked:

                        features = sp.audio_features(track['id'])[0]

                        t = {
                            # MetaData
                            'id': track['id'],
                            'name': track['name'],
                            'artist(s)': [artist['name'] for artist in track['artists']],
                            'artist_id(s)': [artist['id'] for artist in track['artists']],
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

                        all_tracks.append(t)
            
    return all_tracks

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('playlist_length', help='Number of Tracks to Generate')
    parser.add_argument('interval', help='How many minutes there are between iterations')

    try:
        args = parser.parse_args()
        playlist_length = int(args.playlist_length)
        interval = float(args.interval)
        
    except SystemExit as e:
        print()
        playlist_length = int(input('Enter The Number of Tracks to Generate: ', default=25, color='yellow'))
        interval = float(input('Enter Interval in Minutes: ', default=1440, color='yellow'))

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

    # ----------------------------------------------------------------  

    width = 48

    while True:
        date = datetime.strftime(datetime.now(), '%m_%d')

        p1 = ProgressBar('Gathering Your Liked and Disliked Songs', steps=4, width=width, completion='Songs Gathered')

        p1.update(step_name='Connecting to Spotify')
        sp = get_connection(username, client_id, client_secret, redirect_uri)
        user = sp.current_user()

        if not os.path.exists(f'{date}.csv'):

            p1.update(step_name='Collecting Your Saved Tracks')
            saved_tracks = get_saved_tracks(sp=sp)

            p1.update(step_name='Collecting Your Disliked Tracks')
            disliked_tracks = get_playlist_tracks(sp=sp, user=user['id'], playlist_id='6sd1N50ZULzrgoWX0ViDwC', liked=0)

            p1.update(step_name='Writing Data to csv')
            all_tracks = []
            all_tracks.extend(saved_tracks)
            all_tracks.extend(disliked_tracks)
            data = pd.DataFrame(all_tracks)
            data = data.set_index('id')
            data.to_csv(r'{}.csv'.format(date))

        else:
            p1.update(step_name='Reading Data from csv')
            p1.update(step_name='Reading Data from csv')
            p1.update(step_name='Reading Data from csv')
            data = pd.read_csv(f'{date}.csv')

        train, test = train_test_split(data, test_size=0.15)

        # ----------------------------------------------------------------  

        p2 = ProgressBar('Decision Tree Classifier', steps=3, width=width, completion='Classifier Trained')

        p2.update(step_name='Building Tree')
        tree = DecisionTreeClassifier(min_samples_split=150)

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
        print(f'Decision Tree Accuracy: {round(score, 2)}') # 85.38, 86.16

        # ----------------------------------------------------------------

        p3 = ProgressBar('Generating Recommendations', steps=4, width=width, completion='Daily Playlist Created')

        liked = data[data['liked'] == 1]['id'].values.tolist()
        disliked = data[data['liked'] == 0]['id'].values.tolist()

        p3.update(step_name='Gathering a Variety of Songs')
        all_tracks = get_new_songs(sp, data)

        # ----------------------------------------------------------------

        playlist_title = f'DiscoverDaily {date}'
        p3.update(step_name=f'Creating Playlist {playlist_title}')
        playlist_description = 'Generated {date} by Noah Tigner\'s Recommender Engine.\nSee https://bitbucket.org/noahtigner/discoverdaily/src/master/'

        playlist_id = sp.user_playlist_create(user=user['id'], name=playlist_title, description=playlist_description)['id']

        # ----------------------------------------------------------------

        p3.update(step_name='Testing the Songs With the Classifier')
        t = pd.DataFrame(all_tracks)
        pred = t[data_features]
        predictions = tree.predict(pred)

        chosen = []
        for i in range(len(predictions)):
            if predictions[i] == 1:
                chosen.append(t.iloc[i]['id'])

        p3.update(step_name='Filling the Playlist with songs you might like')
        choices = random.sample(chosen, k=playlist_length)
        sp.user_playlist_add_tracks(user=user['id'], playlist_id=playlist_id, tracks=choices)

        CountDown(minutes=interval, message='Restarting in:', completion=(' '*32) + '\n')
