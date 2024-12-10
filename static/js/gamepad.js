// gamepad.js

let gamepadConnected = false;
let gamepadIndex = null;
let lastButtonStates = [];

const gamepadStatusEl = document.querySelector('.gamepad-status');

window.addEventListener('gamepadconnected', (e) => {
    gamepadIndex = e.gamepad.index;
    gamepadConnected = true;
    logMessage(`Gamepad connected: ${e.gamepad.id}`);
    updateGamepadIcon();
    requestAnimationFrame(pollGamepad);
});

window.addEventListener('gamepaddisconnected', (e) => {
    gamepadIndex = null;
    gamepadConnected = false;
    logMessage("Gamepad disconnected");
    updateGamepadIcon();
});

function updateGamepadIcon() {
    if (gamepadConnected) {
        gamepadStatusEl.classList.add('connected');
        gamepadStatusEl.classList.remove('disconnected');
        gamepadStatusEl.textContent = "GP ON";
    } else {
        gamepadStatusEl.classList.remove('connected');
        gamepadStatusEl.classList.add('disconnected');
        gamepadStatusEl.textContent = "GP OFF";
    }
}

function normalize(value, deadzone) {
    if (Math.abs(value) < deadzone) return 0;
    const sign = Math.sign(value);
    const adjusted = (Math.abs(value) - deadzone) / (1 - deadzone);
    return sign * adjusted;
}

function handleGamepadJoystick(gp) {
    let pan = normalize(gp.axes[0], deadzone);
    let tilt = -normalize(gp.axes[1], deadzone);
    handleMotion(pan, tilt);
}

function handleGamepadButtons(gp) {
    if (lastButtonStates.length === 0) {
        lastButtonStates = gp.buttons.map(b => b.pressed);
    }

    gp.buttons.forEach((button, index) => {
        const wasPressed = lastButtonStates[index];
        const isPressed = button.pressed;
        if (!wasPressed && isPressed) {
            switch (index) {
                case 17: // PTZ Power
                    cameraOn = !cameraOn;
                    socket.emit('cmd', {cmd: cameraOn ? 'PTZ-on' : 'PTZ-off'});
                    logMessage(`Gamepad: PTZ Power -> ${cameraOn ? 'ON' : 'OFF'}`);
                    updateButtonState();
                    updatePTZOffMessage();
                    break;
                case 0: // Visible Light
                    visibleLightOn = !visibleLightOn;
                    socket.emit('cmd', {cmd: visibleLightOn ? 'lights-on' : 'lights-off'});
                    logMessage(`Gamepad: Visible Light -> ${visibleLightOn ? 'ON' : 'OFF'}`);
                    updateButtonState();
                    break;
                case 1: // IR Light
                    irLightOn = !irLightOn;
                    socket.emit('cmd', {cmd: irLightOn ? 'ir-lights-on' : 'ir-lights-off'});
                    logMessage(`Gamepad: IR Light -> ${irLightOn ? 'ON' : 'OFF'}`);
                    updateButtonState();
                    break;
                case 2: // Default Position
                    socket.emit('cmd', {cmd: 'default-position'});
                    logMessage("Gamepad: Default Position");
                    break;
                case 3: // Scan
                    scanning = !scanning;
                    socket.emit('cmd', {cmd: scanning ? 'start-scan' : 'stop-scan'});
                    logMessage(`Gamepad: Scan -> ${scanning ? 'START' : 'STOP'}`);
                    updateButtonState();
                    break;
                default:
                    break;
            }
        }
        lastButtonStates[index] = isPressed;
    });
}

function pollGamepad() {
    if (gamepadIndex === null) {
        requestAnimationFrame(pollGamepad);
        return;
    }

    const gp = navigator.getGamepads()[gamepadIndex];
    if (!gp) {
        requestAnimationFrame(pollGamepad);
        return;
    }

    handleGamepadJoystick(gp);
    handleGamepadButtons(gp);

    requestAnimationFrame(pollGamepad);
}
