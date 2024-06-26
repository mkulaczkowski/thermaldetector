import os
import threading
import time

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

    def __init__(self):
        # Initialize video capture only once in the constructor
        #self.visible_camera = cv2.VideoCapture(VisibleCamera.video_source, cv2.CAP_GSTREAMER)
        self.capture = cv2.VideoCapture(self.video_source, cv2.CAP_GSTREAMER)
        self.is_running = False
        self.read_lock = threading.Lock()
        self.frame = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.start()

    def read(self):
        with self.read_lock:
            frame = self.frame.copy() if self.frame is not None else None
        return frame

    def stop(self):
        self.is_running = False
        self.thread.join()

    def release(self):
        self.capture.release()

    def update(self):
        while self.is_running:
            ret, frame = self.capture.read()
            with self.read_lock:
                if ret:
                    self.frame = frame
                else:
                    self.is_running = False

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
            time.sleep(0.03)
