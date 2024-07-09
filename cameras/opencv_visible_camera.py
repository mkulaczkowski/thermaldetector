import os
import time
from vidgear.gears import CamGear
import cv2
import threading
import logging




class OpenCVVisibleCamera:
    def __init__(self, rtsp_url):
        # Initialize video capture only once in the constructor
        logging.info(f'Camera {rtsp_url}')
        self.capture = CamGear(source=rtsp_url, backend=cv2.CAP_FFMPEG).start()
        self.is_running = False
        self.frame = None

    def start(self):
        if not self.is_running:
            self.is_running = True

    def read(self):
        return self.capture.read()

    def stop(self):
        self.is_running = False

    def release(self):
        self.capture.stop()

    def update(self):
        while self.is_running:
            self.frame = self.capture.read()

    def __del__(self):
        # Release the video capture object when the instance is destroyed
        self.stop()
        self.release()

    def get_frame(self):
        while self.is_running:
            frame = self.read()
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield jpeg.tobytes()
