const debugPanel = document.getElementById('debug-panel');
const debugContent = document.getElementById('debug-content');
const logToggleButton = document.getElementById('log-toggle');

/**
 * Appends a log entry to #debug-content and logs to console
 */
function logMessage(message) {
    console.log("[APP LOG] " + message);
    const p = document.createElement('p');
    p.textContent = message;
    debugContent.appendChild(p);

    // Auto-scroll to the newest log
    debugContent.scrollTop = debugContent.scrollHeight;
}

/**
 * Toggles the visibility of the debug panel
 */
function toggleLogPanel() {
    if (debugPanel.style.display === 'none') {
        debugPanel.style.display = 'block';
    } else {
        debugPanel.style.display = 'none';
    }
}

// Attach event to the "Log" button
logToggleButton.addEventListener('click', toggleLogPanel);
