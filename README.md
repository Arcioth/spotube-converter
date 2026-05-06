# Spotube Converter

Spotube Converter is a robust CLI tool for migrating your Spotify playlists (exported as CSV) directly to YouTube Music. It fully bypasses Google's official API quota limits by leveraging `ytmusicapi` to simulate user actions, meaning you can migrate playlists of any size (even thousands of tracks) in a single run.

## Features

- **No Quota Limits:** Bypasses standard YouTube Data API quotas.
- **Smart Search:** Filters specifically for "songs" to get official high-quality audio tracks instead of random videos.
- **Batch Processing:** Safely uploads tracks in batches to prevent data loss if the script gets interrupted.
- **Rate Limiting:** Automatically includes small delays to ensure YouTube doesn't temporarily block your requests.
- **Easy Setup:** Uses a simple CLI interface for both authentication and migration.

## Prerequisites

- Arch Linux (or any Linux distribution)
- Python 3.9+
- `pipx` (Recommended for isolated global CLI installation)

## Installation

### Method 1: pipx (Recommended)
This installs `spotube-converter` globally on your system in an isolated environment.

```bash
git clone <your-repo-url>
cd spotube-converter
./install.sh
```

### Method 2: Arch Native Package (makepkg)
Build an official `.pkg.tar.zst` pacman package. Requires `python-pandas` and `python` installed natively.

```bash
git clone <your-repo-url>
cd spotube-converter
./build-pkg.sh
```

## Usage

### 1. Authenticate with YouTube Music
Before creating playlists, you need to securely authenticate your YouTube account. Run the following command and follow the instructions provided in the terminal to log in via your browser.

```bash
spotube-converter auth
```
*(Your credentials will be safely stored in `~/.config/spotube-converter/oauth.json`)*

### 2. Migrate a Playlist
Once authenticated, you can migrate any Spotify CSV playlist file (ensure it has `name` and `artist` columns, which Spotube usually exports by default).

```bash
spotube-converter migrate /path/to/your/spotify_playlist.csv
```

You can optionally specify a title directly:
```bash
spotube-converter migrate /path/to/your/spotify_playlist.csv -t "My Migrated Playlist"
```

## How It Works
The script will sequentially parse your CSV, build a query (e.g., "Song Name Artist Name"), and search YouTube Music. It automatically selects the first result from the "songs" filter and queues it to your newly created playlist in batches of 50.

## License
MIT
