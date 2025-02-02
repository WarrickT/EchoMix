import requests
import urllib.parse

from flask import Flask, redirect, request, jsonify, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "12b167809764f08d121d6654bd33dd87"

CLIENT_ID = "45b6eef52733429dae5b54f4906819cf"
CLIENT_SECRET = "5fea48d8cd614e3385bfb9dd4dd53c93"
REDIRECT_URI = "http://localhost:5000/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"


# Home Route
@app.route("/")
def index():
    return "Welcome to EchoMix <a href='/login'>Login with Spotify</a>"


# Create login endpoint
@app.route("/login")
def login():
    scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": REDIRECT_URI,
        "show_dialog": True,
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})

    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        print(f"Token Info: {token_info}")

        if "access_token" in token_info:
            session["access_token"] = token_info["access_token"]
            session["refresh_token"] = token_info["refresh_token"]
            session["expires_at"] = (
                datetime.now().timestamp() + token_info["expires_in"]
            )
            return redirect("/playlists")
        else:
            return jsonify({"error": "Failed to retrieve access token."})


@app.route("/playlists")
def get_playlists():
    if "access_token" not in session:
        return redirect("/login")

    print(f"Access Token: {session['access_token']}")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh-token")

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(API_BASE_URL + "me/playlists", headers=headers)

    if response.status_code == 401:
        return jsonify({"error": "Unauthorized. Please check your access token."})

    playlists = response.json()

    return jsonify(playlists)


@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires-at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        print(f"New Token Info: {new_token_info}")

        if "access_token" in new_token_info:
            session["access_token"] = new_token_info["access_token"]
            session["expires_at"] = (
                datetime.now().timestamp() + new_token_info["expires_in"]
            )
            return redirect("/playlists")
        else:
            return jsonify({"error": "Failed to refresh access token."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
