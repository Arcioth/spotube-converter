# YouTube Music Playlist Creator

A secure, browser-based extension to directly migrate and convert your Spotify CSV playlists into YouTube Music playlists.

## Why a Browser Extension?
Due to recent changes in Google's API, the standard OAuth flow for creating YouTube Music playlists is severely limited and often results in unfixable `400 Bad Request` or `401 Unauthorized` errors for third-party scripts.

By running as a browser extension, this tool leverages your existing YouTube Music session securely and locally, acting exactly as if you were clicking the buttons yourself. This bypasses API quotas, broken OAuth flows, and external server dependencies entirely.

## Security & Privacy (How it Works)

This extension is built with extreme privacy in mind. **No data ever leaves your computer.**

1. **Local Execution Only:** The extension contains no telemetry, no tracking, and connects to no external servers. 
2. **Key Security:** To create a playlist, YouTube Music requires an internal token known as the `INNERTUBE_API_KEY` along with a cryptographic hash of your `SAPISID` cookie. 
   - The extension securely requests these variables directly from your active `music.youtube.com` tab's memory (using the `window.ytcfg` object).
   - The `SAPISIDHASH` cryptography is computed entirely on your local machine using standard Web Crypto APIs.
   - The keys are immediately used to construct the playlist request directly to YouTube's official endpoints (`/youtubei/v1/...`). They are never saved, transmitted, or logged anywhere else.
3. **Permissions Explained:**
   - `tabs`: Allows the extension to check if YouTube Music is already open, and if not, quietly open a background tab so it can perform the migration.
   - `scripting` & `*://music.youtube.com/*`: Required to safely inject the local migration script into the YouTube Music tab context so it can access the necessary `ytcfg` variables.
   - `storage`: Used purely to save your local UI preferences (like the consent agreement) and keep a persistent log of your migration progress in case you accidentally close the popup.

## Installation

Since this is a custom local tool, you will load it into your browser manually:

**For Chrome, Edge, Brave, and other Chromium browsers:**
1. Open your browser and navigate to the extensions page: `chrome://extensions/`
2. Turn on **Developer mode** (usually a toggle switch in the top right corner).
3. Click the **Load unpacked** button in the top left.
4. Select the `spotube-extension/` folder on your computer.

**For Firefox:**
1. Navigate to `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on...**
3. Select the `manifest.json` file inside the `spotube-extension/` folder.

## Usage

1. Open your downloaded `spotify_playlist.csv` (or any CSV with at least `Track` and `Artist` columns) in a text editor (Notepad, TextEdit, etc.) and copy all the text.
2. Click the **YouTube Music Playlist Creator** extension icon in your browser toolbar.
3. If it's your first time, read and accept the security consent screen.
4. Enter a name for your new playlist.
5. Paste your copied CSV text into the text area.
6. Click **Create Playlist & Migrate**!

The extension will handle the rest, intelligently batching your songs and respecting YouTube's rate limits, logging its progress directly in the interface.
