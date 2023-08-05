import time
import board

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3 as LSM6DS

from adafruit_lis3mdl import LIS3MDL
import busio


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
    i2c = busio.I2C(board.SCL_1, board.SDA_1)
    accel_gyro = LSM6DS(i2c)
    mag = LIS3MDL(i2c)

    def __init__(self):
        pass

    def read_gyro(self):
        gyro = Gyro.accel_gyro.gyro
        return gyro

    def read_accel(self):
        acceleration = Gyro.accel_gyro.acceleration
        return acceleration

    def read_mag(self):
        magnetic = Gyro.mag.magnetic
        return magnetic
