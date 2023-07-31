import Jetson.GPIO as GPIO
import time

switch_camera = 23
switch_laser = 21

GPIO.setmode(GPIO.BOARD)
GPIO.setup(switch_camera, GPIO.OUT)
GPIO.setup(switch_laser, GPIO.OUT)

class GPIO_switch():

    def __init__(self):
        print('GPIO_switch init')
    def thermal_camera_on(self):
        GPIO.output(switch_camera, GPIO.HIGH)

    def thermal_camera_restart(self):
        GPIO.output(switch_camera, GPIO.LOW)
        time.sleep(5)
        GPIO.output(switch_camera, GPIO.HIGH)

    def laser_on(self):
        GPIO.output(switch_laser, GPIO.HIGH)

    def thermal_camera_off(self):
        GPIO.output(self.switch_camera, GPIO.LOW)

    def laser_off(self):
        GPIO.output(self.switch_laser, GPIO.LOW)
