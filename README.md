# songs-relate-me

This app recommends songs based on conversation history and can automatically create a Spotify playlist for you.

## Setup

1. Copy `.env.example` to `.env` and fill in your Spotify API credentials.
2. Install dependencies with `pip install -r requirements.txt`.

## Running the Application

You have several options to run the FastAPI application:

### Option 1: Using the run script (Recommended for development)
```bash
python run.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn app:app --host 0.0.0.0 --port 8020 --reload
```

### Option 3: Using the original app.py
```bash
python app.py
```

The server will start on `http://localhost:8020` and exposes endpoints to request song recommendations and create playlists.

## API Endpoints

- `POST /recommend` - Get song recommendations based on conversation history
- `GET /authorize` - Start Spotify OAuth flow
- `GET /callback` - Handle Spotify OAuth callback
- `POST /create_playlist` - Create a Spotify playlist with recommended songs
