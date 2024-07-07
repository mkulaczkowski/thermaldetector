import os
import time

import cv2
import threading

def visible_gstreamer_pipeline(
        rtsp_url,
        capture_width=1920,
        capture_height=1080,
        framerate=30,
):
    # Define the GStreamer pipeline
    # gst_pipeline = (
    #     f"rtspsrc location={rtsp_url} latency=0 ! "
    #     f"rtph264depay ! h264parse ! nvv4l2decoder ! "
    #     f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, format=(string)NV12 ! "
    #     f"videoconvert ! video/x-raw, format=(string)BGR ! appsink"
    # )

    gst_pipeline = (f"rtspsrc location={rtsp_url} latency=0 ! "
        f"rtph264depay ! h264parse ! nvv4l2decoder ! "
        f"video/x-raw, width=(int){capture_width}, height=(int){capture_height}, format=(string)BGRx ! "
        f"videoconvert ! video/x-raw, format=(string)BGR ! appsink"
                    )
    print(gst_pipeline)
    return gst_pipeline

class VisibleCamera:
    def __init__(self, rtsp_url):
        # Initialize video capture only once in the constructor
        self.capture = cv2.VideoCapture(visible_gstreamer_pipeline(rtsp_url), cv2.CAP_GSTREAMER)
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
