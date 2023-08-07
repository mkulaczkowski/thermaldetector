import logging
import os
import cv2


from cameras.base_camera import BaseCamera
from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline
from cameras.opencv_visible_camera import visible_gstreamer_pipeline

logger = logging.getLogger('tester.sub')

class FusionCamera(BaseCamera):
    video_source = visible_gstreamer_pipeline()
    video_source1 = thermal_gstreamer_pipeline()

    def __init__(self):
        logger.debug('FusionCamera init')
        super(FusionCamera, self).__init__()

    @staticmethod
    def set_video_source(source):
        FusionCamera.video_source = source

    @staticmethod
    def get_video_sources():
        tries = 3
        for i in range(tries):
            try:
                visible_camera = cv2.VideoCapture(FusionCamera.video_source, cv2.CAP_GSTREAMER)
                thermal_camera = cv2.VideoCapture(FusionCamera.video_source1, cv2.CAP_GSTREAMER)

                assert visible_camera.isOpened()
                assert thermal_camera.isOpened()
            
                return visible_camera, thermal_camera
            except AssertionError as e:
                if i < tries - 1:  # i is zero indexed
                    logger.warning('Fusion video feed Error: ' + str(e))
                    cv2.destroyAllWindows()
                    continue
                else:
                    raise
            break

    @staticmethod
    def frames():
        visible_camera, thermal_camera = FusionCamera.get_video_sources()

        while True:
            # read current frame
            ret, outputFrame = visible_camera.read()

            try:
                ret2, thermalFrame = thermal_camera.read()
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