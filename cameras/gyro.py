import time
import board

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3 as LSM6DS
from math import atan2, degrees
from adafruit_lis3mdl import LIS3MDL
import busio

i2c = busio.I2C(board.SCL_1, board.SDA_1)
accel_gyro = LSM6DS(i2c)
mag = LIS3MDL(i2c)


# while True:
#
#     magnetic = mag.magnetic
#     print(
#         "Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(*acceleration)
#     )
#     print("Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*gyro))
#     print("Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*magnetic))
#     print("")
#     time.sleep(0.5)
#
#
class Gyro:

    def __init__(self):
        print('Gyro init')
        super(Gyro, self).__init__()

    def vector_2_degrees(self, x, y):
        angle = degrees(atan2(y, x))
        if angle < 0:
            angle += 360
        return angle

    def get_heading(self):
        magnet_x, magnet_y, magnet_z = mag.magnetic
        return self.vector_2_degrees(magnet_x, magnet_y)

    def read_gyro(self):
        gyro = accel_gyro.gyro
        return gyro

    def read_accel(self):
        acceleration = accel_gyro.acceleration
        return acceleration

    def read_mag(self):
        magnetic = mag.magnetic
        return magnetic
