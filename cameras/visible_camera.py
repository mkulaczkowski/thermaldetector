import logging
import os
import cv2
import nanocamera

from cameras.opencv_visible_camera import visible_gstreamer_pipeline

logger = logging.getLogger('tester.sub')

class VisibleCamera():
    video_source = visible_gstreamer_pipeline()

    def __init__(self):
        logger.debug('VisibleCamera init')
        self.visible_camera = nanocamera.Camera(flip=2, device_id=0, width=1920, height=1080, fps=25, enforce_fps=True)
        super(VisibleCamera, self).__init__()

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

        self.visible_camera.release()