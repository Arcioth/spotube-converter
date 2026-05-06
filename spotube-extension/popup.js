function log(msg, isError = false) {
    const logDiv = document.getElementById('log');
    const span = document.createElement('span');
    if (isError) span.className = 'error';
    span.textContent = msg + '\n';
    logDiv.appendChild(span);
    logDiv.scrollTop = logDiv.scrollHeight;
}

chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'log') {
        log(message.text, message.text.toLowerCase().includes('error'));
    }
});

document.getElementById('migrateBtn').addEventListener('click', async () => {
    const csvData = document.getElementById('csvData').value.trim();
    let titleInput = document.getElementById('playlistTitle').value.trim();
    if (!titleInput) titleInput = "Migrated Spotify Playlist";

    if (!csvData) {
        log("Please paste your CSV data first.", true);
        return;
    }

    document.getElementById('migrateBtn').disabled = true;
    document.getElementById('log').innerHTML = ''; // clear

    const text = csvData;
    
    // Basic CSV parsing
    const lines = text.split('\n');
    if (lines.length < 2) {
        log("CSV file seems empty.", true);
        document.getElementById('migrateBtn').disabled = false;
        return;
    }

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));
    
    let nameIdx = headers.findIndex(h => h.includes('name') || h.includes('track') || h.includes('title'));
    let artistIdx = headers.findIndex(h => h.includes('artist'));
    
    if (nameIdx === -1 || artistIdx === -1) {
        log("Could not find 'name' and 'artist' columns in CSV. Found: " + headers.join(', '), true);
        document.getElementById('migrateBtn').disabled = false;
        return;
    }

    const songs = [];
    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        
        let row = [];
        let inQuotes = false;
        let currentWord = '';
        for (let char of lines[i]) {
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                row.push(currentWord);
                currentWord = '';
            } else {
                currentWord += char;
            }
        }
        row.push(currentWord);
        
        if (row.length > Math.max(nameIdx, artistIdx)) {
            const songName = row[nameIdx].replace(/"/g, '').trim();
            const artistName = row[artistIdx].replace(/"/g, '').trim();
            if (songName) {
                songs.push(`${songName} ${artistName}`.trim());
            }
        }
    }

    log(`Successfully parsed ${songs.length} songs from CSV.`);
    log(`Connecting to YouTube Music...`);

    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (!tabs || !tabs[0]) {
            log("Could not find active tab.", true);
            document.getElementById('migrateBtn').disabled = false;
            return;
        }
        
        const url = tabs[0].url;
        if (!url.includes('music.youtube.com')) {
            log("ERROR: You must be on music.youtube.com to run this.", true);
            log("Please open a new tab to music.youtube.com, click the extension icon again, and retry.");
            document.getElementById('migrateBtn').disabled = false;
            return;
        }

        chrome.scripting.executeScript({
            target: {tabId: tabs[0].id},
            world: "MAIN",
            func: runMigration,
            args: [songs, titleInput]
        }).catch(err => {
            log(`Script injection failed: ${err.message}`, true);
            document.getElementById('migrateBtn').disabled = false;
        });
    });
});

// This function runs entirely within the youtube page context!
async function runMigration(songs, playlistTitle) {
    const sendLog = (text) => {
        document.dispatchEvent(new CustomEvent('SpotubeLog', { detail: text }));
    };

    try {
        if (!window.ytcfg) {
            sendLog("Error: window.ytcfg not found. Make sure the page is fully loaded and you are logged in.");
            return;
        }

        const apiKey = window.ytcfg.get('INNERTUBE_API_KEY');
        const context = window.ytcfg.get('INNERTUBE_CONTEXT');

        if (!apiKey || !context) {
            sendLog("Error: API Key or Context not found. Are you logged in?");
            return;
        }

        async function apiPost(endpoint, payload) {
            payload.context = context;
            const res = await fetch(`/youtubei/v1/${endpoint}?key=${apiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
        }

        sendLog(`Creating playlist: "${playlistTitle}"...`);
        const createRes = await apiPost('playlist/create', {
            title: playlistTitle,
            description: "Migrated via Spotube Browser Extension",
            privacyStatus: "PRIVATE"
        });

        const playlistId = createRes.playlistId;
        if (!playlistId) {
            sendLog(`Error creating playlist: ${JSON.stringify(createRes)}`);
            return;
        }
        sendLog(`Playlist created! ID: ${playlistId}`);

        let videoIds = [];
        
        for (let i = 0; i < songs.length; i++) {
            const query = songs[i];
            sendLog(`[${i+1}/${songs.length}] Searching: ${query}`);
            
            try {
                // Using the specific params for "Songs" filter in YTM
                const searchRes = await apiPost('search', {
                    query: query,
                    params: "EgWKAQIIAWoMEA4QChADEAQQCRAF"
                });
                
                let foundId = null;
                const jsonStr = JSON.stringify(searchRes);
                // Look for the first videoId
                const match = jsonStr.match(/"videoId":"([a-zA-Z0-9_-]{11})"/);
                if (match && match[1]) {
                    foundId = match[1];
                }

                if (foundId) {
                    videoIds.push(foundId);
                } else {
                    sendLog(` -> Not found`);
                }
            } catch (err) {
                sendLog(` -> Search error: ${err.message}`);
            }

            // Sleep 1 second to avoid rate limits
            await new Promise(r => setTimeout(r, 1000));

            // Batch add every 50 songs
            if (videoIds.length >= 50) {
                sendLog(`Pushing batch of 50 songs to playlist...`);
                await apiPost('browse/edit_playlist', {
                    playlistId: playlistId,
                    actions: videoIds.map(id => ({
                        action: "ACTION_ADD_VIDEO",
                        addedVideoId: id
                    }))
                });
                videoIds = [];
            }
        }

        // Final batch
        if (videoIds.length > 0) {
            sendLog(`Pushing final batch of ${videoIds.length} songs to playlist...`);
            await apiPost('browse/edit_playlist', {
                playlistId: playlistId,
                actions: videoIds.map(id => ({
                    action: "ACTION_ADD_VIDEO",
                    addedVideoId: id
                }))
            });
        }

        sendLog("\nMigration complete! You can find the playlist in your YouTube Music library.");

    } catch (e) {
        sendLog(`Fatal Error: ${e.message}`);
    }
}
