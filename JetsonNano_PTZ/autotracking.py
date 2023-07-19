# encoding: UTF-8
import cv2 #sudo apt-get install python-opencv
import numpy as py
import os
import sys
import time
import argparse
from JetsonCamera import Camera

from Focuser import Focuser
from AutoFocus import AutoFocus


global image_count
image_count = 0

def parse_cmdline():
    parser = argparse.ArgumentParser(description='DoB Autotracking Controller.')

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    return parser.parse_args()
# parse input key
def parseKey(k,focuser,auto_focus,camera):
    global image_count
    motor_step  = 5
    focus_step  = 100
    zoom_step   = 100
    if k == ord('s'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) + motor_step)
    elif k == ord('w'):
        focuser.set(Focuser.OPT_MOTOR_Y,focuser.get(Focuser.OPT_MOTOR_Y) - motor_step)
    elif k == ord('d'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) - motor_step)
    elif k == ord('a'):
        focuser.set(Focuser.OPT_MOTOR_X,focuser.get(Focuser.OPT_MOTOR_X) + motor_step)
    elif k == ord('r'):
        focuser.reset(Focuser.OPT_FOCUS)
        focuser.reset(Focuser.OPT_ZOOM)
    elif k == 10:
        auto_focus.startFocus()
        # auto_focus.startFocus2()
        # auto_focus.auxiliaryFocusing()
        pass
    elif k == 32:
        focuser.set(Focuser.OPT_IRCUT,focuser.get(Focuser.OPT_IRCUT)^0x0001)
        pass
    elif k == ord('c'):
        #save image to file.
        cv2.imwrite("image{}.jpg".format(image_count), camera.getFrame())
        image_count += 1


def autotracking(camera, i2c_bus):
    focuser = Focuser(i2c_bus)
    auto_focus = AutoFocus(focuser,camera)
    

    k = 0
    cursor_x = 0
    cursor_y = 0

    # Loop where k is the last character pressed
    while (k != ord('q')):
        # Initialization
        # parser input key
        parseKey(k,focuser,auto_focus,camera)

def main():
    args = parse_cmdline()
    #open camera
    camera = Camera()
    #open camera preview
    camera.start_preview()

    autotracking(camera, args.i2c_bus)

    camera.stop_preview()
    camera.close()

    

if __name__ == "__main__":
    main()