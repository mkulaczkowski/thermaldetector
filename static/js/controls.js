// controls.js

// Buttons
const powerPtzBtn = document.getElementById('power-ptz');
const powerVisibleLightBtn = document.getElementById('power-visible-light');
const powerIrLightBtn = document.getElementById('power-ir-light');
const defaultPositionBtn = document.getElementById('default-position');
const scanBtn = document.getElementById('scan-button');
const lowLightBtn = document.getElementById('low-light-button');
const toggleThermalBtn = document.getElementById('toggle-thermal');
const pipBtn = document.getElementById('pip-button');

// Update button states based on global variables
function updateButtonState() {
    powerPtzBtn.classList.toggle('active', cameraOn);
    powerVisibleLightBtn.classList.toggle('active', visibleLightOn);
    powerIrLightBtn.classList.toggle('active', irLightOn);
    scanBtn.classList.toggle('active', scanning);
    pipBtn.classList.toggle('active', pipOn);
}

// Button event listeners
toggleThermalBtn.addEventListener('click', () => {
    socket.emit('cmd', {cmd: 'toggleThermal'});
    logMessage("Button: Toggle Thermal");
});

pipBtn.addEventListener('click', () => {
    pipOn = !pipOn;
    logMessage(`PiP -> ${pipOn ? 'ON' : 'OFF'}`);
    updateButtonState();
    updatePiP();
});

powerPtzBtn.addEventListener('click', () => {
    cameraOn = !cameraOn;
    socket.emit('cmd', {cmd: cameraOn ? 'PTZ-on' : 'PTZ-off'});
    logMessage(`PTZ Power -> ${cameraOn ? 'ON' : 'OFF'}`);
    updateButtonState();
    updatePTZOffMessage();
});

powerVisibleLightBtn.addEventListener('click', () => {
    visibleLightOn = !visibleLightOn;
    socket.emit('cmd', {cmd: visibleLightOn ? 'lights-on' : 'lights-off'});
    logMessage(`Visible Light -> ${visibleLightOn ? 'ON' : 'OFF'}`);
    updateButtonState();
});

powerIrLightBtn.addEventListener('click', () => {
    irLightOn = !irLightOn;
    socket.emit('cmd', {cmd: irLightOn ? 'ir-lights-on' : 'ir-lights-off'});
    logMessage(`IR Light -> ${irLightOn ? 'ON' : 'OFF'}`);
    updateButtonState();
});

defaultPositionBtn.addEventListener('click', () => {
    socket.emit('cmd', {cmd: 'default-position'});
    logMessage("Default Position command");
});

scanBtn.addEventListener('click', () => {
    scanning = !scanning;
    socket.emit('cmd', {cmd: scanning ? 'start-scan' : 'stop-scan'});
    logMessage(`Scan -> ${scanning ? 'START' : 'STOP'}`);
    updateButtonState();
});

lowLightBtn.addEventListener('click', () => {
    lowLightMode = !lowLightMode;
    document.body.classList.toggle('low-light', lowLightMode);
    lowLightBtn.classList.toggle('active', lowLightMode);
    logMessage(`Low Light Mode -> ${lowLightMode ? 'ON' : 'OFF'}`);
});
