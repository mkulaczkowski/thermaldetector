import logging
import os
import cv2
from vidgear.gears import VideoGear

from cameras.base_camera import BaseCamera
from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline
from cameras.opencv_visible_camera import visible_gstreamer_pipeline

logger = logging.getLogger('tester.sub')

class FusionCamera():
    video_source = visible_gstreamer_pipeline()
    video_source1 = thermal_gstreamer_pipeline()
    visible_camera = None
    thermal_camera = None

    def __init__(self):
        logger.debug('FusionCamera init')
        self.visible_camera = VideoGear(source=self.video_source, stabilize=False, stream_mode=True, framerate=25, logging=True, backend=cv2.CAP_GSTREAMER).start()
        self.thermal_camera = VideoGear(source=self.video_source1, stabilize=False, stream_mode=True, framerate=25, logging=True, backend=cv2.CAP_GSTREAMER).start()
        super(FusionCamera, self).__init__()

    def __del__(self):
        logger.debug('FusionCamera Stop')
        self.visible_camera.stop()
        self.thermal_camera.stop()

    def get_frame(self):
        while True:
            # read current frame
            outputFrame = self.visible_camera.read()

            # check for stabilized frame if Nonetype
            if outputFrame is None:
                break
            try:
                thermalFrame = self.thermal_camera.read()
                resized = cv2.resize(thermalFrame, (1920, 1080), interpolation=cv2.INTER_AREA)
                img_gray1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                ret, thresh1 = cv2.threshold(img_gray1, 150, 255, cv2.THRESH_BINARY)
                contours2, hierarchy2 = cv2.findContours(thresh1, cv2.RETR_TREE,
                                                         cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(outputFrame, contours2, -1, (0, 255, 0), 2, cv2.LINE_AA, offset=(0, 0))
            except Exception as e:
                logger.info('Fusion video feed Error: ' + str(e))
                continue

            # encode as a jpeg image and return it
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            yield cv2.imencode('.jpg', outputFrame, encode_param)[1].tobytes()