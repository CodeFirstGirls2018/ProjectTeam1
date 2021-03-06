from flask import Flask, render_template, request, redirect, url_for, session
import requests
import urllib
import json
# import random
from requests.auth import HTTPBasicAuth
import os
import sys
import time

from pprint import pprint

app = Flask("MyMusicApp")

# Spotify App data
CLIENT_ID = "81c646550b95493ea3c94f1950f57543"
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

SONGKICK_API_KEY = os.getenv('SONGKICK_API_KEY')

# Port and Hostname that are used to launch App in heroku
PORT = int(os.getenv("PORT", 8888))
HOSTNAME = os.getenv("HEROKU_HOSTNAME", "http://localhost:{}".format(PORT))

# Redirect URI for Spotify API
REDIRECT_URI = HOSTNAME + "/callback"


# Requeest a token without asking user to log in
def call_api_token():
    endpoint = "https://accounts.spotify.com/api/token"
    make_request = requests.post(endpoint,
                                 data={"grant_type": "client_credentials",
                                       "client_id": CLIENT_ID,
                                       "client_secret": CLIENT_SECRET})
    return make_request


# Get a token without asking user to log in
def final():
    spo_response = call_api_token()
    # Check response from Spotify API
    # Something went wrong. Ask user to try again
    if spo_response.status_code != 200:
        return redirect(url_for('index'))
    return spo_response.json()


# Class that stores token not related to user
class TokenStorage:
    def __init__(self):
        self.token = None
        self.expire_in = None
        self.start = None

    # Check if token has exired
    def expire(self, time_now):
        if (time_now - self.start) > self.expire_in:
            return True
        return False

    # Get token first time or if expired
    def get_token(self, time_now):
        if self.token is None or self.expire(time_now):
            access_data = final()
            self.token = access_data['access_token']
            self.expire_in = access_data['expires_in']
            self.start = time.time()
        # print self.token
        return self.token


# Token to access to Spotify data that do not need access to user related data
# It is stored as class TokenStorage object
# To get token - TOKEN.get_token(time_now)
TOKEN = TokenStorage()


def request_user_data_token(code):
    """
    Function that requests refresh and access tokens from Spotify API.
    This token allows to change and request user related data.
    Step 4 in Guide
    """
    endpoint = "https://accounts.spotify.com/api/token"
    payload = {
              "grant_type": 'authorization_code',
              "code": code,
              "redirect_uri": REDIRECT_URI,
            }
    # Get refresh and access tokens
    response_data = requests.post(endpoint,
                                  auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                                  data=payload)

    # print "RESPONSE", response_data
    # Check response from Spotify API
    # Something went wrong. Ask user to try to login again
    if response_data.status_code != 200:
        return redirect(url_for('index'))

    # Success. Convert response data in json
    # data = response_data.json()
    # access_data = {
    #     'access_token': data["access_token"],
    #     'refresh_token': data["refresh_token"],
    #     'token_type': data["token_type"],
    #     'expires_in': data["expires_in"],
    # }
    return response_data.json()


# Function that checks if it is Python3 version
def python_version_3():
    if sys.version_info[0] == 3:
        return True
    return False


# Create params_query_string
def params_query_string(payload):
    # Python2 version
    url_arg = urllib.urlencode(payload)
    # Python3 version
    if python_version_3():
        url_arg = urllib.parse.urlencode(payload)
    return url_arg


# Function that replace special characters in val string using the %xx escape
def quote_params_val(val):
    # Python2 version
    value = urllib.quote(val)
    # Python3 version
    if python_version_3():
        value = urllib.parse.quote(val)
    return value


def searh_request(token, payload):
    '''
    Search request to Spotify API.
    Can be used both types of tokens.
    Payload specifies what you would like to search (in particular: album,
    artist, playlist, or track)
    '''
    # Endpoint to search
    endpoint = 'https://api.spotify.com/v1/search'
    # Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(token)}
    # Prepare URL for search request
    url_arg = "&".join(["{}={}".format(key, quote_params_val(val))
                       for key, val in payload.items()])
    # url_arg = params_query_string(payload)
    auth_url = endpoint + "/?" + url_arg
    # Get request to Spotify API to search
    search_response = requests.get(auth_url, headers=authorization_header)
    # Return the response in json format
    return search_response.json()


def search_artist(token, artist):
    '''
    Function that searches the artist
    Input: token and artist name
    Returns: array of arist objects in json format
    '''
    # Specify that we want to search the artist
    payload = {
              "q": artist,
              "type": "artist",
            }
    # Return array of arist objects in json format
    return searh_request(token, payload)


def get_artist_top_tracks(token, artistID):
    '''
    Function that gets Artist's Top Tracks
    Input: artist ID, token
    Returns: dict where key is a name of the track and value - uri of the track
    '''
    # Endpoint to search
    endpoint = 'https://api.spotify.com/v1/artists/' + artistID + '/top-tracks'
    # Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(token)}
    payload = {"country": "GB"}
    # Creating request URL
    url_arg = params_query_string(payload)
    auth_url = endpoint + "/?" + url_arg
    # Request Spotify API to get Top tracks
    top_tracks = requests.get(auth_url, headers=authorization_header)
    # Check if Spotify have Top Track for this artist

    return top_tracks.json()


def get_artist_data_by_id(artistID, token):
    '''
    Request Spotify API for artist data using artist ID
    '''
    # Endpint to get artist related form_data
    endpoint = "https://api.spotify.com/v1/artists/" + artistID
    # Authorization header
    authorization_header = {"Authorization": "Bearer {}".format(token)}
    # Request Spotify API artist related data
    artist_data = requests.get(endpoint, headers=authorization_header)
    # Returns artist_data in json format
    return artist_data.json()


def get_current_user_profile(user_data_token):
    '''
    Function that Get Current User's Profile
    Input: user data related token
    Returns: user ID
    '''
    # Endpint to get current user profile
    endpoint = "https://api.spotify.com/v1/me"
    # Authorization header
    authorization_header = {"Authorization": "Bearer {}".format(user_data_token)}
    # Request Spotify API artist related data
    user_data = requests.get(endpoint, headers=authorization_header)
    # Returns user_data in json format
    return user_data.json()


def create_empty_playlist(userID, artist_name, user_data_token):
    '''
    Function that creates an empty playlist for user with userID
    Input: user ID
    Returns: ID of the newly created playlist
    '''
    # Endpint to get current user profile
    endpoint = "https://api.spotify.com/v1/users/" + userID + "/playlists"
    # Authorization header
    authorization_header = {"Authorization": "Bearer {}".format(user_data_token)}
    # Specify params of new playlist
    payload = {"name": artist_name}
    playlist_data = requests.post(endpoint,
                                  headers=authorization_header,
                                  json=payload)
    # print "URL", playlist_data.url
    # print "RESPONSE FOR NEW PLAYLIST", playlist_data.json()
    return playlist_data.json()


def add_traks_to_playlist(userID, playlistID, uris, user_data_token):
    '''
    Add Tracks to a Playlist
    Input:
    - user ID and user's playlist ID where you want to add Tracks
    - uris - list of Spotify URIs for tracks
    Returns
    For example: True or False
    True - tracks were added to playlist
    False - in case of error
    '''
    # Endpint to get current user profile
    endpoint = "https://api.spotify.com/v1/users/" + userID + "/playlists/" + playlistID + "/tracks"
    # Authorization header
    authorization_header = {"Authorization": "Bearer {}".format(user_data_token)}
    # Specify params of new playlist
    payload = {"uris": uris}
    playlist_with_tracks = requests.post(endpoint,
                                         headers=authorization_header,
                                         json=payload)

    return playlist_with_tracks


@app.route("/")
def index():
    '''
    Ask user:
    1) Artist to search, see artist's top tracks, listen 30 sec preview,
    add artist's top tracks to user's Spotify account new playlist
    2) Search city for upcoming gigs.
    '''
    if "tracks_uri" in session:
        session.pop('tracks_uri', None)
    if "artist_name" in session:
        session.pop("artist_name", None)
    return render_template("index.html")


@app.route("/login")
def requestAuth():
    """
    Application requests authorization from Spotify.
    Step 1 in Guide
    """
    endpoint = "https://accounts.spotify.com/authorize"
    payload = {
              "client_id": CLIENT_ID,
              "response_type": "code",
              "redirect_uri": REDIRECT_URI,
              # "state": "sdfdskjfhkdshfkj",
              "scope": "playlist-modify-public user-read-private",
              # "show_dialog": True
            }

    # Create query string from params
    # url_arg = "&".join(["{}={}".format(key, quote_params_val(val)) for
    #                    key, val in params.items()])
    url_arg = params_query_string(payload)

    # Request URL
    auth_url = endpoint + "/?" + url_arg
    #print "AUTH_URL", auth_url
    # User is redirected to Spotify where user is asked to authorize access to
    # his/her account within the scopes
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """
    After the user accepts (or denies) request to Log in his Spotify account,
    the Spotify Accounts service redirects back to the REDIRECT_URI.
    Step 3 in Guide.
    """
    # Check if the user has not accepted the request or an error has occurred
    if "error" in request.args:
        return redirect(url_for('index'))

    # On success response query string contains parameter "code".
    # Code is used to receive access data from Spotify
    code = request.args['code']
    # print "CODE", code
    # request_token function returns dict of access values
    access_data = request_user_data_token(code)
    # print "TOKEN", access_data["access_token"]
    # Session allows to store information specific to a user from one request
    # to the next one
    session['access_data'] = access_data
    # After the access_data was received our App can use Spotify API
    return redirect(url_for('create_playlist'))


@app.route("/search_artist", methods=["POST"])
def artists_search():
    """
    This decorator searches the artist by name
    Returns:
    1) Template with found artists that match user input
    2) Template that asks to repeat artist search in case of
    previous unsuccessful attempt.
    """
    # Check if user is logged in
    # if "access_data" not in session:
    #     return redirect(url_for('index'))
    # User is logged in
    # # Get access token from user's request
    # token = session['access_data']['access_token']

    # Not related to user token is stored as class TokenStorage object
    token = TOKEN.get_token(time.time())

    # Get data that user post to app on index page
    form_data = request.form
    artist = form_data["artist"]

    # Get data in json format from search_artist request
    found_artists = search_artist(token, artist)

    # Check if there is artist match at Spotify
    if not found_artists['artists']['items']:
        return render_template("ask_artist.html", artist=artist.title())

    # Create dict of found artists
    artist_dict = dict()
    for artist in found_artists['artists']['items']:
        artist_dict[artist["name"]] = str(artist["id"])

    return render_template("req_to_show_tracks.html", artist_dict=artist_dict)


@app.route("/show_top_tracks", methods=["POST"])
def show_top_tracks():
    '''
    This decorator does next:
    1) Gets an Artist's Top Tracks using artist ID
    2) Displays Artist name, image, Artist's Top Tracks and
    asks user to create playlist
    Returns: Template shows Artist's Top Tracks and asks user
             to create playlist
    '''
    # # Check if user is logged in
    # if "access_data" not in session:
    #     return redirect(url_for('index'))
    # User is logged in
    # Get access token from user's request
    # token = session['access_data']['access_token']

    # Not related to user token is stored as class TokenStorage object
    token = TOKEN.get_token(time.time())

    # Get artist ID from the request form
    form_data = request.form
    artistID = form_data["artist"]
    # Get artist data in json format
    artist_data = get_artist_data_by_id(artistID, token)
    # Artist name
    artist_name = artist_data["name"]
    # Artist picture
    artist_pic = artist_data["images"]
    # Get artist top tracks
    top_tracks = get_artist_top_tracks(token, artistID)
    # print top_tracks
    # Initiate dictionary to story only needed data
    tracks_dict = {}
    tracks_uri = []
    # Storing in dict name, uri and preview_url of top tracks
    for track in top_tracks["tracks"]:
        tracks_dict[track["name"]] = {"preview_url": track["preview_url"]}
        tracks_uri.append(track["uri"])
    # Session allows to store information specific to a user from one request
    # to the next one
    session['artist_name'] = artist_name
    session['tracks_uri'] = tracks_uri
    return render_template("req_to_create_playlist.html",
                           tracks_dict=tracks_dict,
                           name=artist_name.title(),
                           picture=artist_pic)


@app.route("/create_playlist")
def create_playlist():
    '''
    What to do:
    1) Get Current User's Profile:
    https://beta.developer.spotify.com/documentation/web-api/reference/users-profile/get-current-users-profile/
    2) Take from User's Profile "user ID":
    3) Create empty playlist using user ID:
    https://beta.developer.spotify.com/documentation/web-api/reference/playlists/create-playlist/
    4) Add Artist's Top Tracks to a Playlist:
    https://beta.developer.spotify.com/documentation/web-api/reference/playlists/add-tracks-to-playlist/

    Returns: template
    Template saies that playlist is successfully created and there is a link
    to Index page
    '''

    # Check if user is logged in
    if "access_data" not in session:
        return redirect(url_for('index'))
    # User is logged in
    # Get access token from user's request
    token = session['access_data']['access_token']
    # print "TOKEN", token
    if "tracks_uri" not in session:
        return redirect(url_for('index'))

    tracks_uri = session['tracks_uri']
    artist_name = session['artist_name']
    session.pop('tracks_uri', None)
    session.pop('artist_name', None)
    # print "TRACKS_URI", tracks_uri
    # Get user ID from Current User's Profile
    userID = get_current_user_profile(token)["id"]
    # print "USER ID", userID
    # Create empty playlist using user ID
    playlistID = create_empty_playlist(userID, artist_name, token)["id"]
    # playlistID = None
    # Add Artist's Top Tracks to a Playlist
    response = add_traks_to_playlist(userID, playlistID, tracks_uri, token)
    return render_template("playlist_creation.html", res=response)
    # if response.status_code != 201:
    #     return 'Sorry. An error accured. Playlist was not created'
    # return 'Playlist successfully created'


@app.route("/events_list", methods=["POST"])
def city_results():
    '''
    Function captures city, searchs and parses metroID.
    Then parses the result (main_list) for track_url, adds it to the main_list of results
    and passes it to html to be listed.
    '''
    form_data = request.form
    city = form_data['city']
    main_list = parse_metroid_page(search_location(city))[:10]
    # Not related to user token is stored as class TokenStorage object
    token = TOKEN.get_token(time.time())
    for item in main_list:
        try:
            parse_artist_id = (search_artist(token, item['artist_name']))
            artist_id = (parse_artist_id['artists']['items'][0]['id'])
            track_url = (get_sample_track(artist_id))
            item['track_url'] = track_url
        except (KeyError, IndexError):
            continue
    return render_template("events_list.html", main_list=main_list)


def search_location(search_query):
    '''
    Function searchs city name, returns metroID.
    '''
    o = urllib.urlopen("http://api.songkick.com/api/3.0/search/locations.json?query="
                       + search_query + "&apikey=" + SONGKICK_API_KEY)
    page = json.loads(o.read())
    a = page.values()
    b = a[0][u'results']
    c = b[u'location']
    d = c[0][u'metroArea']
    result = d[u'id']
    return result


def parse_metroid_page(metro_id):
    '''
    Songkick groups locations under metroIDs to make recommendations to users.
    Function parses metroID to get event, artist_name, location, date and ticket sale link.
    '''
    metro_id = str(metro_id)
    o = urllib.urlopen("http://api.songkick.com/api/3.0/metro_areas/"
                       + metro_id + "/calendar.json?apikey=" + SONGKICK_API_KEY)
    page = json.loads(o.read())
    result = []
    a = page.values()
    b = a[0][u'results']
    c = b[u'event']
    for i in range(0, len(c)):
        try:
            item = {}
            item['event'] = c[i][u'displayName']
            item['artist_name'] = c[i][u'performance'][0][u'artist'][u'displayName']
            item['location'] = c[i][u'location'][u'city']
            item['start'] = c[i][u'start'][u'date']
            item['link'] = c[i][u'uri']
            result.append(item)
        except KeyError:
            continue
    return result


def get_sample_track(artist_id):
    '''
    Function that uses artist_id to get the first track from artist's top-tracks
    Input: artist ID
    Returns: preview URL of the first track from artist's top-tracks
    '''
    # Not related to user token is stored as class TokenStorage object
    token = TOKEN.get_token(time.time())
    headers = {
                'Authorization': 'Bearer ' + token}
    response = requests.get('https://api.spotify.com/v1/artists/' + artist_id
                            + '/top-tracks?country=SE', headers=headers)
    return response.json()['tracks'][0]['preview_url']


app.secret_key = os.urandom(30)

app.run(port=PORT, host="0.0.0.0", debug=True)
