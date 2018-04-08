from flask import Flask, render_template, request, redirect, url_for, session
import requests
import urllib
from requests.auth import HTTPBasicAuth
import os

app = Flask("MyMusicApp")

# Spotify App data
CLIENT_ID = "81c646550b95493ea3c94f1950f57543"
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Port and Hostname that are used to launch App in heroku
PORT = int(os.getenv("PORT", 8888))
HOSTNAME = os.getenv("HEROKU_HOSTNAME", "http://localhost:{}".format(PORT))

# Redirect URI for Spotify API
REDIRECT_URI = HOSTNAME + "/callback"


@app.route("/")
def index():
    # Main page
    return render_template("index.html")


@app.route("/login")
def requestAuth():
    """
    Application requests authorization from Spotify.
    Step 1 in Guide
    """
    endpoint = "https://accounts.spotify.com/authorize"
    params = {
              "client_id": CLIENT_ID,
              "response_type": "code",
              "redirect_uri": REDIRECT_URI,
              # "state": "sdfdskjfhkdshfkj",
              "scope": "playlist-modify-public playlist-modify-private",
              # "show_dialog": True
            }
    # Create query string from params
    url_arg = "&".join(["{}={}".format(key, urllib.parse.quote(val)) for
                        key, val in params.items()])
    # Request URL
    auth_url = endpoint + "/?" + url_arg
    # User is redirected to Spotify where user is asked to authorize access to
    # his/her account within the scopes
    return redirect(auth_url)


def request_token(code):
    """
    Finction that requests refresh and access tokens from Spotify API
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
    access_data = request_token(code)

    # Session allows to store information specific to a user from one request
    # to the next one
    session['access_data'] = access_data
    # After the access_data was received our App can use Spotify API
    return render_template("ask_artist.html")


@app.route("/search_artist", methods=["POST"])
def search_artist():
    """
    Example decorator that uses access_data to get data from Spotify API.
    In this example the artist is searched by his/her name
    """
    # Check if user is logged in
    if "access_data" not in session:
        return redirect(url_for('index'))

    # User is logged in
    # Get access_token from user's request
    access_token = session['access_data']['access_token']

    # Get data that user post to App
    form_data = request.form
    artist = form_data["artist"]

    # Endpoint to search
    endpoint = 'https://api.spotify.com/v1/search'

    # Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    payload = {
              "q": artist,
              "type": "artist",
            }
    # Search for artist
    url_arg = "&".join(["{}={}".format(key, urllib.parse.quote(val))
                        for key, val in payload.items()])
    auth_url = endpoint + "/?" + url_arg

    # Get request to Spotify API to search an artist
    search_artist_response = requests.get(auth_url,
                                          headers=authorization_header)
    # Convert response data in json
    founded_artists = search_artist_response.json()

    # Create list of founded artists
    artists_list = [art['name'] for art in founded_artists['artists']['items']]
    return str(artists_list)


app.secret_key = os.urandom(30)

app.run(port=PORT, host="0.0.0.0", debug=True)
