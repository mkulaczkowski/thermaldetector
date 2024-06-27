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
    pipeline = f"rtsp://192.168.20.6:554/ONVIFMedia"
    print(pipeline)
    return (pipeline)

class ThermalCamera():
    video_source = thermal_gstreamer_pipeline()
    thermal_camera = None
    def __init__(self):
        print('Thermal init')
        self.thermal_camera = cv2.VideoCapture(ThermalCamera.video_source, cv2.CAP_FFMPEG)

        if not self.thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')

        super(ThermalCamera, self).__init__()
    def __del__(self):
        try:
            self.thermal_camera.release()
        except:
            print('probably theres no cap yet :(')
        cv2.destroyAllWindows()
    def get_frame(self):
        while True:
            # Read current frame
            ret, frame_stab = self.thermal_camera.read()
            if not ret:
                # Break the loop if the frame could not be read
                break
            # Encode as a jpeg image and yield the byte array
            ret, jpeg = cv2.imencode('.jpg', frame_stab)
            if not ret:
                # Break the loop if the frame could not be encoded
                break
            yield jpeg.tobytes()

