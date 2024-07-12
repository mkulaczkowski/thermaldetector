import os
import cv2
import numpy as np

from cameras.base_camera import BaseCamera


class OpenCVVisibleCamera(BaseCamera):
    video_source = 0

    def __init__(self, rtsp_url):
        OpenCVVisibleCamera.set_video_source(rtsp_url)
        super(OpenCVVisibleCamera, self).__init__()

    @staticmethod
    def set_video_source(source):
        OpenCVVisibleCamera.video_source = source

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(OpenCVVisibleCamera.video_source)

        camera.set(cv2.CAP_PROP_BUFFERSIZE , 10)
        camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
        camera.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Creating a black frame with default resolution

        while True:
            # read current frame
            try:
                _, img = camera.read()

                # encode as a jpeg image and return it
                yield cv2.imencode('.jpg', img)[1].tobytes()
            except Exception as e:
                yield cv2.imencode('.jpg', black_frame)[1].tobytes()