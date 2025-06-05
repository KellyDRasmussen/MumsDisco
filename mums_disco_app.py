import streamlit as st
import requests
import base64
import json
import gspread
from tinydb import TinyDB, Query
from datetime import datetime
import pandas as pd
import time
from typing import Optional, Dict, List

# Page configuration
st.set_page_config(
    page_title="🎵 Mum's Disco",
    page_icon="🎵",
    layout="wide"
)

# Initialize database
@st.cache_resource
def init_database():
    return TinyDB('playlist.json')

# Initialize Google Sheets connection
@st.cache_resource
def init_gspread():
    try:
        st.info("🔗 Initializing Google Sheets connection...")
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
        st.success("✅ Google Sheets connection established!")
        return gc
    except Exception as e:
        st.error(f"❌ Failed to initialize Google Sheets: {e}")
        st.error(f"Error type: {type(e).__name__}")
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
        st.error(f"Failed to get Spotify token: {response.status_code}")
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
    st.info("🔍 Inside backup function...")
    
    if not gc:
        st.warning("Google Sheets connection not initialized")
        return False
        
    try:
        st.info("📋 Attempting to find/create sheet...")
        
        # Try to open existing sheet first
        sheet_name = "Mums Disco Playlist"
        spreadsheet = None
        sheet = None
        
        try:
            st.info(f"🔎 Looking for sheet: '{sheet_name}'")
            spreadsheet = gc.open(sheet_name)
            sheet = spreadsheet.sheet1
            st.success(f"✅ Found existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            st.info(f"📝 Sheet not found, creating: {sheet_name}")
            spreadsheet = gc.create(sheet_name)
            sheet = spreadsheet.sheet1
            # Add headers
            st.info("📊 Adding column headers...")
            sheet.append_row(["Title", "Artist", "Album", "Spotify URL", "Added At"])
            st.success(f"✅ Created new sheet: {sheet_name}")
        except Exception as find_error:
            st.error(f"❌ Error finding/creating sheet: {find_error}")
            return False
        
        # Add the song data
        st.info("💾 Adding song to sheet...")
        row_data = [
            song_data["title"],
            song_data["artist"],
            song_data["album"],
            song_data["spotify_url"],
            song_data.get("added_at", datetime.now().isoformat())
        ]
        
        sheet.append_row(row_data)
        st.success("🎉 Successfully backed up to Google Sheets!")
        return True
        
    except Exception as e:
        st.error(f"💥 Backup failed: {str(e)}")
        st.error(f"🔧 Error type: {type(e).__name__}")
        return False

# Main app
def main():
    # Initialize resources
    db = init_database()
    gc = init_gspread()
    
    # Header
    st.title("🎵 Mum's Disco")
    st.markdown("### Crowdsource the perfect playlist! 🕺💃")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add a Song")
        
        # Song input form
        with st.form("add_song_form"):
            song_input = st.text_input(
                "Song Name",
                placeholder="Enter a song title...",
                help="Type the name of a song you'd like to add to the playlist"
            )
            
            search_button = st.form_submit_button("🔍 Search", use_container_width=True)
        
        # Handle song search
        if search_button and song_input.strip():
            with st.spinner("Searching Spotify..."):
                token = get_spotify_token()
                if token:
                    song_data = search_spotify_song(song_input.strip(), token)
                    
                    if song_data:
                        st.session_state.found_song = song_data
                        st.session_state.show_confirmation = True
                    else:
                        st.error("No songs found. Try a different search term.")
                else:
                    st.error("Unable to connect to Spotify. Please try again later.")
        
        # Show song confirmation
        if st.session_state.get("show_confirmation", False) and st.session_state.get("found_song"):
            song = st.session_state.found_song
            
            st.subheader("Found Song:")
            
            # Display song info
            if song.get("image_url"):
                st.image(song["image_url"], width=200)
            
            st.markdown(f"**{song['title']}**")
            st.markdown(f"by {song['artist']}")
            st.markdown(f"Album: {song['album']}")
            
            # Preview audio if available
            if song.get("preview_url"):
                st.audio(song["preview_url"])
            
            # Confirmation buttons
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                if st.button("✅ Yes, add this!", use_container_width=True):
                    st.info("🔄 Processing your song...")
                    
                    # Check for duplicates
                    if song_exists(db, song["title"], song["artist"]):
                        st.warning("This song is already in the playlist!")
                    else:
                        st.info("📝 Adding song to local database...")
                        # Add to database
                        if add_song_to_db(db, song):
                            st.success("Song added to playlist! 🎉")
                            
                            st.info("🔗 Starting Google Sheets backup...")
                            
                            # Debug the gc object
                            if gc is None:
                                st.error("❌ Google Sheets connection is None - check your secrets!")
                            else:
                                st.info(f"✅ Google Sheets connection exists: {type(gc)}")
                                # Try the backup
                                backup_to_sheets(gc, song)
                            
                            # Add a small delay to see messages
                            time.sleep(3)
                            
                            # Clear the form
                            st.session_state.show_confirmation = False
                            st.session_state.found_song = None
                            st.rerun()
                        else:
                            st.error("Failed to add song to playlist.")
            
            with col_no:
                if st.button("❌ No, search again", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.session_state.found_song = None
                    st.rerun()
    
    with col2:
        st.subheader("Current Playlist")
        
        # Get all songs
        songs = get_all_songs(db)
        
        if songs:
            # Display count
            st.markdown(f"**{len(songs)} songs in the playlist**")
            
            # Create playlist table
            playlist_data = []
            for song in songs:
                playlist_data.append({
                    "Title": song["title"],
                    "Artist": song["artist"],
                    "Album": song["album"],
                    "Spotify": f"[Listen]({song['spotify_url']})",
                    "Added": datetime.fromisoformat(song["added_at"]).strftime("%m/%d %H:%M")
                })
            
            df = pd.DataFrame(playlist_data)
            
            # Display table
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Download option
            st.subheader("Export Playlist")
            csv_data = pd.DataFrame([{
                "Title": song["title"],
                "Artist": song["artist"],
                "Album": song["album"],
                "Spotify URL": song["spotify_url"],
                "Added At": song["added_at"]
            } for song in songs])
            
            csv_string = csv_data.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_string,
                file_name=f"mums_disco_playlist_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        else:
            st.info("No songs in the playlist yet. Be the first to add one! 🎵")
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ for Mum's Disco | Powered by Spotify")

# Initialize session state
if "show_confirmation" not in st.session_state:
    st.session_state.show_confirmation = False
if "found_song" not in st.session_state:
    st.session_state.found_song = None

if __name__ == "__main__":
    main()