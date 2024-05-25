import os
import cv2
from cameras.base_camera import BaseCamera

def thermal_gstreamer_pipeline(
        capture_width=640,
        capture_height=480,
        display_width=720,
        display_height=480,
        framerate=25,
        flip_method=0,
):
    pipeline = f"rtsp://192.168.20.249:554/ONVIFMedia"
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
        self.thermal_camera = cv2.VideoCapture(ThermalCamera.video_source)
        if not self.thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')

        while True:
            # read current frame
            _, img = self.thermal_camera.read()

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()

