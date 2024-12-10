// touch.js

const joystick = document.getElementById('touch-joystick');
const joystickHandle = document.getElementById('joystick-handle');

let touchActive = false;
let joystickCenterX, joystickCenterY;

joystick.addEventListener('touchstart', (e) => {
    e.preventDefault();
    touchActive = true;
    const rect = joystick.getBoundingClientRect();
    joystickCenterX = rect.x + rect.width / 2;
    joystickCenterY = rect.y + rect.height / 2;
}, {passive: false});

joystick.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if (!touchActive) return;
    const touch = e.touches[0];
    const dx = touch.clientX - joystickCenterX;
    const dy = touch.clientY - joystickCenterY;
    const maxRadius = 50;
    const distance = Math.min(maxRadius, Math.sqrt(dx * dx + dy * dy));
    const angle = Math.atan2(dy, dx);
    const x = distance * Math.cos(angle);
    const y = distance * Math.sin(angle);

    joystickHandle.style.transform = `translate(${x}px, ${y}px)`;
    let pan = x / maxRadius;
    let tilt = -y / maxRadius;
    if (Math.abs(pan) < deadzone) pan = 0;
    if (Math.abs(tilt) < deadzone) tilt = 0;

    handleMotion(pan, tilt);
}, {passive: false});

joystick.addEventListener('touchend', (e) => {
    e.preventDefault();
    touchActive = false;
    joystickHandle.style.transform = 'translate(-50%, -50%)';
    socket.emit('stop');
    logMessage("Touch Joystick: stop command");
}, {passive: false});
