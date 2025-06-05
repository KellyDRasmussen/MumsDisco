import streamlit as st
import requests
import base64
import json
import gspread
from tinydb import TinyDB, Query
from datetime import datetime
import pandas as pd
from typing import Optional, Dict, List

# Language content
LANGUAGES = {
    "en": {
        "title": "🎵 Mum's Disco",
        "subtitle": "Crowdsource the perfect playlist! 🕺💃",
        "add_song": "Add a Song",
        "song_input": "Song Name",
        "song_placeholder": "Enter a song title...",
        "song_help": "Type the name of a song you'd like to add to the playlist",
        "search_button": "🔍 Search",
        "searching": "Searching Spotify...",
        "found_song": "Found Song:",
        "by_artist": "by",
        "album": "Album:",
        "confirm_yes": "✅ Yes, add this!",
        "confirm_no": "❌ No, search again",
        "already_exists": "This song is already in the playlist!",
        "song_added": "Song added to playlist! 🎉",
        "add_failed": "Failed to add song to playlist.",
        "no_songs_found": "No songs found. Try a different search term.",
        "spotify_error": "Unable to connect to Spotify. Please try again later.",
        "current_playlist": "Current Playlist",
        "songs_count": "songs in the playlist",
        "export_playlist": "Export Playlist",
        "download_csv": "📥 Download as CSV",
        "no_songs_yet": "No songs in the playlist yet. Be the first to add one! 🎵",
        "footer": "Made with ❤️ for Mum's Disco | Powered by Spotify",
        "listen": "Listen",
        "added": "Added",
        "title_col": "Title",
        "artist_col": "Artist",
        "album_col": "Album",
        "spotify_col": "Spotify"
    },
    "da": {
        "title": "🎵 Mors Disko",
        "subtitle": "Crowdsource den perfekte playliste! 🕺💃",
        "add_song": "Tilføj en Sang",
        "song_input": "Sangtitel",
        "song_placeholder": "Indtast en sangtitel...",
        "song_help": "Skriv navnet på en sang, du gerne vil tilføje til playlisten",
        "search_button": "🔍 Søg",
        "searching": "Søger på Spotify...",
        "found_song": "Fundet Sang:",
        "by_artist": "af",
        "album": "Album:",
        "confirm_yes": "✅ Ja, tilføj denne!",
        "confirm_no": "❌ Nej, søg igen",
        "already_exists": "Denne sang er allerede i playlisten!",
        "song_added": "Sang tilføjet til playliste! 🎉",
        "add_failed": "Kunne ikke tilføje sang til playliste.",
        "no_songs_found": "Ingen sange fundet. Prøv et andet søgeord.",
        "spotify_error": "Kan ikke forbinde til Spotify. Prøv igen senere.",
        "current_playlist": "Nuværende Playliste",
        "songs_count": "sange i playlisten",
        "export_playlist": "Eksporter Playliste",
        "download_csv": "📥 Download som CSV",
        "no_songs_yet": "Ingen sange i playlisten endnu. Vær den første til at tilføje en! 🎵",
        "footer": "Lavet med ❤️ til Mors Disko | Drevet af Spotify",
        "listen": "Lyt",
        "added": "Tilføjet",
        "title_col": "Titel",
        "artist_col": "Kunstner",
        "album_col": "Album",
        "spotify_col": "Spotify"
    }
}

# Page configuration
st.set_page_config(
    page_title="🎵 Mum's Disco / Mors Disko",
    page_icon="🎵",
    layout="wide"
)

# Language selector in sidebar
with st.sidebar:
    st.subheader("🌍 Language / Sprog")
    language = st.selectbox(
        "Choose language / Vælg sprog:",
        options=["en", "da"],
        format_func=lambda x: "🇬🇧 English" if x == "en" else "🇩🇰 Dansk",
        index=0
    )

# Get current language content
t = LANGUAGES[language]

# Initialize database
@st.cache_resource
def init_database():
    return TinyDB('playlist.json')

# Initialize Google Sheets connection
@st.cache_resource
def init_gspread():
    try:
        credentials = {
            "type": st.secrets["gspread"]["type"],
            "project_id": st.secrets["gspread"]["project_id"],
            "private_key_id": st.secrets["gspread"]["private_key_id"],
            "private_key": st.secrets["gspread"]["private_key"],
            "client_email": st.secrets["gspread"]["client_email"],
            "client_id": st.secrets["gspread"]["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['gspread']['client_email']}"
        }
        
        gc = gspread.service_account_from_dict(credentials)
        return gc
    except Exception as e:
        st.error(f"Failed to initialize Google Sheets: {e}")
        return None

# Spotify API functions
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_spotify_token():
    """Get Spotify access token using Client Credentials Flow"""
    client_id = st.secrets["spotify"]["client_id"]
    client_secret = st.secrets["spotify"]["client_secret"]
    
    # Encode credentials
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Request token
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None

def search_spotify_song(song_name: str, token: str) -> Optional[Dict]:
    """Search for a song on Spotify"""
    if not token:
        return None
        
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": song_name,
        "type": "track",
        "limit": 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data["tracks"]["items"]:
            track = data["tracks"]["items"][0]
            return {
                "title": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "album": track["album"]["name"],
                "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "spotify_url": track["external_urls"]["spotify"],
                "preview_url": track["preview_url"]
            }
    return None

# Database functions
def song_exists(db: TinyDB, title: str, artist: str) -> bool:
    """Check if a song already exists in the database (case-insensitive)"""
    Song = Query()
    existing = db.search(
        (Song.title.test(lambda x: x.lower() == title.lower())) & 
        (Song.artist.test(lambda x: x.lower() == artist.lower()))
    )
    return len(existing) > 0

def add_song_to_db(db: TinyDB, song_data: Dict) -> bool:
    """Add a song to the database"""
    if song_exists(db, song_data["title"], song_data["artist"]):
        return False
    
    song_entry = {
        **song_data,
        "added_at": datetime.now().isoformat(),
        "id": len(db.all()) + 1
    }
    
    db.insert(song_entry)
    return True

def get_all_songs(db: TinyDB) -> List[Dict]:
    """Get all songs from database, newest first"""
    songs = db.all()
    return sorted(songs, key=lambda x: x.get("added_at", ""), reverse=True)

# Google Sheets functions
def backup_to_sheets(gc, song_data: Dict):
    """Backup song to Google Sheets"""
    if not gc:
        return False
        
    try:
        sheet_name = "Mums Disco Playlist"
        try:
            spreadsheet = gc.open(sheet_name)
            sheet = spreadsheet.sheet1
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(sheet_name)
            sheet = spreadsheet.sheet1
            sheet.append_row(["Title", "Artist", "Album", "Spotify URL", "Added At"])
        
        sheet.append_row([
            song_data["title"],
            song_data["artist"],
            song_data["album"],
            song_data["spotify_url"],
            song_data.get("added_at", datetime.now().isoformat())
        ])
        return True
        
    except Exception as e:
        st.error(f"Backup failed: {str(e)}")
        return False

# Main app
def main():
    # Initialize resources
    db = init_database()
    gc = init_gspread()
    
    # Header
    st.title(t["title"])
    st.markdown(f"### {t['subtitle']}")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader(t["add_song"])
        
        # Song input form
        with st.form("add_song_form"):
            song_input = st.text_input(
                t["song_input"],
                placeholder=t["song_placeholder"],
                help=t["song_help"]
            )
            
            search_button = st.form_submit_button(t["search_button"], use_container_width=True)
        
        # Handle song search
        if search_button and song_input.strip():
            with st.spinner(t["searching"]):
                token = get_spotify_token()
                if token:
                    song_data = search_spotify_song(song_input.strip(), token)
                    
                    if song_data:
                        st.session_state.found_song = song_data
                        st.session_state.show_confirmation = True
                    else:
                        st.error(t["no_songs_found"])
                else:
                    st.error(t["spotify_error"])
        
        # Show song confirmation
        if st.session_state.get("show_confirmation", False) and st.session_state.get("found_song"):
            song = st.session_state.found_song
            
            st.subheader(t["found_song"])
            
            # Display song info
            if song.get("image_url"):
                st.image(song["image_url"], width=200)
            
            st.markdown(f"**{song['title']}**")
            st.markdown(f"{t['by_artist']} {song['artist']}")
            st.markdown(f"{t['album']} {song['album']}")
            
            # Preview audio if available
            if song.get("preview_url"):
                st.audio(song["preview_url"])
            
            # Confirmation buttons
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                if st.button(t["confirm_yes"], use_container_width=True):
                    # Check for duplicates
                    if song_exists(db, song["title"], song["artist"]):
                        st.warning(t["already_exists"])
                    else:
                        # Add to database
                        if add_song_to_db(db, song):
                            st.success(t["song_added"])
                            
                            # Backup to Google Sheets
                            backup_to_sheets(gc, song)
                            
                            # Clear the form
                            st.session_state.show_confirmation = False
                            st.session_state.found_song = None
                            st.rerun()
                        else:
                            st.error(t["add_failed"])
            
            with col_no:
                if st.button(t["confirm_no"], use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.session_state.found_song = None
                    st.rerun()
    
    with col2:
        st.subheader(t["current_playlist"])
        
        # Get all songs
        songs = get_all_songs(db)
        
        if songs:
            # Display count
            st.markdown(f"**{len(songs)} {t['songs_count']}**")
            
            # Create playlist table
            playlist_data = []
            for song in songs:
                playlist_data.append({
                    t["title_col"]: song["title"],
                    t["artist_col"]: song["artist"],
                    t["album_col"]: song["album"],
                    t["spotify_col"]: f"[{t['listen']}]({song['spotify_url']})",
                    t["added"]: datetime.fromisoformat(song["added_at"]).strftime("%m/%d %H:%M")
                })
            
            df = pd.DataFrame(playlist_data)
            
            # Display table
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Download option
            st.subheader(t["export_playlist"])
            csv_data = pd.DataFrame([{
                "Title": song["title"],
                "Artist": song["artist"],
                "Album": song["album"],
                "Spotify URL": song["spotify_url"],
                "Added At": song["added_at"]
            } for song in songs])
            
            csv_string = csv_data.to_csv(index=False)
            st.download_button(
                label=t["download_csv"],
                data=csv_string,
                file_name=f"mums_disco_playlist_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info(t["no_songs_yet"])
    
    # Footer
    st.markdown("---")
    st.markdown(t["footer"])

# Initialize session state
if "show_confirmation" not in st.session_state:
    st.session_state.show_confirmation = False
if "found_song" not in st.session_state:
    st.session_state.found_song = None

if __name__ == "__main__":
    main()