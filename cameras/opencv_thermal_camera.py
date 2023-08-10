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
    pipeline = f"v4l2src device=/dev/video1 ! video/x-raw, format=YUY2, width={capture_width}, height={capture_height}, pixel-aspect-ratio=1/1, framerate={framerate}/1 ! videoconvert ! appsink drop=1 max-buffers=1"
    print(pipeline)
    return (pipeline)

class ThermalCamera():
    video_source = thermal_gstreamer_pipeline()
    thermal_camera = None
    def __init__(self):
        print('Thermal init')
        super(ThermalCamera, self).__init__()
    def __del__(self):
        try:
            self.thermal_camera.release()
        except:
            print('probably theres no cap yet :(')
        cv2.destroyAllWindows()
    def get_frame(self):
        self.thermal_camera = cv2.VideoCapture(ThermalCamera.video_source, cv2.CAP_GSTREAMER)
        if not self.thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')

        while True:
            # read current frame
            _, img = self.thermal_camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()

