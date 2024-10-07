import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import ttk
import os

cache_path = "your_cache_path"
try:
    os.remove(cache_path)
    print("Cache Cleared")
except FileNotFoundError:
    print("Cache file not found.")

client_id = '6f61d716331b4159b2a347c9d43eede7'
client_secret = 'f6571b3094ad4cd2bb6978a4df8bcd75'
# Your new redirect URI
redirect_uri = 'http://localhost:8080/callback'

sp_oauth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope='user-library-read user-top-read user-read-email playlist-read-private playlist-modify-public playlist-modify-private',
                        cache_path="your_cache_path")
sp = spotipy.Spotify(auth_manager=sp_oauth)

# Fetch user profile
user_profile = sp.current_user()
display_name = user_profile.get('display_name', 'N/A')
email = user_profile.get('email', 'N/A')
followers = user_profile.get('followers', {}).get('total', 'N/A')

print(f"Display Name: {display_name}")
print(f"Email: {email}")
print(f"Followers Count: {followers}")


def get_top_tracks():
    top_tracks = sp.current_user_top_tracks(limit=20)
    return [(track['name'], ', '.join(artist['name'] for artist in track['artists'])) for track in top_tracks['items']]

def get_top_artists():
    top_artists = sp.current_user_top_artists(limit=20)
    return [(artist['name'], artist['genres']) for artist in top_artists['items']]

def display_top_tracks():
    top_tracks = get_top_tracks()
    for idx, (track_name, artists) in enumerate(top_tracks, start=1):
        tracks_tree.insert("", "end", values=(idx, track_name, artists))

def display_top_artists():
    top_artists = get_top_artists()
    for idx, (artist_name, genres) in enumerate(top_artists, start=1):
        artists_tree.insert("", "end", values=(idx, artist_name, ', '.join(genres)))

# Create the main window
root = tk.Tk()
root.title("Top 10 Spotify Tracks and Artists")

# Create a notebook to hold tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create frames for each tab
tracks_frame = ttk.Frame(notebook)
artists_frame = ttk.Frame(notebook)

# Add frames to notebook
notebook.add(tracks_frame, text="Top Tracks")
notebook.add(artists_frame, text="Top Artists")

# Create treeview for top tracks
tracks_tree = ttk.Treeview(tracks_frame, columns=("Rank", "Track Name", "Artists"), show="headings")
tracks_tree.heading("Rank", text="Rank")
tracks_tree.heading("Track Name", text="Track Name")
tracks_tree.heading("Artists", text="Artists")
tracks_tree.pack(fill=tk.BOTH, expand=True)

# Create treeview for top artists
artists_tree = ttk.Treeview(artists_frame, columns=("Rank", "Artist Name", "Genres"), show="headings")
artists_tree.heading("Rank", text="Rank")
artists_tree.heading("Artist Name", text="Artist Name")
artists_tree.heading("Genres", text="Genres")
artists_tree.pack(fill=tk.BOTH, expand=True)

# Fetch and display the top tracks and artists
display_top_tracks()
display_top_artists()

# Run the application
root.mainloop()
