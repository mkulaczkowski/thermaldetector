// logging.js

const debugPanel = document.getElementById('debug-panel');
const logToggleBtn = document.getElementById('log-toggle');
const logHideBtn = document.getElementById('log-hide');
let logPanelOpen = false;

function logMessage(msg) {
    const entry = document.createElement('div');
    entry.textContent = msg;
    debugPanel.appendChild(entry);
    debugPanel.scrollTop = debugPanel.scrollHeight;
}

logToggleBtn.addEventListener('click', () => {
    if (!logPanelOpen) {
        logPanelOpen = true;
        debugPanel.style.display = 'block';
        logMessage("Log panel -> OPEN");
    }
});

logHideBtn.addEventListener('click', () => {
    logPanelOpen = false;
    debugPanel.style.display = 'none';
    logMessage("Log panel -> CLOSED");
});
