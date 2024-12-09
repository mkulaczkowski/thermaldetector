import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from JetsonNano_PTZ.pelco.pelco_controller import PELCO_Functions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

ptz_controller = PELCO_Functions(ip_address='192.168.137.99')

ptz_lock = threading.Lock()
ptz_state = {
    'direction': 'STOP',
    'pan_speed': 0x09,
    'tilt_speed': 0x09
}

def update_ptz_state(direction, pan_speed, tilt_speed):
    with ptz_lock:
        ptz_state['direction'] = direction
        ptz_state['pan_speed'] = pan_speed
        ptz_state['tilt_speed'] = tilt_speed

def get_ptz_state():
    with ptz_lock:
        return (ptz_state['direction'], ptz_state['pan_speed'], ptz_state['tilt_speed'])

def ptz_command_sender():
    last_direction, last_pan_speed, last_tilt_speed = 'STOP', 0x09, 0x09
    interval = 0.05 # 50ms interval (~20 commands per second max)
    while True:
        direction, pan_speed, tilt_speed = get_ptz_state()
        # Only send if changed significantly


        if (direction != last_direction or abs(pan_speed - last_pan_speed) > 2 or abs(tilt_speed - last_tilt_speed) > 2):
            if direction == 'STOP':
                ptz_controller.pantilt_stop()
            else:
                ptz_controller.pantilt_move(direction, pan_speed, tilt_speed)

            last_direction, last_pan_speed, last_tilt_speed = direction, pan_speed, tilt_speed
            print(f'{last_direction}, {last_pan_speed}, {last_tilt_speed}')
        time.sleep(interval)



threading.Thread(target=ptz_command_sender, daemon=True).start()


@socketio.on('stop')
def handle_stop_event():
    update_ptz_state('STOP', 0x09, 0x09)

@app.route('/')
def index():
    return render_template('index_v2.html') # Ensure index.html is the client code

@socketio.on('connect')
def handle_connect():
    app.logger.info("Client connected")

@socketio.on('motion')
def handle_motion_event(json):
    pan_input = float(json.get('pan', 0.0))
    tilt_input = float(json.get('tilt', 0.0))
    speed_input = float(json.get('speed', 0.0))

    deadzone = 0.05
    if abs(pan_input) < deadzone and abs(tilt_input) < deadzone:
        update_ptz_state('STOP', 0x09, 0x09)
        return

    min_speed = 0x09
    max_speed = 0x3F
    max_speed_tilt = 0xFF
    pan_speed_val = min_speed + int((max_speed - min_speed) * (abs(pan_input) * speed_input))
    tilt_speed_val = min_speed + int((max_speed_tilt - min_speed) * (abs(tilt_input) * speed_input))

    direction = 'STOP'
    if tilt_input > deadzone:
        if pan_input > deadzone:
            direction = 'UP-RIGHT'
        elif pan_input < -deadzone:
            direction = 'UP-LEFT'
        else:
            direction = 'UP'
    elif tilt_input < -deadzone:
        if pan_input > deadzone:
            direction = 'DOWN-RIGHT'
        elif pan_input < -deadzone:
            direction = 'DOWN-LEFT'
        else:
            direction = 'DOWN'
    else:
        if pan_input > deadzone:
            direction = 'RIGHT'
        elif pan_input < -deadzone:
            direction = 'LEFT'

    update_ptz_state(direction, pan_speed_val, tilt_speed_val)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
