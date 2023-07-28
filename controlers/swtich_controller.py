import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)


class GPIO_switch():
    switch_camera = 23
    switch_laser = 21

    def __init__(self):
        GPIO.setup(self.switch_camera, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.switch_laser, GPIO.OUT, initial=GPIO.LOW)

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
