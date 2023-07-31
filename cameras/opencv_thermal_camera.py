import os
import cv2
from cameras.base_camera import BaseCamera

def thermal_gstreamer_pipeline(
        capture_width=480,
        capture_height=320,
        display_width=720,
        display_height=480,
        framerate=25,
        flip_method=0,
):
    pipeline = f"v4l2src device=/dev/video1 ! video/x-raw, format=YUY2, width={capture_width}, height={capture_height}, pixel-aspect-ratio=1/1, framerate={framerate}/1 ! videoconvert ! appsink name=thermal_sink"
    print(pipeline)
    return (pipeline)

class ThermalCamera(BaseCamera):
    video_source = thermal_gstreamer_pipeline()

    def __init__(self):
        if os.environ.get('OPENCV_CAMERA_SOURCE'):
            ThermalCamera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
        super(ThermalCamera, self).__init__()

    @staticmethod
    def set_video_source(source):
        ThermalCamera.video_source = source

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(ThermalCamera.video_source, cv2.CAP_GSTREAMER)
        if not camera.isOpened():
            raise RuntimeError('Could not start visible camera.')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()