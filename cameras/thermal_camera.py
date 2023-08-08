import logging
import os
import cv2
import nanocamera

from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline

logger = logging.getLogger('tester.sub')

class ThermalCamera():
    video_source = thermal_gstreamer_pipeline()
    thermal_camera = None

    def __init__(self):
        logger.debug('Thermal init')
        self.thermal_camera = nanocamera.Camera(camera_type=1, device_id=1, width=480, height=320, fps=25, enforce_fps=True)
        super(ThermalCamera, self).__init__()

    def get_frame(self):
        while True:
            # read current frame
            outputFrame = self.thermal_camera.read()

            # check for stabilized frame if Nonetype
            if outputFrame is None:
                break
            # encode as a jpeg image and return it
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            yield cv2.imencode('.jpg', outputFrame, encode_param)[1].tobytes()

        self.thermal_camera.release()