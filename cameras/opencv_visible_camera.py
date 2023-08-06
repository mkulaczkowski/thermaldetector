import os
import cv2
from cameras.base_camera import BaseCamera
def visible_gstreamer_pipeline(
        capture_width=3840,
        capture_height=2160,
        display_width=1920,
        display_height=1080,
        framerate=25,
        flip_method=2,
):
    pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "omxh264enc ! qtmux ! appsink drop=1"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method
            )
    )
    # pipeline = (
    #         "nvarguscamerasrc ! "
    #         "video/x-raw(memory:NVMM), "
    #         "width=(int)%d, height=(int)%d, "
    #         "format=(string)NV12, framerate=(fraction)%d/1 ! "
    #         "nvvidconv flip-method=%d ! "
    #         "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
    #         "videoconvert ! "
    #         "video/x-raw, format=(string)BGR ! appsink drop=1"
    #         % (
    #             capture_width,
    #             capture_height,
    #             framerate,
    #             flip_method,
    #             display_width,
    #             display_height,
    #         )
    # )
    return pipeline

class VisibleCamera(BaseCamera):
    video_source = visible_gstreamer_pipeline()

    def __init__(self):
        print('VisibleCamera init')
        super(VisibleCamera, self).__init__()

    @staticmethod
    def frames():
        cv2.destroyAllWindows()
        camera = cv2.VideoCapture(VisibleCamera.video_source, cv2.CAP_GSTREAMER)
        if not camera.isOpened():
            raise RuntimeError('Could not start visible camera.')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()