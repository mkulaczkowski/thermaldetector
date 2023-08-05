import time
import board

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3 as LSM6DS
from math import atan, atan2, degrees, pi, cos, sin
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
    offmag = (0, 0, 0)
    offaccel = (0, 0, 0)
    def __init__(self):
        print('Gyro init')
        super(Gyro, self).__init__()

    def vector_2_degrees(self, x, y):
        angle = degrees(atan2(y, x))
        if angle < 0:
            angle += 360
        return angle

    def get_heading(self):
        Xm, Ym, Zm = mag.magnetic
        Xm = Xm - Gyro.offmag[0]
        Ym = Ym - Gyro.offmag[1]
        Zm = Zm - Gyro.offmag[2]
        ax, ay, az = accel_gyro.acceleration
        ax = ax - Gyro.offaccel[0]
        ay = ay - Gyro.offaccel[1]
        az = az - Gyro.offaccel[2]

        # tilt compensation equations
        stableZ = az + (ax * 0.01)
        phi = atan2(ay, stableZ)

        Gz2 = ay * sin(phi) + az * cos(phi)
        theta = atan(-ax / Gz2)

        By2 = Zm * sin(phi) - Ym * cos(phi)
        Bz2 = Ym * sin(phi) + Zm * cos(phi)
        Bx3 = Xm * cos(theta) + Bz2 * sin(theta)

        return self.vector_2_degrees(Bx3, By2)

    def read_gyro(self):
        gyro = accel_gyro.gyro
        return gyro

    def read_accel(self):
        acceleration = accel_gyro.acceleration
        return acceleration

    def read_mag(self):
        magnetic = mag.magnetic
        return magnetic
