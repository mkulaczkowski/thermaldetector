import logging
import threading
import cv2
from deffcode import FFdecoder

# Define suitable parameters
ffparams = {
    "-rtsp_transport": "tcp",
    "-enforce_cv_patch": True,
    "-fflags" : "nobuffer"
}

class OpenCVVisibleCamera:
    def __init__(self, rtsp_url):
        logging.info(f'Initializing camera with URL: {rtsp_url}')
        self.capture = FFdecoder(rtsp_url, frame_format="bgr24", verbose=True, **ffparams).formulate()
        self.is_running = False
        self.frame = None


    def start(self):
        if not self.is_running:
            self.is_running = True

    def read(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.is_running = False

    def release(self):
        self.capture.terminate()

    def update(self):
        while self.is_running:
            frame = self.capture.read()
            with self.lock:
                self.frame = frame

    def __del__(self):
        self.stop()
        self.release()

    def frames(self):
        while self.is_running:

            # grab the BGR24 frames from decoder
            for frame in self.capture.generateFrame():
                if frame is None:
                    continue

                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield jpeg.tobytes()