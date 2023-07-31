import os
import cv2

from cameras.base_camera import BaseCamera
from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline
from cameras.opencv_visible_camera import visible_gstreamer_pipeline


class FusionCamera(BaseCamera):
    video_source = visible_gstreamer_pipeline()
    video_source1 = thermal_gstreamer_pipeline()

    def __init__(self):
        print('FusionCamera init')
        super(FusionCamera, self).__init__()

    @staticmethod
    def set_video_source(source):
        FusionCamera.video_source = source

    @staticmethod
    def frames():
        visible_camera = cv2.VideoCapture(FusionCamera.video_source, cv2.CAP_GSTREAMER)
        thermal_camera = cv2.VideoCapture(FusionCamera.video_source1, cv2.CAP_GSTREAMER)
        if not visible_camera.isOpened():
            raise RuntimeError('Could not start visible camera.')

        if not thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')

        while True:
            # read current frame
            ret, outputFrame = visible_camera.read()
            ret2, thermalFrame = thermal_camera.read()

            resized = cv2.resize(thermalFrame, (1280, 853), interpolation=cv2.INTER_AREA)
            img_gray1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            ret, thresh1 = cv2.threshold(img_gray1, 150, 255, cv2.THRESH_BINARY)
            contours2, hierarchy2 = cv2.findContours(thresh1, cv2.RETR_TREE,
                                                     cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(outputFrame, contours2, -1, (0, 255, 0), 2, cv2.LINE_AA)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', outputFrame)[1].tobytes()