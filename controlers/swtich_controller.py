try:
    import Jetson.GPIO as GPIO
except ImportError as e:
    print(e)
    print("Failed to import Jetson.GPIO library")

import time

switch_camera = 23
switch_laser = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(switch_camera, GPIO.OUT)
GPIO.setup(switch_laser, GPIO.OUT)
GPIO.output(switch_camera, GPIO.LOW)
GPIO.output(switch_laser, GPIO.LOW)

class GPIO_switch():

    def __init__(self):
        print('GPIO init')
        super(GPIO_switch, self).__init__()
    # BCM pin-numbering scheme from Raspberry Pi
    # set pin as an output pin with optional initial state of HIGH

    def thermal_camera_on(self):
        GPIO.output(switch_camera, GPIO.HIGH)

    def thermal_camera_restart(self):
        GPIO.output(switch_camera, GPIO.LOW)
        time.sleep(5)
        GPIO.output(switch_camera, GPIO.HIGH)

    def laser_on(self):
        GPIO.output(switch_laser, GPIO.HIGH)

    def thermal_camera_off(self):
        GPIO.output(switch_camera, GPIO.LOW)

    def laser_off(self):
        GPIO.output(self.switch_laser, GPIO.LOW)
