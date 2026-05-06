import pandas as pd
import time
import sys
import os
from ytmusicapi import YTMusic

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <path_to_spotify_csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Error: Could not find CSV file at {csv_file}")
        sys.exit(1)
        
    if not os.path.exists('oauth.json'):
        print("Error: oauth.json not found. Please run 'ytmusicapi oauth' first to authenticate.")
        sys.exit(1)

    # 1. Authenticate using the oauth.json generated earlier
    print("Authenticating with YouTube Music...")
    yt = YTMusic('oauth.json')

    # 2. Load your specific CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} songs from CSV.")

    # 3. Create the new YouTube playlist
    playlist_title = input("Enter a title for the new YouTube playlist [Migrated Spotify Playlist]: ") or "Migrated Spotify Playlist"
    playlist_id = yt.create_playlist(
        title=playlist_title, 
        description='Automated migration from Spotify CSV'
    )
    print(f"Created Playlist. ID: {playlist_id}")

    video_ids = []

    # 4. Loop through the CSV, search, and queue the videos
    # Note: Assuming columns are named 'name' and 'artist' based on the chat. If they differ, we might need to adjust.
    # Let's do a quick check on columns
    columns = [c.lower() for c in df.columns]
    
    name_col = next((c for c in df.columns if 'name' in c.lower() or 'track' in c.lower() or 'title' in c.lower()), None)
    artist_col = next((c for c in df.columns if 'artist' in c.lower()), None)
    
    if not name_col or not artist_col:
        print(f"Warning: Could not automatically detect 'name' or 'artist' columns. Found columns: {list(df.columns)}")
        name_col = input("Enter the exact name of the track/song column: ")
        artist_col = input("Enter the exact name of the artist column: ")

    for index, row in df.iterrows():
        # Create a query like: "Instant Crush (feat. Julian Casablancas) Daft Punk"
        query = f"{row[name_col]} {row[artist_col]}"
        print(f"[{index + 1}/{len(df)}] Searching: {query}")
        
        try:
            # Search for the song (filter="songs" ensures we get official audio when possible)
            results = yt.search(query, filter="songs", limit=1)
            
            if results:
                video_ids.append(results[0]['videoId'])
            else:
                print(f"  -> Could not find: {query}")
                
        except Exception as e:
            print(f"  -> Error searching for {query}: {e}")
            
        # Sleep to avoid getting temporarily rate-limited by YouTube
        time.sleep(1) 
        
        # 5. Add to playlist in batches of 50 to ensure we don't lose progress if the script stops
        if len(video_ids) >= 50:
            yt.add_playlist_items(playlist_id, video_ids)
            print("--- Pushed batch of 50 to YouTube ---")
            video_ids = [] # Reset the batch

    # Push any remaining songs
    if video_ids:
        yt.add_playlist_items(playlist_id, video_ids)
        print("--- Pushed final batch to YouTube ---")

    print("Migration complete! Check your YouTube account.")

if __name__ == "__main__":
    main()
