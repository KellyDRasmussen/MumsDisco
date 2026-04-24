# 🎵 Mum's Disco

Quarterly crowdsourced playlist app. Party guests add songs via a Streamlit web app, which backs them up to Google Sheets. A separate script on your laptop watches the Sheet and adds new songs to your YouTube Music playlist in real time.

---

## How it works

```
Guest types song → Streamlit app (iTunes search) → Google Sheets
                                                         ↓
                              live_playlist_sync.py watches Sheet
                                                         ↓
                                          YouTube Music playlist
```

---

## Before each event

### 1. Refresh the YouTube Music auth

The `browser.json` cookies in the `playlist getter` folder expire after a few weeks. Refresh them before each event:

1. Go to [music.youtube.com](https://music.youtube.com) and make sure you're logged in
2. Open DevTools (F12) → Network tab → filter by `browse`
3. Click **Library** in the sidebar to trigger a request
4. Click the `browse` request → Headers tab → Request Headers
5. Copy all the request headers
6. Open `playlist getter/browser.json` and replace the values for:
   - `authorization`
   - `cookie`
7. Make sure `accept-encoding` stays as `gzip, deflate` (not `br` or `zstd`)

### 2. Clear the playlist app database

The Streamlit app stores songs in a `playlist.json` TinyDB file on Streamlit Cloud. If you want a fresh playlist each event, go to your Streamlit Cloud dashboard, find the app, and delete `playlist.json` from the file manager — or just leave it and it'll keep accumulating across events.

### 3. Share the app link with guests

Your Streamlit app URL is the link guests use to add songs. Share it however you like (QR code works well).

---

## On the night

Run this on your laptop to sync songs from the Sheet to YouTube Music in real time:

```bash
cd "playlist getter"
python live_playlist_sync.py
```

It checks for new songs every 30 seconds and adds them automatically. Leave it running in the background. Press `Ctrl+C` to stop.

The YouTube Music playlist it syncs to:
`https://music.youtube.com/playlist?list=PLFINE5yyf5zKXCoFvhNoTrrEwuBC9MlsP`

---

## Repos

| Folder | What it does |
|--------|-------------|
| `MumsDisco/` | Streamlit app — guests use this to add songs |
| `playlist getter/` | Scripts that sync Google Sheets → YouTube Music |

---

## Troubleshooting

**"No songs found" in the Streamlit app**
The iTunes search API is used — no API key needed. If this breaks, check that the app deployed correctly on Streamlit Cloud and that there are no errors in the logs.

**YouTube Music sync not adding songs**
Almost certainly expired cookies. Redo step 1 above (refresh `browser.json`). Make sure `accept-encoding` is `gzip, deflate` — if you paste raw browser headers it'll include `br` which breaks things.

**Songs not appearing in Google Sheets**
Check the gspread credentials in Streamlit Cloud secrets are still valid. The service account is `mums-disco-service@mums-disco.iam.gserviceaccount.com` and the sheet must be shared with that email.

**Streamlit app showing old songs from last event**
Delete `playlist.json` via the Streamlit Cloud file manager and restart the app.
