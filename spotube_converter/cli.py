import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from ytmusicapi import YTMusic

CONFIG_DIR = Path.home() / ".config" / "spotube-converter"
OAUTH_FILE = CONFIG_DIR / "oauth.json"

def setup_auth():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if OAUTH_FILE.exists():
        print(f"Already authenticated. Credentials found at {OAUTH_FILE}")
        return
    
    print("================================================================")
    print("                YouTube Music API Authentication                ")
    print("================================================================")
    print("To authenticate, you need to create a Google Cloud Project with")
    print("the YouTube Data API v3 enabled and generate OAuth credentials.")
    print("")
    print("1. Open the following link in your browser:")
    print("   https://console.cloud.google.com/apis/credentials/wizard?api=youtube.googleapis.com&previousPage=%252Fapis%252Fapi%252Fyoutube.googleapis.com%252Fmetrics")
    print("2. Select 'User data' and click 'Next'.")
    print("3. Fill in the App Information (names/emails can be anything, app icon is not needed) and click 'Save and Continue'.")
    print("4. Skip 'Scopes' by just clicking 'Save and Continue'.")
    print("5. In the 'Test users' step, click 'Add Users', type your Google email address, and click 'Save and Continue'.")
    print("6. In 'OAuth Client ID', select 'TVs and Limited Input devices' as Application type and click 'Create'.")
    print("7. Under 'Your Credentials', click 'Download' to save the JSON file to your computer.")
    print("================================================================\n")
    
    json_path = input("Enter the full path to the downloaded JSON file (e.g. ~/Downloads/client_secret_...json): ").strip()
    
    json_path = os.path.expanduser(json_path)
    
    if not os.path.exists(json_path):
        print(f"Error: Could not find file at {json_path}")
        sys.exit(1)
        
    try:
        with open(json_path, 'r') as f:
            creds = json.load(f)
            
        client_id = creds.get('installed', {}).get('client_id') or creds.get('web', {}).get('client_id')
        client_secret = creds.get('installed', {}).get('client_secret') or creds.get('web', {}).get('client_secret')
        
        if not client_id or not client_secret:
            print("Error: The provided JSON file does not contain a valid client_id or client_secret.")
            sys.exit(1)
            
        print("\nStarting authentication process...")
        import subprocess
        ytmusicapi_bin = os.path.join(os.path.dirname(sys.executable), "ytmusicapi")
        subprocess.run([ytmusicapi_bin, "oauth", "--file", str(OAUTH_FILE), "--client-id", client_id, "--client-secret", client_secret], check=True)
        print(f"\nAuthentication successful. Credentials saved to {OAUTH_FILE}")
    except json.JSONDecodeError:
        print("Error: The provided file is not a valid JSON file.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nAuthentication failed. ytmusicapi exited with code {e.returncode}")
        print("If you see 'OAuth client failure', please ensure that the 'YouTube Data API v3' is enabled for your project.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)

def migrate_playlist(csv_file, title):
    if not os.path.exists(csv_file):
        print(f"Error: Could not find CSV file at {csv_file}")
        sys.exit(1)
        
    if not OAUTH_FILE.exists():
        print("Error: Not authenticated. Please run 'spotube-converter auth' first.")
        sys.exit(1)

    print("Authenticating with YouTube Music...")
    yt = YTMusic(str(OAUTH_FILE))

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
