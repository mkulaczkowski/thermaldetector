import time
import board

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3 as LSM6DS

from adafruit_lis3mdl import LIS3MDL
import busio
i2c = busio.I2C(board.SCL_1, board.SDA_1)   # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
accel_gyro = LSM6DS(i2c)
mag = LIS3MDL(i2c)

while True:
    acceleration = accel_gyro.acceleration
    gyro = accel_gyro.gyro
    magnetic = mag.magnetic
    print(
        "Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(*acceleration)
    )
    print("Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*gyro))
    print("Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*magnetic))
    print("")
    time.sleep(0.5)