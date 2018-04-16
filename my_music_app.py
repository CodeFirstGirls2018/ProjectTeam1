from flask import Flask, render_template, request, redirect, url_for, session
import requests
import urllib
import json
import random
from requests.auth import HTTPBasicAuth
import os
import sys

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


def request_user_data_token(code):
    """
    Finction that requests refresh and access tokens from Spotify API.
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

    # Check response from Spotify API
    # Something went wrong. Ask user to try to login again
    if response_data.status_code != 200:
        return redirect(url_for('index'))

    # Success. Convert response data in json
    data = response_data.json()
    access_data = {
        'access_token': data["access_token"],
        'refresh_token': data["refresh_token"],
        'token_type': data["token_type"],
        'expires_in': data["expires_in"],
    }
    return access_data


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
    #url_arg = params_query_string(payload)
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


def get_artist_top_tracks(artistID):
    '''
    Function that gets Artist's Top Tracks
    Input: artist ID
    Returns: dict where key is a name of the track and value - uri of the track
    '''
    # Please, write the code
    pass


def get_current_user_profile(user_data_token):
    '''
    Function that Get Current User's Profile
    Input: user data related token
    Returns: user ID
    '''
    # Please, write the code
    pass


def create_empty_playlist(userID):
    '''
    Function that creates an empty playlist for user with userID
    Input: user ID
    Returns: ID of the newly created playlist
    '''
    # Please, write the code
    pass


def add_traks_to_playlist(userID, playlistID, uris):
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
    # Please, write the code
    pass


@app.route("/")
def index():
    '''
    Main packages
    !!! On main page should be added:
    1) In file index.html: ask user what track he/she would like to listen to.
    '''
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

    # request_token function returns dict of access values
    access_data = request_user_data_token(code)

    # Session allows to store information specific to a user from one request
    # to the next one
    session['access_data'] = access_data
    # After the access_data was received our App can use Spotify API
    return render_template("ask_artist.html")


@app.route("/search_artist", methods=["POST"])
def artists_search():
    """
    Example decorator that uses access_data to get data from Spotify API.
    In this example the artist is searched by his/her name
    """
    # Check if user is logged in
    if "access_data" not in session:
        return redirect(url_for('index'))
    # User is logged in
    # Get access token from user's request
    token = session['access_data']['access_token']
    # Get data that user post to App
    form_data = request.form
    artist = form_data["artist"]
    # Get data in json format from search_artist request
    founded_artists = search_artist(token, artist)
    # Create dict of founded artists
    artist_dict = dict()
    for artist in founded_artists['artists']['items']:
        artist_dict[str(artist["name"])] = str(artist["id"])

    return render_template("req_to_show_tracks.html", artist_dict=artist_dict)


@app.route("/show_top_tracks", methods=["POST"])
def show_top_tracks():
    '''
    What to do:
    1)Get an Artist's Top Tracks using artist ID
    2) Display Artist's Top Tracks and ask user to create playlist
    3) Create template
    Returns: template
    Template shows Artist's Top Tracks and asks user to create playlist
    '''
    # Get artist ID from the request form
    form_data = request.form
    artistID = form_data["artist"]
    tracks = get_artist_top_tracks(artistID)
    return render_template("req_to_create_playlist.html", artist_dict=tracks)


@app.route("/create_playlist", methods=["POST"])
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

    form_data = request.form
    artistID = form_data["artist"]


    # Get list of artist's top tracks URIs
    track_uris = get_artist_top_tracks(artistID)
    # Get user ID from Current User's Profile
    userID = get_current_user_profile(token)
    # Create empty playlist using user ID
    playlistID = create_empty_playlist(userID)
    # Add Artist's Top Tracks to a Playlist
    response = add_traks_to_playlist(userID, playlistID, track_uris)
    if not response:
        return 'Sorry. An error accured. Playlist was not created'
    return 'Playlist successfully created'


# Requeest a token without asking user to log in
def call_api_token(code):
    endpoint = "https://accounts.spotify.com/api/token"
    make_request = requests.post(endpoint,
        data={"grant_type": "client_credentials",
              "client_id": CLIENT_ID,
              "client_secret": CLIENT_SECRET})
    return make_request


# Get a toke without asking user to log in
def final():
    code_api_token = request.args.get("code")
    #missing checks, eg. if access denied
    #no refresh token either
    spo_response = call_api_token(code_api_token)
    token = spo_response.json()["access_token"]
    return token


@app.route("/events_list", methods=["POST"])
def city_results():
    print request
    form_data = request.form
    city = form_data['city']
    main_list = parse_metroid_page(search_location(city))[:10]
    token = final()
    for item in main_list:
        parse_artist_id = (search_artist(token, item['artist_name']))
        artist_id = (parse_artist_id['artists']['items'][0]['id'])
        track_url = (get_sample_track(artist_id))
        item['track_url'] = track_url
    return render_template("events_list.html", main_list=main_list)


def search_location(search_query):
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
    token = final()
    headers = {
                'Authorization': 'Bearer ' + token}
    response = requests.get('https://api.spotify.com/v1/artists/' + artist_id
                            + '/top-tracks?country=SE', headers=headers)
    return response.json()['tracks'][0]['preview_url']


app.secret_key = os.urandom(30)

app.run(port=PORT, host="0.0.0.0", debug=True)
