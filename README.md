# 🎵 Mum's Disco

A Streamlit app for crowdsourcing playlists! Users can search for songs via Spotify API, confirm their selection, and add them to a shared playlist that's stored locally and backed up to Google Sheets.

## Features

- **Song Search**: Search for songs using Spotify's Web API
- **Duplicate Prevention**: Case-insensitive duplicate checking
- **Real-time Playlist**: All users see the same live playlist
- **Audio Preview**: Listen to song previews when available
- **Backup**: Automatic backup to Google Sheets
- **Export**: Download playlist as CSV

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your `Client ID` and `Client Secret`

### 3. Set up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create a Service Account:
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download the JSON key file
5. Share your Google Sheet with the service account email

### 4. Configure Secrets

Create `.streamlit/secrets.toml` with your credentials:

```toml
[spotify]
client_id = "your_spotify_client_id"
client_secret = "your_spotify_client_secret"

[gspread]
type = "service_account"
project_id = "your_project_id"
private_key_id = "your_private_key_id" 
private_key = "-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END PRIVATE KEY-----\n"
client_email = "your_service_account_email"
client_id = "your_client_id"
```

**Note**: For the `private_key`, make sure to include the full key with newlines (`\n`) as shown above.

## Running the App

```bash
streamlit run mums_disco_app.py
```

The app will be available at `http://localhost:8501`

## How It Works

1. **Search**: Users type in a song name
2. **Find**: App searches Spotify for the closest match
3. **Confirm**: User sees the result (title, artist, album art, preview) and confirms
4. **Save**: Confirmed songs are saved to local TinyDB (`playlist.json`)
5. **Backup**: Songs are automatically backed up to Google Sheets
6. **Display**: The full playlist is shown to all users, newest first

## File Structure

```
mums-disco/
├── streamlit_app.py      # Main application
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .streamlit/
│   └── secrets.toml     # API credentials (create this)
└── playlist.json        # Local database (auto-created)
```

## Features in Detail

### Duplicate Prevention
- Case-insensitive checking for song title + artist
- Prevents the same song from being added twice

### Spotify Integration
- Uses Client Credentials Flow (no user login required)
- Searches for exact matches
- Shows album artwork and audio previews
- Provides direct Spotify links

### Data Persistence
- **Local**: TinyDB stores playlist in `playlist.json`
- **Cloud**: Google Sheets backup for redundancy
- **Export**: CSV download option

### User Experience
- Clean, responsive interface
- Real-time updates across all users
- Audio previews for song confirmation
- Newest songs displayed first

## Troubleshooting

### Spotify API Issues
- Verify your Client ID and Client Secret
- Make sure your Spotify app is not in development mode restrictions

### Google Sheets Issues
- Ensure the service account email has access to your spreadsheet
- Check that the Google Sheets API is enabled in your project
- Verify the private key format in secrets.toml

### Database Issues
- The `playlist.json` file is created automatically
- If corrupted, delete it and restart the app

## Contributing

Feel free to submit issues and pull requests!

## License

This project is open source and available under the MIT License.