from flask import Flask, render_template, request, redirect, url_for, session
import requests
import urllib
from requests.auth import HTTPBasicAuth
import os

app = Flask("MyMusicApp")

CLIENT_ID = "81c646550b95493ea3c94f1950f57543"
CLIENT_SECRET = os.getenv('CLIENT_SECRET')


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def requestAuth():
    #print("Requeste aouthorisation")
    endpoint = "https://accounts.spotify.com/authorize"
    params = {
              "client_id": CLIENT_ID,
              "response_type": "code",
              "redirect_uri": "http://localhost:8888/callback",
              # "state": "sdfdskjfhkdshfkj",
              "scope": "playlist-modify-public playlist-modify-private",
              # "show_dialog": True
            }
    url_arg = "&".join(["{}={}".format(key, urllib.parse.quote(val)) for key, val in params.items()])
    auth_url = endpoint + "/?" + url_arg
    #print(auth_url)
    return redirect(auth_url)


def ask_token(code):
    endpoint = "https://accounts.spotify.com/api/token"
    payload = {
              "grant_type": 'authorization_code',
              "code": code,
              "redirect_uri": "http://localhost:8888/callback",
            }
    #client = '{}:{}'.format(CLIENT_ID, CLIENT_SECRET)

    #r = requests.post(api_URL, auth=HTTPBasicAuth('user', 'pass'), data=payload)
    #clientBase64Encoded = base64.b64encode(bytes(client, 'utf-8'))
    #headers = {"Authorization": "Basic %s" % clientBase64Encoded}
    response_data = requests.post(endpoint,
                                  auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                                  data=payload)
    #print(response_data)
    if response_data.status_code != 200:
        return redirect(url_for('index'))
    data = response_data.json()
    #print(data)
    access_data = {
        'access_token': data["access_token"],
        'refresh_token': data["refresh_token"],
        'token_type': data["token_type"],
        'expires_in': data["expires_in"],
    }
    return access_data


@app.route("/callback")
def callback():
    if "error" in request.args:
        return redirect(url_for('index'))
    code = request.args['code']
    #print('CODE', code)
    # Dict of access values
    access_data = ask_token(code)
    #print(access_data)
    session['access_data'] = access_data
    #session['access_token'] = access_data['access_token']
    return render_template("ask_artist.html")


@app.route("/search_artist", methods=["POST"])
def search_artist():
    if "access_data" not in session:
        return redirect(url_for('index'))
    access_token = session['access_data']['access_token']

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
    url_arg = "&".join(["{}={}".format(key, urllib.parse.quote(val)) for key, val in payload.items()])
    auth_url = endpoint + "/?" + url_arg
    search_artist_response = requests.get(auth_url, headers=authorization_header)

    founded_artists = search_artist_response.json()
    print(founded_artists)
    # Loop through artist
    artists_list = []
    for art in founded_artists['artists']['items']:
        artists_list.append(art['name'])
    print(artists_list)
    return str(artists_list)


app.secret_key = os.urandom(30)

app.run(port=8888, debug=True)
