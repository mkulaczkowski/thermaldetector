import RPi.GPIO as GPIO
import time

# Pin Definitions
input_pin = 21  # BCM pin 18, BOARD pin 12
# Pin Definitions
output_pin = 21  # BCM pin 18, BOARD pin 12


class GPIO_switch():
    switch_camera = 21
    switch_laser = 20

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)  # BCM pin-numbering scheme from Raspberry Pi
        # set pin as an output pin with optional initial state of HIGH
        GPIO.setup(self.switch_camera, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.switch_laser, GPIO.OUT, initial=GPIO.LOW)

    def thermal_camera_on(self):
        GPIO.output(self.switch_camera, GPIO.HIGH)

    def laser_on(self):
        GPIO.output(self.switch_laser, GPIO.HIGH)

    def thermal_camera_off(self):
        GPIO.output(self.switch_camera, GPIO.LOW)

    def laser_off(self):
        GPIO.output(self.switch_laser, GPIO.LOW)