import logging
import os
import ssl
import subprocess
import threading
import time

from flask import Flask, Response, jsonify, render_template
from flask_socketio import SocketIO, emit
from logging.config import dictConfig

from onvif import ONVIFError
from stream_infer import Player, Inference
from stream_infer.dispatcher import Dispatcher
from stream_infer.producer import PyAVProducer

from JetsonNano_PTZ.camera_controlers.onvif_controler import PTZCamera
from JetsonNano_PTZ.pelco.pelco_d import PELCO_Functions
from algos.yolo import YoloDetectionAlgo2
from cameras.ffmpeg_visible_camera import FFMPEGCamera
from cameras.fusion_camera import VisibleThermalCamera
from cameras.opencv_thermal_camera import ThermalCamera
from cameras.opencv_visible_camera import OpenCVVisibleCamera
# from cameras.opencv_visible_camera import VisibleCamera


from cameras.utils import connect_camera, connect_thermal_camera, connect_visible_camera
from controlers.swtich_controller import RelayModuleController

# Configure logging
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

# Initialize Flask app and SocketIO
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'Ranger'
socketio = SocketIO(app, logger=True, engineio_logger=True)
from flask import g

# Initialize PTZ controller
ptz_controller = PELCO_Functions(ip_address=os.getenv('PTZ_IP', '192.168.137.99'))

relay_controller = RelayModuleController(ip_address=os.getenv('PTZ_RELAY', '192.168.137.100'))

thermal_camera_ptz = None
visible_camera_ptz = None

# Global PTZ state and lock
ptz_state = {
    'direction': 'STOP',   # 'UP', 'DOWN', 'LEFT', 'RIGHT', etc.
    'pan_speed': 0x09,
    'tilt_speed': 0x09
}
ptz_lock = threading.Lock()


def update_ptz_state(direction, pan_speed, tilt_speed):
    with ptz_lock:
        ptz_state['direction'] = direction
        ptz_state['pan_speed'] = pan_speed
        ptz_state['tilt_speed'] = tilt_speed


def get_ptz_state():
    with ptz_lock:
        return ptz_state['direction'], ptz_state['pan_speed'], ptz_state['tilt_speed']


def ptz_command_sender(controller, interval=1):
    last_direction, last_pan_speed, last_tilt_speed = 'STOP', 0, 0
    while True:
        direction, pan_speed, tilt_speed = get_ptz_state()
        print(f'{direction}, {pan_speed}, {tilt_speed}')

        # Only send if direction/speed changed significantly
        if (direction != last_direction):
            if direction == 'STOP':
                controller.pantilt_stop()
            else:
                controller.pantilt_move(direction, pan_speed, tilt_speed)

            last_direction, last_pan_speed, last_tilt_speed = direction, pan_speed, tilt_speed

        time.sleep(interval)


# Start background thread for sending PTZ commands
threading.Thread(target=ptz_command_sender, args=(ptz_controller,), daemon=True).start()


def initialize_cameras():
    global visible_camera_ptz, thermal_camera_ptz

    thermal_camera_ptz = connect_thermal_camera()
    visible_camera_ptz = connect_visible_camera()


@socketio.on("connect")
def connect():
    app.logger.debug("Client connected")

    #initialize_cameras()

    emit("handshake", {"data": "Connected", "start_horizontal": ptz_controller.query_horizontal_angle(),
                       "start_vertical": ptz_controller.query_vertical_angle()})


@socketio.on("get_ptz_angles")
def get_ptz_angles():
    #app.logger.debug(f'Received GET PTZ ANGLE')

    horizontal_angle = ptz_controller.query_horizontal_angle()

    emit("ptz", {"horizontal": horizontal_angle,
                 "vertical": ptz_controller.query_vertical_angle()})



@socketio.on("get_relay_status")
def get_relay_status():
    # app.logger.debug(f'Received GET RELAY STATUS')
    emit("relay", {"channel1": relay_controller.get_channel_status(1),
                   "channel2": relay_controller.get_channel_status(2)})



@socketio.on('message')
def handle_message(data):
    app.logger.debug(f'Received message: {data}')


@socketio.on('cmd')
def handle_cmd(data):
    app.logger.debug(f'Received cmd: {data}')
    cmd = data['cmd']
    commands = {
        'camera-on': 'Camera On',
        'camera-off': 'Camera Off',
        'laser-on': 'Laser On',
        'laser-off': 'Laser Off',
        'max-zoom': 'Max Zoom',
        'min-zoom': 'Min Zoom',
        'ir-cut': 'IR Cut'
    }
    if cmd in commands:
        app.logger.info(commands[cmd])

    if cmd == 'camera-on':
        ptz_controller.turn_on_light()
        initialize_cameras()
    elif cmd == 'camera-off':
        ptz_controller.turn_off_light()
    elif cmd == 'reinit_cameras':
        initialize_cameras()

    elif cmd == 'lights-on':
        relay_controller.ch1_activate()
    elif cmd == 'lights-off':
        relay_controller.ch1_deactivate()
    elif cmd == 'ir-lights-on':
        relay_controller.ch2_activate()
    elif cmd == 'ir-lights-off':
        relay_controller.ch2_deactivate()


@socketio.on('motion')
def handle_motion_event(json):
    app.logger.debug('Received motion event: ' + str(json))

    pan_input = float(json.get('pan', 0.0))   # Range: [-1.0, 1.0]
    tilt_input = float(json.get('tilt', 0.0)) # Range: [-1.0, 1.0]
    speed_input = float(json.get('speed', 0.0)) # Range: [0.0, 1.0]

    # If both pan and tilt are near zero, update state to STOP
    deadzone = 0.05
    if abs(pan_input) < deadzone and abs(tilt_input) < deadzone:
        update_ptz_state('STOP', 0x09, 0x09)
        return

    # Pelco-D speed range
    min_speed = 0x09
    max_speed = 0x3F

    pan_speed_val = min_speed + int((max_speed - min_speed) * (abs(pan_input) * speed_input))
    tilt_speed_val = min_speed + int((max_speed - min_speed) * (abs(tilt_input) * speed_input))

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

    # Update PTZ state (background thread will send command)
    update_ptz_state(direction, pan_speed_val, tilt_speed_val)

@socketio.on('stop')
def handle_stop_event():
    app.logger.debug('Received stop event')
    update_ptz_state('STOP', 0x09, 0x09)

# @socketio.on('stop')
# def handle_stop_event():
#     app.logger.debug('Received stop event')
#     ptz_controller.pantilt_stop()


@socketio.on('optic')
def handle_optic_event(json):
    app.logger.debug('Received optic event: ' + str(json))
    value_zoom = float(json['zoom'])
    visible_camera_ptz.zoom(value_zoom)  # Example zoom in


@socketio.on('stop_zoom')
def handle_stop_event():
    app.logger.debug('Received stop zoom')
    visible_camera_ptz.stop_zoom()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/restart/")
def restart_video_sources():
    app.logger.info('Restarting video sources')
    restart_service = subprocess.run(["sudo", "systemctl", "restart", "nvargus-daemon.service"])
    app.logger.debug(f"The exit code was: {restart_service.returncode}")
    return jsonify(status='OK')


@app.route("/start/")
def start_video_sources():
    app.logger.info('Starting video sources')
    ptz_controller.turn_on_light()
    initialize_cameras()
    return jsonify(status='OK')


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    for frame in camera.frames():
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

def gen2(player):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    for frame, index in player.play():

        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed/visible/')
def visible_video_feed():
    app.logger.info('Visible video feed')
    global visible_camera_ptz, thermal_camera_ptz

    if not visible_camera_ptz:
        initialize_cameras()

    try:
        visible_camera = FFMPEGCamera(visible_camera_ptz.get_stream_url())
        visible_camera.start()
    except Exception as e:
        app.logger.critical('Visible video Error ' + str(e))
        return Response('Error', status=500)
    return Response(gen(visible_camera), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/thermal/')
def thermal_video_feed():
    app.logger.info('Thermal video feed')

    if not thermal_camera_ptz:
        initialize_cameras()

    try:
        thermal_camera = FFMPEGCamera(thermal_camera_ptz.get_stream_url())
        thermal_camera.start()
    except Exception as e:
        app.logger.critical('Thermal video Error ' + str(e))
        return Response('Error', status=500)
    return Response(gen(thermal_camera), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/fusion/')
def fusion_video_feed():
    app.logger.info('Fusion video feed')

    dispatcher = Dispatcher.create()
    inference = Inference(dispatcher)
    #inference.load_algo(YoloDetectionAlgo2(), frame_count=1, frame_step=0, interval=1)

    player = Player(dispatcher, PyAVProducer(800, 600), source=thermal_camera_ptz.get_stream_url())
    inference.start(player, fps=30)

    #camera = VisibleThermalCamera(visible_camera_ptz.get_stream_url(), thermal_camera_ptz.get_stream_url())
    return Response(gen2(player), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", type=str, required=True, help="IP address of the device")
    parser.add_argument("-o", "--port", type=int, required=True, help="Port number of the server (1024 to 65535)")
    parser.add_argument("-f", "--frame-count", type=int, default=25,
                        help="# of frames used to construct the background model")
    args = parser.parse_args()

    print(f'Started on port {args.ip}:{args.port}')

    socketio.run(app, host=args.ip, port=args.port, debug=True)
