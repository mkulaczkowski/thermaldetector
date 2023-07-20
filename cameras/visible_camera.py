import cv2
import time

try:
    from Queue import Queue
except ModuleNotFoundError:
    from queue import Queue

import threading
import signal
import sys


def visible_gstreamer_pipeline(
        capture_width=3840,
        capture_height=2160,
        display_width=1280,
        display_height=720,
        framerate=30,
        flip_method=2,
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


def thermal_gstreamer_pipeline(
        capture_width=640,
        capture_height=480,
        display_width=640,
        display_height=480,
        framerate=30,
        flip_method=0,
):
    return (
            "v4l2src device=/dev/video1 ! "
            "video/x-raw, "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


class FrameReader(threading.Thread):
    queues = []
    _running = True
    camera = None

    def __init__(self, camera, name):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera

    def run(self):
        while self._running:
            _, frame = self.camera.read()
            while self.queues:
                queue = self.queues.pop()
                queue.put(frame)

    def addQueue(self, queue):
        self.queues.append(queue)

    def getFrame(self, timeout=None):
        queue = Queue(1)
        self.addQueue(queue)
        return queue.get(timeout=timeout)

    def stop(self):
        self._running = False


class Previewer(threading.Thread):
    window_name = "Arducam"
    _running = True
    camera = None

    def __init__(self, camera, name):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera

    def run(self):
        self._running = True
        while self._running:
            cv2.imshow(self.window_name, self.camera.getFrame(2000))
            keyCode = cv2.waitKey(16) & 0xFF
        cv2.destroyWindow(self.window_name)

    def start_preview(self):
        self.start()

    def stop_preview(self):
        self._running = False


class Camera(object):
    frame_reader = None
    cap = None
    previewer = None
    pipeline = None

    def __init__(self, source='visible'):
        if source == 'visible':
            self.pipeline = visible_gstreamer_pipeline()
        else:
            self.pipeline = thermal_gstreamer_pipeline()
        self.open_camera()

    def open_camera(self):
        self.cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera!")
        if self.frame_reader == None:
            self.frame_reader = FrameReader(self.cap, "")
            self.frame_reader.daemon = True
            self.frame_reader.start()
        self.previewer = Previewer(self.frame_reader, "")

    def getFrame(self):
        return self.frame_reader.getFrame()

    def start_preview(self):
        self.previewer.daemon = True
        self.previewer.start_preview()

    def stop_preview(self):
        self.previewer.stop_preview()
        self.previewer.join()

    def close(self):
        self.frame_reader.stop()
        self.cap.release()


if __name__ == "__main__":
    camera = Camera()
    camera.start_preview()
    time.sleep(10)
    camera.stop_preview()
    camera.close()
