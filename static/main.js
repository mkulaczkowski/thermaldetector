$(document).ready(function () {

    const socket = io.connect(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.hostname}:${location.port || (location.protocol === 'https:' ? 443 : 80)}${location.pathname}`);

    let currentFeed = 0;
    let isThermalOn = false;
    let isLaserOn = false;
    let gamepadIndex;
    let tracking;

    function changeChannel(channel) {
        $("#primary_video").attr("src", '');
        setTimeout(() => {
            $("#primary_video").attr("src", {
                'Fusion': fusionFeed,
                'Thermal': thermalFeed,
                'Optical': visibleFeed
            }[channel]);
            $("#channel").text(channel);
        }, 1000);
    }

    function emitGetPtzAngles() {
        socket.emit('get_ptz_angles');
    }

    function switchChannels() {
        currentFeed = (currentFeed + 1) % 3;
        changeChannel(['Optical', 'Thermal', 'Fusion'][currentFeed]);
    }

    function toggleThermal() {
        socket.emit('cmd', {'cmd': isThermalOn ? 'thermal-off' : 'thermal-on'});
        isThermalOn = !isThermalOn;
        $("#thermal").text(isThermalOn ? 'Thermal ON' : 'Thermal OFF');
    }

    function handleGamepadInput() {
        const myGamepad = navigator.getGamepads()[gamepadIndex];
        if (!myGamepad) return;

        if (myGamepad.axes.some(axis => axis.toFixed(2) != 0.00)) {
            const [pan, tilt, zoom, focus] = myGamepad.axes.map(axis => parseFloat(axis.toFixed(2)));
            socket.emit('motion', {pan: -pan, tilt: tilt, relative: true});
            socket.emit('optic', {zoom: zoom, focus: -focus, relative: true});
        }

        myGamepad.buttons.forEach((button, index) => {
            if (button.pressed) {
                const actions = [
                    () => changeChannel('Fusion'), () => changeChannel('Optical'), () => changeChannel('Thermal'),
                    () => socket.emit('cmd', {'cmd': 'ir-cut'}), null, null,
                    () => socket.emit('cmd', {'cmd': 'min-zoom'}), () => socket.emit('cmd', {'cmd': 'max-zoom'}),
                    switchChannels, toggleThermal,
                    () => {
                        socket.emit('cmd', {'cmd': 'laser-off'});
                        isLaserOn = false;
                    },
                    () => {
                        socket.emit('cmd', {'cmd': 'laser-on'});
                        isLaserOn = true;
                    },
                    toggleThermal, switchChannels, () => socket.emit('cmd', {'cmd': 'ir-cut'}), null
                ];
                actions[index]?.();
            }
        });
    }

    window.addEventListener('gamepadconnected', event => {
        gamepadIndex = event.gamepad.index;
        setInterval(handleGamepadInput, 100);
    });

    socket.on('connect', () => socket.emit('handshake', {data: 'I\'m connected!'}));
    socket.on('handshake', data => {
        $("#pantilt").text(`Pan: ${data.start_horizontal} Tilt: ${data.start_vertical}`);
        isThermalOn = data.thermal_status;
        $("#primary_video").attr("src", fusionFeed);
    });

    socket.on('ptz', data => {
        $("#pantilt").text(`Pan: ${data.horizontal} Tilt: ${data.vertical}`);
    });

    $("#reload").click(() => location.reload());
    $("#toggle").click(switchChannels);

    const amount = event => event.shiftKey ? 5 : 1;
    const activeKeys = {};

    const stopRotation = () => {
        console.log('Stop rotating');
        socket.emit('stop'); // Replace with actual PTZ stop command
    };

    const handleMotion = (pan, tilt) => {
        socket.emit('motion', {pan, tilt, relative: true});
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
                'ArrowRight': () => handleMotion(-amount(event), 0),
                'ArrowUp': () => handleMotion(0, amount(event)),
                'ArrowDown': () => handleMotion(0, -amount(event)),
                '0': () => changeChannel('Optical'),
                '1': () => changeChannel('Optical'),
                '2': () => changeChannel('Thermal'),
                '3': () => changeChannel('Fusion'),
                't': toggleThermal,
                'h': () => $('#help').css('opacity', $('#help').css('opacity') === '0' ? 1 : 0)
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
    });

    setInterval(emitGetPtzAngles, 1000);

    $('#container').on('mousedown', e => {
        $('#container').css('cursor', 'grab');
        lp = e.pageX;
        lt = e.pageY;
        tracking = true;
    }).on('mousemove', e => {
        if (tracking) {
            const pv = (e.pageX - lp) / 4;
            const tv = (e.pageY - lt) / 4;
            if (pv || tv) {
                socket.emit('motion', {pan: pv, tilt: tv, relative: true});
                lp = e.pageX;
                lt = e.pageY;
            }
        }
    }).on('mouseup', () => {
        tracking = false;
        $('#container').css('cursor', 'default');
    });

    showUIOverlay();
});

function showUIOverlay() {
    $('.ui').css('opacity', 0.5);
}
