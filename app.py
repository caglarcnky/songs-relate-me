import os
import uuid
from urllib.parse import urlencode

from flask import Flask, request, redirect, session, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Simple placeholder recommendation function
# In a real application this would use conversation history and an LLM
# to determine relevant songs.
def recommend_songs(history: str):
    return [
        "spotify:track:4uLU6hMCjMI75M1A2tKUQC",  # Never Gonna Give You Up
        "spotify:track:7GhIk7Il098yCjg4BQjzvb",  # Take on Me
    ]


@app.route("/recommend", methods=["POST"])
def recommend_endpoint():
    data = request.get_json() or {}
    history = data.get("history", "")
    songs = recommend_songs(history)
    return jsonify({"songs": songs})


@app.route("/authorize")
def authorize():
    state = uuid.uuid4().hex
    session["state"] = state
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "state": state,
        "scope": "playlist-modify-private playlist-modify-public",
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if state != session.get("state"):
        return "State mismatch", 400

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        },
    )
    token_info = resp.json()
    session["access_token"] = token_info.get("access_token")
    return "Authentication successful. You may close this window."  # noqa: E501


def get_user_id(token: str) -> str:
    resp = requests.get(
        f"{API_BASE}/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json().get("id")


def create_playlist(token: str, user_id: str, name: str) -> str:
    resp = requests.post(
        f"{API_BASE}/users/{user_id}/playlists",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"name": name, "public": False},
    )
    return resp.json().get("id")


def add_tracks(token: str, playlist_id: str, tracks):
    requests.post(
        f"{API_BASE}/playlists/{playlist_id}/tracks",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"uris": tracks},
    )


@app.route("/create_playlist", methods=["POST"])
def create_playlist_endpoint():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}
    tracks = data.get("songs")
    if not tracks:
        return jsonify({"error": "No songs provided"}), 400

    user_id = get_user_id(token)
    playlist_id = create_playlist(token, user_id, "ChatGPT Recommendations")
    add_tracks(token, playlist_id, tracks)
    return jsonify({"playlist_id": playlist_id})


if __name__ == "__main__":
    app.run(debug=True)
