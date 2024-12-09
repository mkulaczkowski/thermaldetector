import time
import threading
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from JetsonNano_PTZ.pelco.pelco_controller import PELCO_Functions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

# Initialize PTZ controller
ptz_controller = PELCO_Functions(ip_address='192.168.137.99')

# Shared PTZ state with thread lock
ptz_lock = threading.Lock()
ptz_state = {
    'direction': 'STOP',
    'pan_speed': 0x05,
    'tilt_speed': 0x05
}

# Logging configuration
app.logger.setLevel(logging.DEBUG)


def update_ptz_state(direction, pan_speed, tilt_speed):
    """
    Update the PTZ state in a thread-safe manner.

    :param direction: PTZ direction (e.g. 'UP', 'LEFT', 'STOP')
    :param pan_speed: Speed for pan axis
    :param tilt_speed: Speed for tilt axis
    """
    with ptz_lock:
        ptz_state['direction'] = direction
        ptz_state['pan_speed'] = pan_speed
        ptz_state['tilt_speed'] = tilt_speed


def get_ptz_state():
    """
    Safely retrieve the current PTZ state.

    :return: (direction, pan_speed, tilt_speed)
    """
    with ptz_lock:
        return ptz_state['direction'], ptz_state['pan_speed'], ptz_state['tilt_speed']


def ptz_command_sender():
    """
    Background thread that periodically checks if the PTZ state changed
    and sends commands to the camera only when necessary.
    """
    last_direction, last_pan_speed, last_tilt_speed = 'STOP', 0x05, 0x05
    interval = 1  # 50ms interval (~20 commands per second)
    while True:
        direction, pan_speed, tilt_speed = get_ptz_state()

        # Send command only if a significant change occurred
        if (direction != last_direction or
                abs(pan_speed - last_pan_speed) > 2 or
                abs(tilt_speed - last_tilt_speed) > 2):

            if direction == 'STOP':
                ptz_controller.pantilt_stop()
            else:
                ptz_controller.pantilt_move(direction, pan_speed, tilt_speed)

            last_direction, last_pan_speed, last_tilt_speed = direction, pan_speed, tilt_speed
            app.logger.debug(f'PTZ Update -> Direction: {direction}, Pan Speed: {pan_speed}, Tilt Speed: {tilt_speed}')

        time.sleep(interval)


# Start the PTZ command sender thread
threading.Thread(target=ptz_command_sender, daemon=True).start()


@socketio.on('stop')
def handle_stop_event():
    """
    Handle a stop event, setting direction to STOP and speeds to a default low speed.
    """
    update_ptz_state('STOP', 0x09, 0x09)


@socketio.on('connect')
def handle_connect():
    """
    Handle a new client connection.
    """
    app.logger.info("Client connected")


@socketio.on('motion')
def handle_motion_event(json):
    """
    Handle motion events from the client’s joystick input.
    Compute direction and speeds based on joystick values.
    """
    pan_input = float(json.get('pan', 0.0))
    tilt_input = float(json.get('tilt', 0.0))
    speed_input = float(json.get('speed', 0.0))

    deadzone = 0.1
    # Check if we're in the deadzone for both axes
    if abs(pan_input) < deadzone and abs(tilt_input) < deadzone:
        # Joystick in deadzone -> STOP
        update_ptz_state('STOP', 0x09, 0x09)
        return

    # Determine direction:
    # If both axes exceed deadzone, choose a diagonal direction
    if abs(pan_input) > deadzone and abs(tilt_input) > deadzone:
        vertical_dir = 'UP' if tilt_input > 0 else 'DOWN'
        horizontal_dir = 'RIGHT' if pan_input > 0 else 'LEFT'
        direction = f'{vertical_dir}-{horizontal_dir}'
    else:
        # Only one axis significantly moved
        if abs(tilt_input) > deadzone:
            direction = 'UP' if tilt_input > 0 else 'DOWN'
        elif abs(pan_input) > deadzone:
            direction = 'RIGHT' if pan_input > 0 else 'LEFT'
        else:
            direction = 'STOP'  # Just a fallback

    # Calculate magnitude of input for speed
    magnitude = max(abs(pan_input), abs(tilt_input)) * speed_input
    app.logger.debug(f'magnitude:{magnitude}')
    # Define discrete speed levels for pan
    pan_low_speed = 0x15
    pan_med_speed = 0x2D
    pan_high_speed = 0x3F  # Pan max speed

    # Define discrete speed levels for tilt
    tilt_low_speed = 0x15
    tilt_med_speed = 0x2D
    tilt_high_speed = 0xFF  # Tilt max speed

    # Choose speed based on magnitude
    if magnitude < 0.33:
        chosen_pan_speed = pan_low_speed
        chosen_tilt_speed = tilt_low_speed
    elif magnitude < 0.66:
        chosen_pan_speed = pan_med_speed
        chosen_tilt_speed = tilt_med_speed
    else:
        chosen_pan_speed = pan_high_speed
        chosen_tilt_speed = tilt_high_speed

    # Update PTZ state with chosen direction and speeds
    update_ptz_state(direction, chosen_pan_speed, chosen_tilt_speed)


@app.route('/')
def index():
    """
    Serve the main page.
    """
    return render_template('index_v2.html')
