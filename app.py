import os
import uuid
from urllib.parse import urlencode
import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Simple placeholder recommendation function
# In a real application this would use conversation history and an LLM
# to determine relevant songs.
def recommend_songs(history: str):
    return [
        "spotify:track:4uLU6hMCjMI75M1A2tKUQC",  # Never Gonna Give You Up
        "spotify:track:7GhIk7Il098yCjg4BQjzvb",  # Take on Me
    ]

class RecommendRequest(BaseModel):
    history: str = Field(..., example="I want to listen to 80s pop music")

class CreatePlaylistRequest(BaseModel):
    songs: List[str] = Field(..., example=[
        "spotify:track:4uLU6hMCjMI75M1A2tKUQC",
        "spotify:track:7GhIk7Il098yCjg4BQjzvb"
    ])

@app.post("/recommend")
async def recommend_endpoint(body: RecommendRequest, request: Request):
    history = body.history
    songs = recommend_songs(history)
    return {"songs": songs}


@app.get("/authorize")
async def authorize(request: Request):
    state = uuid.uuid4().hex
    request.session["state"] = state
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "state": state,
        "scope": "playlist-modify-private playlist-modify-public",
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if state != request.session.get("state"):
        return PlainTextResponse("State mismatch", status_code=400)

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
    request.session["access_token"] = token_info.get("access_token")
    return PlainTextResponse("Authentication successful. You may close this window.")


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


@app.post("/create_playlist")
async def create_playlist_endpoint(body: CreatePlaylistRequest, request: Request):
    token = request.session.get("access_token")
    if not token:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    tracks = body.songs
    if not tracks:
        return JSONResponse({"error": "No songs provided"}, status_code=400)
    user_id = get_user_id(token)
    playlist_id = create_playlist(token, user_id, "ChatGPT Recommendations")
    add_tracks(token, playlist_id, tracks)
    return {"playlist_id": playlist_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8020)