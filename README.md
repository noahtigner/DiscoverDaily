# DiscoverDaily

A Recommender System that uses scikit-learn and the Spotify API.

Analyzes your Spotify library - including likes and dislikes - to produce music recommendations for you every day.

### Exploratory Data Analysis of my musical taste
![EDA](screenshots/eda.png)

### The Decision Tree Classifier
![Tree](screenshots/tree.png)

### Use

You will need a Spotify Client ID and Client SECRET. See: [Spotify Authorization](https://developer.spotify.com/dashboard/applications)

The application will analyze your library, as well as over 2000 songs that I have arbitrarily deemed 'bad'.

* export your SPOTIPY_USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI

    * See [spotipy env](https://spotipy.readthedocs.io/en/latest/#authorization-code-flow)
    
* To run on a daily basis:

    * run run.sh
    
* For a single use:

    * run discoverdaily.py

    * args:

        * playlist_length: number of track recommendations to generate

### Development

Written in Python.

Dependencies: 

* sklearn for machine learning

* pandas for data management

* Spotipy, a wrapper around the Spotify API

* sqlite3 for DBM

## Author

Noah Tigner

noahzanetigner@gmail.com

