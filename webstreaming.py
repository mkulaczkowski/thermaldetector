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

from JetsonNano_PTZ.camera_controlers.onvif_controler import PTZCamera
from JetsonNano_PTZ.pelco.ptz_control import PELCO_Functions
from cameras.fusion_camera import VisibleThermalCamera
from cameras.opencv_thermal_camera import ThermalCamera
#from cameras.opencv_visible_camera import VisibleCamera
from cameras.nano_visible_camera import VisibleCamera



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



def start_cameras():
    ptz_controller.turn_on_light()
    time.sleep(10)

    def connect_camera(ip, port, username, password, ptz_functions=True, retries=5, timeout=10):
        attempt = 0
        while attempt < retries:
            try:
                app.logger.info(f'Started Camera {ip}')
                return PTZCamera(ip=ip, port=port, username=username, password=password, ptz_functions=ptz_functions)
            except ONVIFError as e:
                attempt += 1
                if attempt < retries:
                    app.logger.warning(f'Attempt {attempt} failed to connect to camera at {ip}:{port}, retrying...')
                    time.sleep(timeout)
                else:
                    app.logger.error(f'Cannot connect to camera at {ip}:{port} after {retries} attempts')
                    return None

    visible_camera_ptz = connect_camera(
        ip=os.getenv('VISIBLE_CAMERA_IP', '192.168.20.94'),
        port=os.getenv('VISIBLE_CAMERA_PORT', 8899),
        username=os.getenv('VISIBLE_CAMERA_USER', 'admin'),
        password=os.getenv('VISIBLE_CAMERA_PASS', 'admin')
    )

    thermal_camera_ptz = connect_camera(
        ip=os.getenv('THERMAL_CAMERA_IP', '192.168.20.249'),
        port=os.getenv('THERMAL_CAMERA_PORT', 8000),
        username=os.getenv('THERMAL_CAMERA_USER', 'admin'),
        password=os.getenv('THERMAL_CAMERA_PASS', 'admin'),
        ptz_functions=False
    )

    return visible_camera_ptz, thermal_camera_ptz


# Initialize PTZ controller
ptz_controller = PELCO_Functions(ip_address=os.getenv('PTZ_IP', '192.168.20.22'))
# Start Cameras
visible_camera_ptz, thermal_camera_ptz = start_cameras()

@socketio.on("connect")
def connect():
    app.logger.debug("Client connected")
    emit("handshake", {"data": "Connected", "start_horizontal": ptz_controller.query_horizontal_angle(),
                       "start_vertical": ptz_controller.query_vertical_angle()})

@socketio.on("get_ptz_angles")
def get_ptz_angles():
    #app.logger.debug(f'Received GET PTZ ANGLE')
    emit("ptz", {"horizontal": ptz_controller.query_horizontal_angle(),
                 "vertical": ptz_controller.query_vertical_angle()})

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
    elif cmd == 'camera-off':
        ptz_controller.turn_off_light()

@socketio.on('motion')
def handle_motion_event(json):
    app.logger.debug('Received motion event: ' + str(json))
    value_x = int(2 * json['pan'])
    value_y = int(2 * json['tilt'])
    if value_x < 0:
        ptz_controller.pantilt_move('RIGHT')
    elif value_x > 0:
        ptz_controller.pantilt_move('LEFT')
    elif value_y > 0:
        ptz_controller.pantilt_move('UP')
    elif value_y < 0:
        ptz_controller.pantilt_move('DOWN')
@socketio.on('stop')
def handle_stop_event():
    app.logger.debug('Received stop event')
    ptz_controller.pantilt_stop()

@socketio.on('optic')
def handle_optic_event(json):
    app.logger.debug('Received optic event: ' + str(json))
    value_zoom = float(json['zoom'])
    visible_camera_ptz.zoom(value_zoom)  # Example zoom in
    time.sleep(1)
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

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    for frame in camera.get_frame():
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed/visible/')
def visible_video_feed():
    app.logger.info('Visible video feed')
    app.logger.info('Restarting video sources')
    restart_service = subprocess.run(["sudo", "systemctl", "restart", "nvargus-daemon.service"])
    visible_camera = VisibleCamera(visible_camera_ptz.get_stream_url()[7:], 1920, 1080, fps=25)
    visible_camera.start()

    return Response(gen(visible_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/thermal/')
def thermal_video_feed():
    app.logger.info('Thermal video feed')
    app.logger.info('Restarting video sources')
    restart_service = subprocess.run(["sudo", "systemctl", "restart", "nvargus-daemon.service"])
    thermal_camera = VisibleCamera(thermal_camera_ptz.get_stream_url()[7:], thermal_camera_ptz.get_stream_resolution()[0], thermal_camera_ptz.get_stream_resolution()[1], fps=25)
    thermal_camera.start()

    return Response(gen(thermal_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/fusion/')
def fusion_video_feed():
    app.logger.info('Fusion video feed')
    camera = VisibleThermalCamera(visible_camera_ptz.get_stream_url(), thermal_camera_ptz.get_stream_url())
    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", type=str, required=True, help="IP address of the device")
    parser.add_argument("-o", "--port", type=int, required=True, help="Port number of the server (1024 to 65535)")
    parser.add_argument("-f", "--frame-count", type=int, default=25, help="# of frames used to construct the background model")
    args = parser.parse_args()

    print(f'Started on port {args.ip}:{args.port}')
    socketio.run(app, host=args.ip, port=args.port, debug=True, allow_unsafe_werkzeug=True)
