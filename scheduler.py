import os
import sys
import argparse

from utils.utilities import my_print as print
from utils.utilities import my_input as input
from utils.utilities import ProgressBar, CountDown, print_json

from discoverdaily import main

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

    while True:
        main(playlist_length, username, client_id, client_secret, redirect_uri, width=16)

        CountDown(minutes=interval, message='Restarting in:', completion=(' '*32) + '\n')