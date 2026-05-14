document.addEventListener('SpotubeLog', (e) => {
    chrome.runtime.sendMessage({ type: 'log', text: e.detail });
});