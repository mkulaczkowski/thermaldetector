$(document).ready(function () {
    const socket = io.connect(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.hostname}:${location.port || (location.protocol === 'https:' ? 443 : 80)}${location.pathname}`);

    let currentFeed = 1;
    let isThermalOn = false;
    let isLaserOn = false;
    let isCameraOn = true;
    let areLightsOn = false;
    let areIRLightsOn = false;
    let gamepadIndex;
    let tracking;
    let zoomLevel = 1;
    let ptzSpeed = 1; // 1: Slow, 2: Medium, 3: Fast

    function changeChannel(channel) {
        $("#primary_video").attr("src", {
            'Fusion': fusionFeed,
            'Thermal': thermalFeed,
            'Optical': visibleFeed
        }[channel]);
        $("#channel").text(`Channel: ${channel}`);
        $("#primary_video").show();

    }

    function emitGetPtzAngles() {
        socket.emit('get_ptz_angles');
    }

    function emitGetRelayStatus() {
        socket.emit('get_relay_status');
    }


    function switchChannels() {
        currentFeed = (currentFeed + 1) % 3;
        changeChannel(['Optical', 'Thermal', 'Fusion'][currentFeed]);
    }

    function toggleCamera() {
        socket.emit('cmd', {'cmd': isCameraOn ? 'camera-off' : 'camera-on'});
        isCameraOn = !isCameraOn;
        $("#toggle-camera span").text(isCameraOn ? 'power_off' : 'power_settings_new');
    }

    function reInitCameras() {
        socket.emit('cmd', {'cmd': 'reinit_cameras'});
        isCameraOn = true;
    }

    function toggleLights() {
        socket.emit('cmd', {'cmd': areLightsOn ? 'lights-off' : 'lights-on'});
        areLightsOn = !areLightsOn;
        $("#toggle-lights span").text(areLightsOn ? 'flashlight_off' : 'flashlight_on');
    }

    function toggleIRLights() {
        socket.emit('cmd', {'cmd': areIRLightsOn ? 'ir-lights-off' : 'ir-lights-on'});
        areIRLightsOn = !areIRLightsOn;
        $("#toggle-lights-ir span").text(areIRLightsOn ? 'bedtime_off' : 'bedtime');
    }

    const deadzone = 0.1; // Adjust for desired sensitivity
    const baseSpeed = 1.0; // Base speed scaling factor
    const pollInterval = 1000;

    function normalize(value, deadzone) {
        // If within deadzone, treat as 0
        if (Math.abs(value) < deadzone) return 0;
        // Remap from [-1, 1] to [-1, 1] but with deadzone removed
        const sign = Math.sign(value);
        const adjusted = (Math.abs(value) - deadzone) / (1 - deadzone);
        return sign * adjusted;
    }

    function pollGamepad() {
        const gamepad = navigator.getGamepads()[0];
        if (!gamepad) return; // No gamepad connected

        // Left stick used for PTZ control
        let pan = gamepad.axes[0];  // Horizontal axis: -1 (left), +1 (right)
        let tilt = gamepad.axes[1]; // Vertical axis: -1 (up), +1 (down) – we may invert this if needed

        // Normalize inputs
        pan = normalize(pan, deadzone);
        tilt = normalize(-tilt, deadzone); // Invert tilt to have up as positive

        // Calculate a speed factor based on how far the stick is pushed
        // Speed factor: 0.0 (no movement) to 1.0 (max tilt/pan)
        const panAbs = Math.abs(pan);
        const tiltAbs = Math.abs(tilt);
        const speedFactor = Math.max(panAbs, tiltAbs) * baseSpeed;

        // Send the current pan, tilt, and speed to the server
        // Assumes a socket.io or WebSocket connection is established as `socket`

        socket.emit('motion', {pan, tilt, speed: speedFactor});

    }

// Start polling when gamepad is connected
    window.addEventListener('gamepadconnected', () => {
        console.log('Gamepad connected!');
        setInterval(pollGamepad, pollInterval);
    });


    // function handleGamepadInput() {
    //     const myGamepad = navigator.getGamepads()[gamepadIndex];
    //     if (!myGamepad) return;
    //
    //     if (myGamepad.axes.some(axis => axis.toFixed(2) != 0.00)) {
    //         const [pan, tilt, zoom, focus] = myGamepad.axes.map(axis => parseFloat(axis.toFixed(2)));
    //         socket.emit('motion', {pan: -pan, tilt: tilt, relative: true});
    //         socket.emit('optic', {zoom: zoom, focus: -focus, relative: true});
    //     }
    //
    //     myGamepad.buttons.forEach((button, index) => {
    //         if (button.pressed) {
    //             const actions = [
    //                 () => changeChannel('Fusion'), () => changeChannel('Optical'), () => changeChannel('Thermal'),
    //                 () => socket.emit('cmd', {'cmd': 'ir-cut'}), null, null,
    //                 () => socket.emit('cmd', {'cmd': 'min-zoom'}), () => socket.emit('cmd', {'cmd': 'max-zoom'}),
    //                 switchChannels, toggleThermal,
    //                 () => {
    //                     socket.emit('cmd', {'cmd': 'laser-off'});
    //                     isLaserOn = false;
    //                 },
    //                 () => {
    //                     socket.emit('cmd', {'cmd': 'laser-on'});
    //                     isLaserOn = true;
    //                 },
    //                 toggleThermal, switchChannels, () => socket.emit('cmd', {'cmd': 'ir-cut'}), null
    //             ];
    //             actions[index]?.();
    //         }
    //     });
    //}


    socket.on('connect', () => socket.emit('handshake', {data: 'I\'m connected!'}));
    socket.on('handshake', data => {
        $("#pantilt").text(`Pan: ${data.start_horizontal} | Tilt: ${data.start_vertical}`);
        isThermalOn = data.thermal_status;
        //$("#primary_video").attr("src", thermalFeed);
        emitGetRelayStatus()
    });

    // socket.on('ptz', data => {
    //
    //     $("#pantilt").text(`Pan: ${data.horizontal} | Tilt: ${data.vertical}`);
    //     if (data.horizontal > 240 || data.horizontal < 5) {
    //         stopRotation();
    //     }
    // });

    socket.on('relay', data => {
        if (data.channel1) {
            $('#toggle-lights span').text('flashlight_on'); // Add class to indicate active status
            areLightsOn = true;
        } else {
            $('#toggle-lights span').text('flashlight_off'); // Remove class to indicate inactive status
            areLightsOn = false;
        }

        if (data.channel2) {
            $('#toggle-lights-ir span').text('bedtime'); // Add class to indicate active status
            areIRLightsOn = true;
        } else {
            $('#toggle-lights-ir span').text('bedtime_off'); // Remove class to indicate inactive status
            areIRLightsOn = false;
        }
    });

    $("#reload").click(() => location.reload());
    $("#toggle").click(switchChannels);
    $("#toggle-camera").click(toggleCamera);
    $("#reinit-camera").click(reInitCameras);
    $("#toggle-lights").click(toggleLights);
    $("#toggle-lights-ir").click(toggleIRLights);

    $("#speed-1").click(() => setSpeed(1));
    $("#speed-2").click(() => setSpeed(2));
    $("#speed-3").click(() => setSpeed(3));

    const amount = event => event.shiftKey ? 5 : 1;
    const activeKeys = {};

    const stopRotation = () => {
        console.log('Stop rotating');
        socket.emit('stop'); // Replace with actual PTZ stop command
    };
    const stopZoom = () => {
        console.log('Stop zoom');
        socket.emit('stop_zoom'); // Replace with actual PTZ stop command
    };

    const handleMotion = (pan, tilt, speed = ptzSpeed) => {
        console.log(`pan: ${pan}, tilt: ${tilt}, speed: ${speed}`);
        socket.emit('motion', {pan, tilt, speed: speed, relative: true});
    };

    const setSpeed = (speed) => {
        ptzSpeed = speed;
        $("#speed-level").text(`Speed: ${speed}`);
        console.log(`PTZ speed set to ${speed}`);
    };

    $(document).keydown(event => {
        if (activeKeys[event.key]) return; // If the key is already active, do nothing
        activeKeys[event.key] = true;

        if (event.ctrlKey) {
            if (event.shiftKey && event.key === 'R') socket.emit('cmd', {'cmd': 'restart'});
            else if (event.key === 't') socket.emit('cmd', {'cmd': 'thermal-on'});
            else if (['a', 'b', 'c', 'd'].includes(event.key)) socket.emit('cmd', {'cmd': 'setPos', 'pos': event.key});
        } else {
            const keyActions = {
                'ArrowLeft': () => handleMotion(amount(event), 0),
                'ArrowUp': () => handleMotion(0, amount(event)),
                'ArrowRight': () => handleMotion(-amount(event), 0),
                'ArrowDown': () => handleMotion(0, -amount(event)),
                '-': () => socket.emit('optic', {zoom: zoomLevel = -0.1, relative: false}),
                '+': () => socket.emit('optic', {zoom: zoomLevel = 0.1, relative: false}),
                '1': () => changeChannel('Optical'),
                '2': () => changeChannel('Thermal'),
                '3': () => changeChannel('Fusion'),
                't': () => toggleCamera(),
                'h': () => $('#help').css('opacity', $('#help').css('opacity') === '0' ? 1 : 0),
                'z': () => setSpeed(1),
                'x': () => setSpeed(2),
                'c': () => setSpeed(3)
            };

            if (keyActions[event.key]) keyActions[event.key]();
        }
    });

    $(document).keyup(event => {
        if (!activeKeys[event.key]) return; // If the key is not active, do nothing
        delete activeKeys[event.key];

        if (['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown'].includes(event.key)) {
            stopRotation();
        }
        if (['-', '+'].includes(event.key)) {
            stopZoom();
        }
    });

    setInterval(emitGetPtzAngles, 500);

    // $('#container').on('mousedown', e => {
    //     $('#container').css('cursor', 'grab');
    //     lp = e.pageX;
    //     lt = e.pageY;
    //     tracking = true;
    // }).on('mousemove', e => {
    //     if (tracking) {
    //         const pv = (e.pageX - lp) / 4;
    //         const tv = (e.pageY - lt) / 4;
    //         if (pv || tv) {
    //             socket.emit('motion', {pan: pv, tilt: tv, relative: true});
    //             lp = e.pageX;
    //             lt = e.pageY;
    //         }
    //     }
    // }).on('mouseup', () => {
    //     tracking = false;
    //     $('#container').css('cursor', 'default');
    // });

    $(".control-button").on("mousedown", function () {
        const action = $(this).attr("id");
        if (action === "up") handleMotion(0, amount(event));
        else if (action === "down") handleMotion(0, -amount(event));
        else if (action === "left") handleMotion(amount(event), 0);
        else if (action === "right") handleMotion(-amount(event), 0);
        else if (action === "zoom-in") socket.emit('optic', {zoom: zoomLevel = 1, relative: false});
        else if (action === "zoom-out") socket.emit('optic', {zoom: zoomLevel = -1, relative: false});
        $("#zoom-level").text(`Zoom: ${zoomLevel.toFixed(1)}`);
    });

    // Error handling for video feed
    $("#primary_video").on('error', function () {
        $("#error-message").text("Error: Unable to load the camera feed. Please check the connection or try again later.").show();
        $("#primary_video").hide();
    });

    $('#toggle-hidden-panel').click(function () {
        $('#hidden-panel').slideToggle('slow', function () {
            if ($('#hidden-panel').is(':visible')) {
                $('#toggle-hidden-panel').text('Hide More Controls');
            } else {
                $('#toggle-hidden-panel').text('Show More Controls');
            }
        });
    });
    showUIOverlay();
});

function showUIOverlay() {
    $('.ui').css('opacity', 0.5);
}
