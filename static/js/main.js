// main.js

// Global variables (shared across files)
let pc = null;
let pipPc = null;
let currentCamera = "PTZ Thermal Camera";
let cameraOn = false;
let visibleLightOn = false;
let irLightOn = false;
let scanning = false;
let pipOn = false;
let lowLightMode = false;
let hasStopped = false;
let locationRequested = false;

const deadzone = 0.3;
const baseSpeed = 1.0;
let lastPan = 0, lastTilt = 0, lastSpeed = 0;
let lastEmitTime = 0;
const emitInterval = 500;

// DOM elements
const cameraOverlay = document.getElementById('cameraOverlay');
const ptzOffMessageEl = document.getElementById('ptz-off-message');
const pipVideo = document.getElementById('pipVideo');
const noFeedMessageEl = document.getElementById('no-feed-message');
const vehicleDataEl = document.getElementById('vehicle-data');
const cameraVideo = document.getElementById('cameraVideo');

// Dynamically determine the host IP from the serving location
const host = window.location.hostname;
const protocol = window.location.protocol; // e.g. "http:"
// const port = window.location.port; // e.g. "8080"

let basePort = 1984; // adjust if your streaming server runs on a different port
if (protocol === 'https:') {
    basePort = 1985;
}
const baseUrl = `http://${host}:${basePort}/api/webrtc?src=`;

// Map camera names to actual streaming URLs
const cameraSources = {
    "PTZ Thermal Camera": `${baseUrl}PTZ_Thermal`,
    "PTZ Visible Camera": `${baseUrl}PTZ_Visual`,
    "Front Camera": `${baseUrl}Front_Camera`
};

// Socket setup
const socket = io.connect(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.hostname}:${location.port || (location.protocol === 'https:' ? 443 : 80)}${location.pathname}`);

socket.on('connect', () => {
    logMessage("WS: Connected to server");
    socket.emit('handshake');
});

socket.on('ptz-angles', (data) => {
    cameraOverlay.innerHTML = `PTZ Rotation: ${data.horizontal.toFixed(2)}°<br>Tilt: ${data.vertical.toFixed(2)}°`;
});

/**
 * Safely stop and close an RTCPeerConnection
 */
function stopRTCPeerConnection(connection) {
    if (connection) {
        connection.getSenders().forEach(s => s.track && s.track.stop());
        connection.getReceivers().forEach(r => r.track && r.track.stop());
        connection.close();
    }
}

/**
 * Play a camera stream in a given <video> element via WebRTC
 */
async function playCameraStream(url, videoEl) {
    let localPc = null;
    try {
        logMessage(`Action: Attempting to set video source: ${url}`);

        // Create and configure RTCPeerConnection
        localPc = new RTCPeerConnection();

        // Add a transceiver for video (recvonly)
        localPc.addTransceiver('video', { direction: 'recvonly' });

        // On track received, bind to video element
        localPc.ontrack = (event) => {
            if (event && event.streams && event.streams[0]) {
                videoEl.srcObject = event.streams[0];
                logMessage('WS: Video track received');
            } else {
                logMessage('Warning: No valid video track in ontrack event.');
            }
        };

        // Create offer, set local description
        const offer = await localPc.createOffer();
        await localPc.setLocalDescription(offer);

        logMessage('Connection: Sending offer to server...');
        let response;
        try {
            response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'offer', sdp: offer.sdp })
            });
        } catch (fetchErr) {
            logMessage(`Network error fetching camera feed: ${fetchErr}`);
            localPc.close();
            return { pc: null, success: false };
        }

        if (!response.ok) {
            logMessage(`Error fetching camera feed. HTTP status: ${response.status}`);
            localPc.close();
            return { pc: null, success: false };
        }

        // Parse server's answer
        let answer;
        try {
            answer = await response.json();
        } catch (parseErr) {
            logMessage(`Failed to parse response JSON: ${parseErr}`);
            localPc.close();
            return { pc: null, success: false };
        }

        if (!answer || !answer.sdp) {
            logMessage('No valid SDP in answer, camera may be unavailable.');
            localPc.close();
            return { pc: null, success: false };
        }

        // Set remote description
        await localPc.setRemoteDescription(new RTCSessionDescription(answer));
        logMessage('Connection: Remote description set, waiting for tracks...');

        return { pc: localPc, success: true };

    } catch (err) {
        logMessage(`Unexpected error: ${err.message || err}`);
        if (localPc) {
            localPc.close();
        }
        return { pc: null, success: false };
    }
}

/**
 * Show the main camera in the primary video element
 */
async function showMainCamera(cameraName) {
    logMessage(`Action: Show main camera -> ${cameraName}`);

    stopRTCPeerConnection(pc);
    const url = cameraSources[cameraName];

    if (!url) {
        logMessage(`No source for ${cameraName}`);
        showNoFeedMessage(true);
        pc = null;
        cameraOn = false;
    } else {
        cameraOn = true; // Trying to turn camera on
        const result = await playCameraStream(url, cameraVideo);
        if (!result.success) {
            showNoFeedMessage(true);
            pc = null;
            cameraOn = false;
        } else {
            pc = result.pc;
            showNoFeedMessage(false);
        }
    }

    updatePTZOffMessage();
    updatePiP();
}

/**
 * Show the PiP camera in the PiP <video> element
 */
async function showPiP() {
    // If PiP is off, or the main camera is off, or the main camera is not PTZ, hide PiP
    if (!pipOn || !cameraOn || !(currentCamera === "PTZ Thermal Camera" || currentCamera === "PTZ Visible Camera")) {
        pipVideo.style.display = 'none';
        stopRTCPeerConnection(pipPc);
        pipPc = null;
        return;
    }

    let pipCamera = currentCamera === "PTZ Thermal Camera" ? "PTZ Visible Camera" : "PTZ Thermal Camera";
    logMessage(`Action: Show PiP camera -> ${pipCamera}`);

    stopRTCPeerConnection(pipPc);
    const url = cameraSources[pipCamera];

    if (!url) {
        logMessage(`No PiP source for ${pipCamera}`);
        pipVideo.style.display = 'none';
        pipPc = null;
        return;
    }

    const result = await playCameraStream(url, pipVideo);
    pipPc = result.pc;
    if (!result.success) {
        pipVideo.style.display = 'none';
        pipPc = null;
    } else {
        pipVideo.style.display = 'block';
    }
}

/**
 * Wrapper to update PiP state
 */
function updatePiP() {
    showPiP();
}

/**
 * Show or hide the 'no feed' message
 */
function showNoFeedMessage(show) {
    noFeedMessageEl.style.display = show ? 'block' : 'none';
}

/**
 * Update the PTZ-off message for PTZ cameras that aren't powered on
 */
function updatePTZOffMessage() {
    const isPTZCamera = (currentCamera === "PTZ Thermal Camera" || currentCamera === "PTZ Visible Camera");
    if (!cameraOn && isPTZCamera) {
        ptzOffMessageEl.style.display = 'block';
        cameraOverlay.style.display = 'none';
        pipVideo.style.display = 'none';
    } else {
        ptzOffMessageEl.style.display = 'none';
        cameraOverlay.style.display = 'block';
        if (pipOn && cameraOn && isPTZCamera) {
            pipVideo.style.display = 'block';
        }
    }
}

/**
 * Send motion commands to the server
 */
function handleMotion(pan, tilt) {
    const speedFactor = Math.max(Math.abs(pan), Math.abs(tilt)) * baseSpeed;
    const now = performance.now();
    const panDiff = Math.abs(pan - lastPan);
    const tiltDiff = Math.abs(tilt - lastTilt);
    const speedDiff = Math.abs(speedFactor - lastSpeed);
    const inDeadzone = (pan === 0 && tilt === 0);

    if (inDeadzone) {
        if (!hasStopped) {
            socket.emit('stop');
            logMessage("Motion: stop (deadzone)");
            hasStopped = true;
        }
    } else {
        hasStopped = false;
        if ((panDiff > 0.05 || tiltDiff > 0.05 || speedDiff > 0.05) && (now - lastEmitTime > emitInterval)) {
            socket.emit('motion', { pan, tilt, speed: speedFactor });
            logMessage(`Motion: pan=${pan.toFixed(2)} tilt=${tilt.toFixed(2)} speed=${speedFactor.toFixed(2)}`);
            lastPan = pan;
            lastTilt = tilt;
            lastSpeed = speedFactor;
            lastEmitTime = now;
        }
    }
}

/**
 * Request browser geolocation for logging or display
 */
function requestLocation() {
    logMessage("Requesting location...");
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                const mgrsStr = mgrs.forward([lon, lat], 5);
                vehicleDataEl.textContent = `Lat: ${lat.toFixed(4)}°, Lon: ${lon.toFixed(4)}°, MGRS: ${mgrsStr}`;
                logMessage(`Location acquired: Lat=${lat.toFixed(4)}, Lon=${lon.toFixed(4)}, MGRS=${mgrsStr}`);
            },
            (err) => {
                logMessage(`GPS Error: ${err.message}`);
                vehicleDataEl.textContent = "Lat: N/A, Lon: N/A, MGRS: N/A (GPS unavailable)";
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    } else {
        logMessage("GPS not supported by this browser");
        vehicleDataEl.textContent = "Lat: N/A, Lon: N/A, MGRS: N/A (GPS not supported)";
    }
}

/**
 * Camera thumbnails
 *
 * NOTE: Updated selector to match '.camera-select .thumbnail'
 */
const thumbnails = document.querySelectorAll('.camera-select .thumbnail');
thumbnails.forEach(thumb => {
    thumb.addEventListener('click', () => {
        const cameraName = thumb.getAttribute('data-camera');
        logMessage(`User: Selected camera: ${cameraName}`);

        // Update active thumbnail
        thumbnails.forEach(t => t.classList.remove('active'));
        thumb.classList.add('active');

        currentCamera = cameraName;
        showMainCamera(currentCamera);

        if (!locationRequested) {
            locationRequested = true;
            requestLocation();
        }
    });
});

/**
 * Handle Picture-in-Picture button (if desired)
 */
const pipButton = document.getElementById('pip-button');
pipButton.addEventListener('click', () => {
    pipOn = !pipOn;
    logMessage(`User toggled PiP: ${pipOn ? 'ON' : 'OFF'}`);
    updatePiP();
});

// Initial camera load
showMainCamera(currentCamera);

// Update UI state
updatePTZOffMessage();

/**
 * Example function for other button states (if you have them)
 * Stubbed out here
 */
function updateButtonState() {
    // If you have other buttons to disable/enable, do so here
    // e.g., toggling IR/visible light, etc.
}
