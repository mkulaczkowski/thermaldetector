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

import cameras.visible_camera
from cameras.Focuser import Focuser
from cameras.visible_camera import visible_gstreamer_pipeline, thermal_gstreamer_pipeline
from controlers.swtich_controller import GPIO_switch

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'Ranger'
socketio = SocketIO(app, logger=True, engineio_logger=True)
try:
    focuser = Focuser(1)
except Exception as e:
    logging.critical(f'Failed to initialize focuser: {e}')

try:
    switch = GPIO_switch()
except Exception as e:
    logging.critical(f'Failed to initialize GPIO Switch: {e}')


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
    if data['cmd'] == 'thermal-on':
        switch.switch_camera_on()
    elif data['cmd'] == 'thermal-off':
        switch.switch_camera_off()
    print('received cmd: ' + data)

@socketio.on('motion')
def handle_motion_event(json):
    print('Received motion event: ' + str(json))
    value_x = int(5 * json['pan'])
    value_y = int(5 * json['tilt'])
    if value_x != 0:
        focuser.set(Focuser.OPT_MOTOR_X, focuser.get(Focuser.OPT_MOTOR_X) + value_x)
    if value_y != 0:
        focuser.set(Focuser.OPT_MOTOR_Y, focuser.get(Focuser.OPT_MOTOR_Y) + value_y)

    print('Pan: ' + str(focuser.get(Focuser.OPT_MOTOR_X)))
    print('Tilt: ' + str(focuser.get(Focuser.OPT_MOTOR_Y)))


@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


@app.route("/visible/")
def visible():
    # return the rendered template
    return render_template("visible.html")


@app.route("/thermal/")
def thermal():
    # return the rendered template
    return render_template("thermal.html")


@app.route("/fusion/")
def fusion():
    # return the rendered template
    return render_template("fusion.html")


@app.route('/zoom/<int:number>/')
def zoom(number):
    focuser.set(Focuser.OPT_ZOOM, number)

    response = app.response_class(
        response=f'Zoom: {focuser.get(Focuser.OPT_ZOOM)}',
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/focus/<int:number>/')
def focus(number):
    focuser.set(Focuser.OPT_FOCUS, number)
    response = app.response_class(
        response=f'Focus: {focuser.get(Focuser.OPT_FOCUS)}',
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/IR/')
def IR_cut():
    focuser.set(Focuser.OPT_IRCUT, focuser.get(Focuser.OPT_IRCUT) ^ 0x0001)
    response = app.response_class(
        response=f'Focus: {focuser.get(Focuser.OPT_IRCUT)}',
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/mode/<mode>/')
def change_source(mode):
    current_source = mode
    response = app.response_class(
        response=f'Mode: {current_source}',
        status=200,
        mimetype='application/json'
    )
    return response


def generate(mode='visible'):
    if mode == 'fusion' or mode == 'thermal':
        thermal_camera = cv2.VideoCapture(thermal_gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if not thermal_camera.isOpened():
            raise RuntimeError("Failed to open thermal camera!")
    elif mode == 'visible' or mode == 'fusion':
        visible_camera = cv2.VideoCapture(visible_gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if not visible_camera.isOpened():
            raise RuntimeError("Failed to open visible camera!")

    if mode == 'fusion':
        focuser.set(Focuser.OPT_FOCUS, 9300)
        focuser.set(Focuser.OPT_ZOOM, 7000)
    current_source = 'visible'
    # loop over frames from the output stream
    while True:
        # encode the frame in JPEG format
        with lock:
            if mode == 'visible':
                ret, outputFrame = visible_camera.read()
            elif mode == 'thermal':
                ret2, outputFrame = thermal_camera.read()
            elif mode == 'fusion':
                ret, outputFrame = visible_camera.read()
                ret2, thermalFrame = thermal_camera.read()

                resized = cv2.resize(thermalFrame, (1280, 853), interpolation=cv2.INTER_AREA)
                img_gray1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                ret, thresh1 = cv2.threshold(img_gray1, 150, 255, cv2.THRESH_BINARY)
                contours2, hierarchy2 = cv2.findContours(thresh1, cv2.RETR_TREE,
                                                         cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(outputFrame, contours2, -1, (0, 255, 0), 2, cv2.LINE_AA)

            # encode the frame in JPEG format
            if outputFrame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

        # ensure the frame was successfully encoded
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


# @app.route('/video_feed')
# def video_feed():
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     return Response(gen(Camera()),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/video_feed/<mode>")
def video_feed(mode):
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(mode),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


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
