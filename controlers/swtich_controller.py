try:
    import Jetson.GPIO as GPIO
except ImportError as e:
    print(e)
    print("Failed to import Jetson.GPIO library, using dummy GPIO")
    from Mock.GPIO import GPIO

import time


class GPIO_switch():
    switch_camera = 23
    switch_laser = 21
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.switch_camera, GPIO.OUT)
        GPIO.setup(self.switch_laser, GPIO.OUT)

    # BCM pin-numbering scheme from Raspberry Pi
    # set pin as an output pin with optional initial state of HIGH

    def thermal_camera_on(self):
        GPIO.output(self.switch_camera, GPIO.HIGH)

    def thermal_camera_restart(self):
        GPIO.output(self.switch_camera, GPIO.LOW)
        time.sleep(5)
        GPIO.output(self.switch_camera, GPIO.HIGH)

    def laser_on(self):
        GPIO.output(self.switch_laser, GPIO.HIGH)

    def thermal_camera_off(self):
        GPIO.output(self.switch_camera, GPIO.LOW)

    def laser_off(self):
        GPIO.output(self.switch_laser, GPIO.LOW)
