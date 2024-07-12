import os
import time

import cv2
import threading
import logging
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

    gst_pipeline = (
        f"rtspsrc location={rtsp_url} ! "
        "rtph264depay ! "
        "h264parse ! "
        "nvv4l2decoder ! "
        "videoconvert ! "
        "appsink"
    )

    gst_pipeline = (f"rtspsrc location={rtsp_url} latency=0 ! "
        f"rtph264depay ! h264parse ! nvv4l2decoder ! "
        f"video/x-raw, width=(int){capture_width}, height=(int){capture_height}, format=(string)BGRx ! "
        f"videoconvert ! video/x-raw, format=(string)BGR ! appsink"
                    )
    print(gst_pipeline)
    return gst_pipeline



class OpenCVVisibleCamera:
    def __init__(self, rtsp_url):
        # Initialize video capture only once in the constructor
        logging.info(f'Camera {rtsp_url}')
        self.capture = cv2.VideoCapture(rtsp_url)
        logging.info(f'Camera CAP {self.capture.get(cv2.CAP_PROP_BUFFERSIZE)}')
        thread = threading.Thread(target=self.rtsp_cam_buffer, args=(), name="rtsp_read_thread")
        thread.daemon = True
        thread.start()

    def rtsp_cam_buffer(self):
        while True:
            with self.lock:
                self.last_ready = self.capture.grab()

    def getFrame(self):
        if (self.last_ready is not None):
            self.last_ready, self.last_frame = self.capture.retrieve()
            return self.last_frame.copy()
        else:
            return -1

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.update, daemon=True)
            self.thread.start()

    def read(self):
        with self.read_lock:
            frame = self.frame.copy() if self.frame is not None else None
        return frame

    def stop(self):
        self.is_running = False
        if self.thread.is_alive():
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
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield frame
