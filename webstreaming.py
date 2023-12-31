# import the necessary packages
import logging
import ssl
import subprocess

from flask_socketio import SocketIO, emit

from imutils.video import VideoStream
from flask import Response, jsonify
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
import logging

# from cameras.gyro import Gyro

thread = None
ping_thread = None
run_threads = True

from cameras.Focuser import Focuser

from cameras.fusion_camera import FusionCamera
from cameras.opencv_thermal_camera import ThermalCamera
from cameras.visible_camera import VisibleCamera

from logging.config import dictConfig

# lock = threading.Lock()
# try:
#     gyro_ = Gyro()
# except Exception as e:
#     logging.critical(f'Failed to initialize gyro: {e}')

try:
    time.sleep(5)
    from controlers.swtich_controller import GPIO_switch
except ImportError as e:
    print('GPIO error')

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

# initialize a flask object
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'Ranger'
socketio = SocketIO(app, logger=True, engineio_logger=True)
try:
    focuser = Focuser(1)
except Exception as e:
    logging.critical(f'Failed to initialize focuser: {e}')


@socketio.on("connect")
def connect():
    app.logger.debug("Client connected")
    emit("handshake", {"data": "Connected", "start_pan": focuser.get(Focuser.OPT_MOTOR_X),
                       "start_tilt": focuser.get(Focuser.OPT_MOTOR_Y)})
    # global run_threads
    # global thread
    # global ping_thread
    #
    # run_threads = True
    #
    # if thread is None or not thread.is_alive():
    #     # Set up the long running loop to listen for any changes from the Sonos
    #     thread = threading.Thread(target=gyro)
    #     thread.daemon = True
    #     thread.start()


# @socketio.on("get_gyro")
# def get_gyro(data):
#     app.logger.debug(f'received gyro: {str(data)}')
#     time.sleep(1)
#     emit("gyro",
#          {"accel": gyro_.read_accel(),
#           "gyro": gyro_.read_gyro(),
#           "heading": gyro_.get_heading()
#           })

@socketio.on('message')
def handle_message(data):
    app.logger.debug(f'received message: {str(data)}')


@socketio.on('cmd')
def handle_message(data):
    app.logger.debug(f'received cmd: {str(data)}')
    if data['cmd'] == 'thermal-on':
        switch = GPIO_switch()
        switch.thermal_camera_on()
        app.logger.info('Thermal On')
    elif data['cmd'] == 'thermal-off':
        switch = GPIO_switch()
        switch.thermal_camera_off()
        app.logger.info('Thermal Off')
    elif data['cmd'] == 'laser-on':
        switch = GPIO_switch()
        switch.laser_on()
        app.logger.info('Laser On')
    elif data['cmd'] == 'laser-off':
        switch = GPIO_switch()
        switch.laser_off()
        app.logger.info('Laser Off')
    elif data['cmd'] == 'max-zoom':
        focuser.set(Focuser.OPT_ZOOM, 7700)
        focuser.set(Focuser.OPT_FOCUS, 190)
    elif data['cmd'] == 'min-zoom':
        focuser.set(Focuser.OPT_ZOOM, 7400)
        focuser.set(Focuser.OPT_FOCUS, 20000)
    elif data['cmd'] == 'ir-cut':
        focuser.set(Focuser.OPT_IRCUT, focuser.get(Focuser.OPT_IRCUT) ^ 0x0001)
        app.logger.info('IR: ' + str(focuser.get(Focuser.OPT_IRCUT)))


@socketio.on('motion')
def handle_motion_event(json):
    app.logger.debug('Received motion event: ' + str(json))
    value_x = int(2 * json['pan'])
    value_y = int(2 * json['tilt'])
    if value_x != 0:
        focuser.set(Focuser.OPT_MOTOR_X, focuser.get(Focuser.OPT_MOTOR_X) + value_x)
    if value_y != 0:
        focuser.set(Focuser.OPT_MOTOR_Y, focuser.get(Focuser.OPT_MOTOR_Y) + value_y)

    app.logger.info('Pan: ' + str(focuser.get(Focuser.OPT_MOTOR_X)))
    app.logger.info('Tilt: ' + str(focuser.get(Focuser.OPT_MOTOR_Y)))


@socketio.on('optic')
def handle_optic_event(json):
    app.logger.debug('Received optic event: ' + str(json))
    value_zoom = int(200 * json['zoom'])
    value_focus = int(200 * json['focus'])

    if value_zoom != 0:
        focuser.set(Focuser.OPT_ZOOM, focuser.get(Focuser.OPT_ZOOM) + value_zoom)
    if value_focus != 0:
        focuser.set(Focuser.OPT_FOCUS, focuser.get(Focuser.OPT_FOCUS) + value_focus)

    app.logger.info('Zoom: ' + str(focuser.get(Focuser.OPT_ZOOM)))
    app.logger.info('Focus: ' + str(focuser.get(Focuser.OPT_FOCUS)))


@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


@app.route("/restart/")
def restart_video_sources():
    # return the rendered template
    app.logger.info('Restarting video sources')
    restart_service = subprocess.run(["sudo", "systemctl", "restart", "nvargus-daemon.service"])
    app.logger.debug("The exit code was: %d" % restart_service.returncode)
    return jsonify(status='OK')

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    for frame in camera.get_frame():
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed/visible/')
def visible_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    app.logger.info('Visible video feed')
    return Response(gen(VisibleCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/thermal/')
def thermal_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    app.logger.info('Thermal video feed')
    return Response(gen(ThermalCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/fusion/')
def fusion_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    app.logger.info('Fusion video feed')
    return Response(gen(FusionCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # construct the argument parser and parse command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True, default="0.0.0.0",
                    help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True, default=8000,
                    help="ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=25,
                    help="# of frames used to construct the background model")
    args = vars(ap.parse_args())

    app.logger.info('Restarting video sources')
    restart_service = subprocess.run(["sudo", "systemctl", "restart", "nvargus-daemon.service"])

    # start a thread that will perform motion detection
    # t = threading.Thread(target=detect_motion)
    # t.daemon = True
    # t.start()
    # start the flask app
    print(cv2.getBuildInformation())
    print(f'Started on port {args["ip"]}:{args["port"]}')
    # app.run(host=args["ip"], port=args["port"], debug=True,
    #        threaded=True, use_reloader=False)
    #context = ssl.create_default_context()
    #context.load_cert_chain(certfile='/Users/mkulaczkowski/Aiprojects/thermaldetector/localhost.crt', keyfile='/Users/mkulaczkowski/Aiprojects/thermaldetector/localhost.key')
    socketio.run(app, host=args["ip"], port=args["port"], debug=False)

