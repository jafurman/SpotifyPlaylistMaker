import urllib3
import ssl
import certifi
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from requests import post
import base64
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os

cache_path = "your_cache_path"
try:
    os.remove(cache_path)
    print("Cache Cleared")
except FileNotFoundError:
    print("Cache file not found.")

client_id = '6f61d716331b4159b2a347c9d43eede7'
client_secret = 'nicetry'
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


def getToken():
    authString = client_id + ":" + client_secret
    authBytes = authString.encode("utf-8")
    authBase64 = str(base64.b64encode(authBytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + authBase64,
        "Content_Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data, verify=False)
    jsonResult = json.loads(result.content)
    token = jsonResult["access_token"]
    return token


def getAuthHeader(token):
    return {"Authorization": "Bearer " + token}


def get_spotipy_client():
    # Initialize Spotipy client with OAuth
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri='http://localhost:8080/callback',
                                                   scope='user-library-read user-top-read user-read-email playlist-read-private playlist-modify-public playlist-modify-private'))
    return sp


def checkTopArtists(amt):
    top_artists = sp.current_user_top_artists(limit=amt)
    print("\nYour Top Artists:")
    for idx, artist in enumerate(top_artists['items']):
        print(f"{idx + 1}. {artist['name']}")


def checkTopSongs(amt):
    top_tracks = sp.current_user_top_tracks(limit=amt)
    print("\nYour Top Tracks:")
    for idx, track in enumerate(top_tracks['items']):
        print(f"{idx + 1}. {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}")


def checkLikedSongs():
    numOfSongsToDisplay = input("How many liked songs would you like to display?: ")
    numOfSongsToDisplay = int(numOfSongsToDisplay)

    limit = 25
    offset = 0

    counter = 0
    while True:
        if counter >= numOfSongsToDisplay:
            break
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)

        if not liked_tracks['items']:
            break
        for idx, track in enumerate(liked_tracks['items']):
            counter += 1
            print(
                f"{idx + offset + 1}. {track['track']['name']} - {', '.join(artist['name'] for artist in track['track']['artists'])}")

        offset += limit


def checkLikedSongsPopularity():
    limit = 25
    offset = 0
    counter = 0
    popScores = []
    while True:
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
        if not liked_tracks['items']:
            break
        for idx, track in enumerate(liked_tracks['items']):
            counter += 1
            first_artist_name = track['track']['artists'][0]['name']
            artist_info = sp.search(q=f'artist:{first_artist_name}', type='artist')
            if artist_info['artists']['items']:
                artist_popularity = artist_info['artists']['items'][0]['popularity']
                popScores.append(int(artist_popularity))
                average = int(sum(popScores) / len(popScores))
                print(f"{average}: current calculated score average with {first_artist_name} : {artist_popularity} on "
                      f"song #{counter}.")
        offset += limit
    average = int(sum(popScores) / len(popScores))
    print(f"Your final average liked songs aritst popularity score is: {average}")
    if average > 80:
        print("Yikes, that's high...")


def removePopularityLevelFromLikedSongs(popLevel):
    if int(popLevel) <= 85:
        print("Bro you aint ready for that...")
        exit()
    limit = 25
    offset = 0
    counter = 0
    while True:
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
        if not liked_tracks['items']:
            break
        for idx, track in enumerate(liked_tracks['items']):
            counter += 1
            first_artist_name = track['track']['artists'][0]['name']
            artist_info = sp.search(q=f'artist:{first_artist_name}', type='artist')
            if artist_info['artists']['items']:
                artist_popularity = artist_info['artists']['items'][0]['popularity']
                print(
                    f"{idx + offset + 1}. {track['track']['name']} - {first_artist_name} (Popularity Score: {artist_popularity})"
                )
                if artist_popularity >= int(popLevel):
                    track_id = track['track']['id']
                    sp.current_user_saved_tracks_delete(tracks=[track_id])
                    print("\033[91mELIMINATED {} from liked songs because they're too popular for you.\033[0m".format(
                        track['track']['name']))
            else:
                print(
                    f"{idx + offset + 1}. {track['track']['name']} - {first_artist_name} (Popularity: N/A)"
                )

        offset += limit


def checkLikedSongsGenres():
    # Input from the user: Number of liked songs to display
    num_of_songs_to_display = int(input("How many liked songs would you like to display?: "))

    limit = 25
    offset = 0

    song_names = []
    genres_list = []

    counter = 0

    while counter < num_of_songs_to_display:
        liked_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)

        if not liked_tracks['items']:
            break
        for track in liked_tracks['items']:
            counter += 1
            song_name = track['track']['name']

            artists = track['track']['artists']
            artist_genres = []
            for artist in artists:
                artist_info = sp.artist(artist['id'])
                artist_genres.extend(artist_info['genres'])

            if not artist_genres:
                artist_genres = ['No genres found']

            song_names.append(song_name)
            genres_list.append(artist_genres)

            if counter >= num_of_songs_to_display:
                break

        offset += limit

    # Cluster the genres
    p1, p2, p3, p4 = cluster_genres(genres_list, song_names)

    deletePlaylist("Generated Playlist One")
    deletePlaylist("Generated Playlist Two")
    deletePlaylist("Generated Playlist Three")
    deletePlaylist("Misc")
    createPlaylist(p1, "Generated Playlist One")
    createPlaylist(p2, "Generated Playlist Two")
    createPlaylist(p3, "Generated Playlist Three")
    createPlaylist(p4, "Misc")

    # Print songs associated with each cluster
    print(p1)
    for song in p1:
        print(f"- {song}")

    print(p2)
    for song in p2:
        print(f"- {song}")

    print(p3)
    for song in p3:
        print(f"- {song}")

    print(p4)
    for song in p4:
        print(f"- {song}")

    # Plot the pie chart
    plot_genre_pie_chart(genres_list)

    return None


def plot_genre_pie_chart(genres_list):
    # Flatten the list of genres
    flat_genres = [genre for sublist in genres_list for genre in sublist]
    genre_counts = pd.Series(flat_genres).value_counts()

    # Sort the genre counts in descending order
    genre_counts = genre_counts.sort_values(ascending=False)

    # Grouping smaller percentages into "Other" category
    threshold = 2  # Adjust this threshold as needed
    other_genres = genre_counts[genre_counts < threshold]
    genre_counts = genre_counts[genre_counts >= threshold]
    genre_counts['Other'] = other_genres.sum()

    # Define a color palette for the genres
    colors = plt.cm.tab20.colors  # You can choose any other colormap

    # Plotting the pie chart
    plt.figure(figsize=(10, 8))
    explode = [0.1 if i == 0 else 0 for i in range(len(genre_counts))]  # Explode the first slice
    genre_counts.plot.pie(autopct='%1.1f%%', colors=colors, explode=explode)

    # Add title and labels
    plt.title('Distribution of Genres in Liked Songs')
    plt.ylabel('')

    # Add legend outside the pie chart to the left
    legend_labels = [f"{genre} ({count})" for genre, count in zip(genre_counts.index, genre_counts.values)]
    plt.legend(legend_labels, loc='upper left', bbox_to_anchor=(0.95, 0.5), fontsize='small')

    plt.show()

    return None


def cluster_genres(genres, song_names):
    # Flatten the list of lists into a single list
    flattened_genres = [' '.join(sublist) for sublist in genres]

    # Create TF-IDF vectorizer
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(flattened_genres)

    # Perform K-means clustering
    num_clusters = 4
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(tfidf_matrix)

    # Initialize four separate lists for each cluster
    p1, p2, p3, p4 = [], [], [], []

    # Group songs by cluster
    for song_name, label in zip(song_names, cluster_labels):
        if label == 0:
            p1.append(song_name)
        elif label == 1:
            p2.append(song_name)
        elif label == 2:
            p3.append(song_name)
        elif label == 3:
            p4.append(song_name)

    return p1, p2, p3, p4


def createPlaylist(songs, playlist_name):
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False)
    playlist_id = playlist['id']

    batch_size = 100
    for i in range(0, len(songs), batch_size):
        batch = songs[i:i + batch_size]
        song_uris = []
        for song in batch:
            track_results = sp.search(q='track:' + song, type='track')
            if track_results['tracks']['items']:
                track_uri = track_results['tracks']['items'][0]['uri']
                song_uris.append(track_uri)
        sp.playlist_add_items(playlist_id, song_uris)

    return f"Playlist '{playlist_name}' created successfully with {len(songs)} songs."


def deletePlaylist(playlist_name):
    user_id = sp.current_user()['id']
    playlists = sp.user_playlists(user=user_id)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            sp.user_playlist_unfollow(user=user_id, playlist_id=playlist_id)
            print(f"Playlist '{playlist_name}' deleted successfully.")
            break
    else:
        print(f"Playlist '{playlist_name}' not found.")


# _______________________ MAIN METHOD ___________________________


'''
sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                        scope='user-library-read user-top-read user-read-email playlist-read-private playlist-modify-public playlist-modify-private', requests_session=False)

sp = spotipy.Spotify(auth_manager=sp_oauth)

user_profile = sp.current_user()
display_name = user_profile.get('display_name', 'N/A')
email = user_profile.get('email', 'N/A')
followers = user_profile.get('followers', {}).get('total', 'N/A')

print(f"Display Name: {display_name}")
print(f"Email: {email}")
print(f"Followers Count: {followers}")

'''

while True:
    print()
    # Avaliable Options
    print(f"[1]. See 'x' top artists (max 50)")
    print(f"[2]. See 'x' top songs (max 50)")
    print(f"[3]. See all liked songs")
    print(f"[4]. Display and average 'Popularity Score' in Liked Songs")
    print(f"[5]. Remove popular artist's songs from Liked Songs given 'x' popularity score")
    print(f"[6]. Check liked songs plus genre")
    print(f"[Anything else]. Exit")

    answer = int(input("\nWhat would you like to do?: "))

    if answer == 1:
        amount = int(input("How many artists do you want to see?: "))
        checkTopArtists(amount)
    elif answer == 2:
        amount = int(input("How many songs do you want to see?: "))
        checkTopSongs(amount)
    elif answer == 3:
        checkLikedSongs()
    elif answer == 4:
        checkLikedSongsPopularity()
    elif answer == 5:
        popRemoveLevel = input("What is the popularity score you would like to remove?: ")
        removePopularityLevelFromLikedSongs(popRemoveLevel)
    elif answer == 6:
        pri = checkLikedSongsGenres()
        print(pri)
    else:
        exit()
