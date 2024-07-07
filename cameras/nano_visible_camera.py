import os
import time

import cv2
import threading

import os
import time
import threading
from nanocamera import Camera


class VisibleCamera:
    def __init__(self, rtsp_url, capture_width=640, capture_height=480, fps=25):
        # Initialize the NanoCamera
        self.camera = Camera(
            camera_type=2,
            source=rtsp_url,     # RTSP URL
            width=capture_width,
            height=capture_height,
            fps=fps
        )
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
        self.camera.release()

    def update(self):
        while self.is_running:
            frame = self.camera.read()
            with self.read_lock:
                if frame is not None:
                    self.frame = frame
                else:
                    self.is_running = False

    def __del__(self):
        # Release the NanoCamera object when the instance is destroyed
        self.stop()
        self.release()

    def get_frame(self):
        while self.is_running:
            frame = self.read()
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield jpeg.tobytes()

