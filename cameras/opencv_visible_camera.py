import os
import cv2
from vidgear.gears import VideoGear
from cameras.base_camera import BaseCamera
def visible_gstreamer_pipeline(
        capture_width=1280,
        capture_height=720,
        display_width=1280,
        display_height=720,
        framerate=25,
        flip_method=2,
):
    pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink drop=1 max-buffers=1"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )
    return pipeline

class VisibleCamera():
    video_source = visible_gstreamer_pipeline()

    def __init__(self):
        print('VisibleCamera init')
        super(VisibleCamera, self).__init__()

    def get_frame(self):
        camera = cv2.VideoCapture(VisibleCamera.video_source, cv2.CAP_GSTREAMER)
        if not camera.isOpened():
            raise RuntimeError('Could not start visible camera.')

        while True:
            # read current frame
            frame_stab = camera.read()
            # check for stabilized frame if Nonetype
            if frame_stab is None:
                break
            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', frame_stab)[1].tobytes()