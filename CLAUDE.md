# Mum's Disco — Streamlit App

Quarterly crowdsourced playlist app. Guests search for songs, confirm them, and they get saved to Google Sheets. A separate script (`playlist getter/live_playlist_sync.py`) watches the Sheet and adds songs to YouTube Music.

## The other repo
`C:\Users\terfy\Documents\GitHub\playlist getter\` — runs locally on the night to sync to YouTube Music.

## Architecture
```
Guest → this Streamlit app → TinyDB (playlist.json) + Google Sheets
                                                             ↓
                                              live_playlist_sync.py (run locally)
                                                             ↓
                                                  YouTube Music playlist
```

## Search
Uses the **iTunes Search API** — free, no API key, no account needed.

**Why not Spotify:** Requires paid subscription for server-side search since late 2024.
**Why not YouTube Music (ytmusicapi):** Returns empty results from Streamlit Cloud IPs — blocked by YouTube.

## Streamlit Cloud secrets needed
Only `[gspread]` — no Spotify or YouTube credentials required.

```toml
[gspread]
type = "service_account"
project_id = "mums-disco"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "mums-disco-service@mums-disco.iam.gserviceaccount.com"
client_id = "..."
```

## Resetting between events
Delete `playlist.json` via Streamlit Cloud file manager to start fresh.

## Key files
- `mums_disco_app.py` — the whole app
- `requirements.txt` — no ytmusicapi or Spotify packages needed
- `playlist.json` — TinyDB, auto-created, lives on Streamlit Cloud
