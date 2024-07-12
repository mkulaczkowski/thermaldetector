import threading
import time
import cv2

def thermal_gstreamer_pipeline(
        rtsp_url,
        capture_width=720,
        capture_height=576,
        framerate=25,
        flip_method=0,
):
    gst_pipeline = (
        f"rtspsrc location={rtsp_url} latency=0 ! "
        f"rtph264depay ! h264parse ! nvv4l2decoder ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, format=(string)NV12 ! "
        f"videoconvert ! video/x-raw, format=(string)BGR ! appsink"
    )
    print(gst_pipeline)
    return gst_pipeline

class ThermalCamera:

    def __init__(self, rtsp_url):
        self.capture = cv2.VideoCapture(thermal_gstreamer_pipeline(rtsp_url), cv2.CAP_GSTREAMER)
        self.is_running = False
        self.read_lock = threading.Lock()
        self.frame = None

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
            if not ret:
                self.is_running = False
                break
            with self.read_lock:
                self.frame = frame

    def __del__(self):
        self.stop()
        self.release()

    def get_frame(self):
        while self.is_running:
            frame = self.read()
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield jpeg.tobytes()


# Example usage:
# camera = ThermalCamera()
# camera.start()
# for frame in camera.get_frame():
#     # process frame
# camera.stop()
