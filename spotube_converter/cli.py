import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from ytmusicapi import YTMusic

CONFIG_DIR = Path.home() / ".config" / "spotube-converter"
AUTH_FILE = CONFIG_DIR / "browser_auth.json"

def setup_auth():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if AUTH_FILE.exists():
        print(f"Already authenticated. Credentials found at {AUTH_FILE}")
        print("If you want to re-authenticate, delete that file and run this command again.")
        return
    
    print("================================================================")
    print("                YouTube Music API Authentication                ")
    print("================================================================")
    print("Due to recent Google API changes, OAuth is currently broken for")
    print("creating playlists (HTTP 400 errors). We must use Browser Auth.")
    print("")
    print("Please follow these exact steps carefully:")
    print("1. Open https://music.youtube.com in Firefox or Chrome.")
    print("2. Make sure you are logged into your account.")
    print("3. Press F12 to open Developer Tools, and go to the 'Network' tab.")
    print("4. Refresh the page (F5).")
    print("5. In the Network tab, search for 'browse' or 'next' and click on a request.")
    print("6. Scroll down to 'Request Headers'.")
    print("7. Find the header named 'cookie' or 'Cookie'.")
    print("8. Right-click the 'cookie' value and copy it entirely.")
    print("================================================================\n")
    
    print("Paste your cookie string below and press ENTER:")
    cookie_string = input("Cookie: ").strip()
    
    if not cookie_string:
        print("Error: No cookie provided.")
        sys.exit(1)
        
    try:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "cookie": cookie_string,
            "x-goog-authuser": "0",
            "x-origin": "https://music.youtube.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        with open(AUTH_FILE, "w") as f:
            json.dump(headers, f, indent=4)
        print(f"\nAuthentication successful. Credentials saved to {AUTH_FILE}")
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)

def migrate_playlist(csv_file, title):
    if not os.path.exists(csv_file):
        print(f"Error: Could not find CSV file at {csv_file}")
        sys.exit(1)
        
    if not AUTH_FILE.exists():
        print("Error: Not authenticated. Please run 'spotube-converter auth' first.")
        sys.exit(1)

    print("Authenticating with YouTube Music...")
    yt = YTMusic(str(AUTH_FILE))

    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} songs from CSV.")

    playlist_title = title or input("Enter a title for the new YouTube playlist [Migrated Spotify Playlist]: ") or "Migrated Spotify Playlist"
    
    print("Creating playlist...")
    playlist_id = yt.create_playlist(
        title=playlist_title, 
        description='Automated migration from Spotify CSV via spotube-converter'
    )
    print(f"Created Playlist '{playlist_title}'. ID: {playlist_id}")

    video_ids = []

    columns = [c.lower() for c in df.columns]
    
    name_col = next((c for c in df.columns if 'name' in c.lower() or 'track' in c.lower() or 'title' in c.lower()), None)
    artist_col = next((c for c in df.columns if 'artist' in c.lower()), None)
    
    if not name_col or not artist_col:
        print(f"Warning: Could not automatically detect 'name' or 'artist' columns. Found columns: {list(df.columns)}")
        name_col = input("Enter the exact name of the track/song column: ")
        artist_col = input("Enter the exact name of the artist column: ")

    print("\nStarting search and migration...")
    for index, row in df.iterrows():
        query = f"{row[name_col]} {row[artist_col]}"
        print(f"[{index + 1}/{len(df)}] Searching: {query}")
        
        try:
            results = yt.search(query, filter="songs", limit=1)
            
            if results:
                video_ids.append(results[0]['videoId'])
            else:
                print(f"  -> Could not find: {query}")
                
        except Exception as e:
            print(f"  -> Error searching for {query}: {e}")
            
        time.sleep(1) 
        
        if len(video_ids) >= 50:
            yt.add_playlist_items(playlist_id, video_ids)
            print("--- Pushed batch of 50 to YouTube ---")
            video_ids = []

    if video_ids:
        yt.add_playlist_items(playlist_id, video_ids)
        print("--- Pushed final batch to YouTube ---")

    print("\nMigration complete! Check your YouTube account.")

def main():
    parser = argparse.ArgumentParser(description="Convert Spotify CSV playlists to YouTube Music playlists.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Auth command
    subparsers.add_parser("auth", help="Authenticate with YouTube Music (Generates OAuth credentials)")

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate a CSV playlist")
    migrate_parser.add_argument("csv_file", help="Path to the Spotify CSV file")
    migrate_parser.add_argument("-t", "--title", help="Title for the new YouTube playlist", default="")

    args = parser.parse_args()

    if args.command == "auth":
        setup_auth()
    elif args.command == "migrate":
        migrate_playlist(args.csv_file, args.title)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
