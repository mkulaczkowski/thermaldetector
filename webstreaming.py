# import the necessary packages
import logging

from flask_socketio import SocketIO, emit

from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
import logging
import RPi.GPIO as GPIO

from cameras.Focuser import Focuser

from cameras.fusion_camera import FusionCamera
from cameras.opencv_thermal_camera import ThermalCamera
from cameras.opencv_visible_camera import VisibleCamera
from controlers.swtich_controller import GPIO_switch

# initialize a flask object
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'Ranger'
socketio = SocketIO(app, logger=True, engineio_logger=True)
try:
    focuser = Focuser(1)
except Exception as e:
    logging.critical(f'Failed to initialize focuser: {e}')



@socketio.on("connect")
def test_connect():
    print("Connected")
    emit("handshake", {"data": "Connected", "start_pan": focuser.get(Focuser.OPT_MOTOR_X),
                       "start_tilt": focuser.get(Focuser.OPT_MOTOR_Y)})


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)


@socketio.on('cmd')
def handle_message(data):
    try:
        switch = GPIO_switch()
    except Exception as e:
        logging.critical(f'Failed to initialize switch: {e}')
    if data['cmd'] == 'thermal-on':
        switch.thermal_camera_on()
    elif data['cmd'] == 'thermal-off':
        switch.thermal_camera_off()
    elif data['cmd'] == 'ir-cut':
        focuser.set(Focuser.OPT_IRCUT, focuser.get(Focuser.OPT_IRCUT) ^ 0x0001)
        print('IR: ' + str(focuser.get(Focuser.OPT_IRCUT)))
    print(f'received cmd: {str(data)}')


@socketio.on('motion')
def handle_motion_event(json):
    print('Received motion event: ' + str(json))
    value_x = int(4 * json['pan'])
    value_y = int(4 * json['tilt'])
    if value_x != 0:
        focuser.set(Focuser.OPT_MOTOR_X, focuser.get(Focuser.OPT_MOTOR_X) + value_x)
    if value_y != 0:
        focuser.set(Focuser.OPT_MOTOR_Y, focuser.get(Focuser.OPT_MOTOR_Y) + value_y)

    print('Pan: ' + str(focuser.get(Focuser.OPT_MOTOR_X)))
    print('Tilt: ' + str(focuser.get(Focuser.OPT_MOTOR_Y)))


@socketio.on('optic')
def handle_optic_event(json):
    print('Received optic event: ' + str(json))
    value_zoom = int(100 * json['zoom'])
    value_focus = int(100 * json['focus'])

    if value_zoom != 0:
        focuser.set(Focuser.OPT_ZOOM, focuser.get(Focuser.OPT_ZOOM) + value_zoom)
    if value_focus != 0:
        focuser.set(Focuser.OPT_FOCUS, focuser.get(Focuser.OPT_FOCUS) + value_focus)

    print('Zoom: ' + str(focuser.get(Focuser.OPT_ZOOM)))
    print('Focus: ' + str(focuser.get(Focuser.OPT_FOCUS)))


@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed/visible/')
def visible_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(VisibleCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/thermal/')
def thermal_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(ThermalCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed/fusion/')
def fusion_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
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
    # start a thread that will perform motion detection

    # start the flask app
    print(f'Started on port {args["ip"]}:{args["port"]}')
    # app.run(host=args["ip"], port=args["port"], debug=True,
    #        threaded=True, use_reloader=False)
    socketio.run(app, host=args["ip"], port=args["port"], debug=True)
