import logging
import os
import cv2
from vidgear.gears import VideoGear

from cameras.base_camera import BaseCamera
from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline
from cameras.opencv_visible_camera import visible_gstreamer_pipeline

logger = logging.getLogger('tester.sub')

class VisibleCamera():
    video_source = visible_gstreamer_pipeline()

    def __init__(self):
        logger.debug('VisibleCamera init')
        self.visible_camera = VideoGear(source=self.video_source, stabilize=False, logging=True, backend=cv2.CAP_GSTREAMER)
        super(VisibleCamera, self).__init__()

    def __del__(self):
        logger.debug('VisibleCamera Stop')
        if self.visible_camera:
            self.visible_camera.stop()
    @staticmethod
    def set_video_source(source):
        VisibleCamera.video_source = source

    def get_frame(self):
        while True:
            # read current frame
            outputFrame = self.visible_camera.read()

            # check for stabilized frame if Nonetype
            if outputFrame is None:
                break
            # encode as a jpeg image and return it
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            yield cv2.imencode('.jpg', outputFrame, encode_param)[1].tobytes()