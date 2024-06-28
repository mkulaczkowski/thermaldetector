import logging
import ssl
import subprocess
import threading
import time

from flask import Flask, Response, jsonify, render_template
from flask_socketio import SocketIO, emit
from logging.config import dictConfig
from JetsonNano_PTZ.pelco.ptz_control import PELCO_Functions
from cameras.fusion_camera import FusionCamera, VisibleThermalCamera
from cameras.opencv_thermal_camera import ThermalCamera
from cameras.opencv_visible_camera import VisibleCamera

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

# Initialize PTZ controller
ptz_controller = PELCO_Functions(ip_address="192.168.20.22")

@socketio.on("connect")
def connect():
    app.logger.debug("Client connected")
    emit("handshake", {"data": "Connected", "start_horizontal": ptz_controller.query_horizontal_angle(),
                       "start_vertical": ptz_controller.query_vertical_angle()})

@socketio.on("get_ptz_angles")
def get_ptz_angles():
    app.logger.debug(f'Received GET PTZ ANGLE')
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
    value_zoom = int(200 * json['zoom'])
    value_focus = int(200 * json['focus'])
    # Implement focusing logic here if necessary

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

    camera = VisibleCamera()
    camera.start()

    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/thermal/')
def thermal_video_feed():
    app.logger.info('Thermal video feed')
    camera = ThermalCamera()
    camera.start()

    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/fusion/')
def fusion_video_feed():
    app.logger.info('Fusion video feed')

    camera = VisibleThermalCamera()

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
