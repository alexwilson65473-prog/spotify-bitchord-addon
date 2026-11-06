import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "MASUKKAN_CLIENT_ID_DISINI")
SPOTIFY_CLIENT_SECRET = os.getenv("MASUKKAN_CLIENT_SECRET_DISINI")

def get_client_credentials_token():
    auth_url = "https://accounts.spotify.com/api/token"
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    try:
        response = requests.post(auth_url, data=auth_data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception:
        pass
    return None

@app.route("/")
def index():
    return "Spotify BitChord Addon Server is Running!"

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "id": "com.spotify.bitchord.addon",
        "version": "1.0.0",
        "name": "Spotify Sync Addon",
        "description": "Addon BitChord terintegrasi Spotify untuk pemutaran dan riwayat.",
        "resources": ["catalog", "meta", "stream", "search"],
        "types": ["track", "album", "playlist", "artist"],
        "idPrefixes": ["spotify:"],
        "catalogs": [
            {
                "type": "track",
                "id": "spotify_top_tracks",
                "name": "Spotify Tracks & Search",
                "extra": [{"name": "search", "isRequired": False}]
            }
        ]
    })

@app.route("/catalog/<type>/<id>.json")
def catalog(type, id):
    token = get_client_credentials_token()
    if not token:
        return jsonify({"metas": []})
    
    headers = {"Authorization": f"Bearer {token}"}
    metas = []
    search_query = request.args.get("search")
    
    if type == "track":
        query = search_query if search_query else "pop"
        url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=20"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            tracks = res.json().get("tracks", {}).get("items", [])
            for t in tracks:
                metas.append({
                    "id": f"spotify:track:{t['id']}",
                    "type": "track",
                    "name": t['name'],
                    "artist": ", ".join([a['name'] for a in t['artists']]),
                    "poster": t['album']['images'][0]['url'] if t['album']['images'] else None,
                    "description": f"Album: {t['album']['name']}"
                })
    return jsonify({"metas": metas})

@app.route("/meta/<type>/<id>.json")
def meta(type, id):
    token = get_client_credentials_token()
    if not token:
        return jsonify({"meta": {}})
    
    headers = {"Authorization": f"Bearer {token}"}
    spotify_id = id.split(":")[-1]
    
    if type == "track":
        url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            t = res.json()
            meta_obj = {
                "id": id,
                "type": "track",
                "name": t['name'],
                "artist": ", ".join([a['name'] for a in t['artists']]),
                "album": t['album']['name'],
                "poster": t['album']['images'][0]['url'] if t['album']['images'] else None,
                "releaseInfo": t['album'].get('release_date', '')
            }
            return jsonify({"meta": meta_obj})
    return jsonify({"meta": {}})

@app.route("/stream/<type>/<id>.json")
def stream(type, id):
    spotify_id = id.split(":")[-1]
    return jsonify({
        "streams": [
            {
                "title": "Spotify Official Playback",
                "externalUrl": f"https://open.spotify.com/track/{spotify_id}",
                "url": f"https://open.spotify.com/track/{spotify_id}"
            }
        ]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
