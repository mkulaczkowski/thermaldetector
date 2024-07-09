import logging
import os
import sys
import time
import threading
import numpy as np
import cv2
from vidgear.gears import CamGear


# also acts (partly) like a cv.VideoCapture
class FreshestFrame(threading.Thread):
    def __init__(self, capture, name='FreshestFrame'):
        self.capture = capture
        assert self.capture.isOpened()

        # this lets the read() method block until there's a new frame
        self.cond = threading.Condition()

        # this allows us to stop the thread gracefully
        self.running = False

        # keeping the newest frame around
        self.frame = None

        # passing a sequence number allows read() to NOT block
        # if the currently available one is exactly the one you ask for
        self.latestnum = 0

        # this is just for demo purposes
        self.callback = None

        super().__init__(name=name)
        self.start()

    def start(self):
        self.running = True
        super().start()

    def release(self, timeout=None):
        self.running = False
        self.join(timeout=timeout)
        self.capture.release()

    def run(self):
        counter = 0
        while self.running:
            # block for fresh frame
            (rv, img) = self.capture.read()
            assert rv
            counter += 1

            # publish the frame
            with self.cond:  # lock the condition for this operation
                self.frame = img if rv else None
                self.latestnum = counter
                self.cond.notify_all()

            if self.callback:
                self.callback(img)

    def read(self, wait=True, seqnumber=None, timeout=None):
        # with no arguments (wait=True), it always blocks for a fresh frame
        # with wait=False it returns the current frame immediately (polling)
        # with a seqnumber, it blocks until that frame is available (or no wait at all)
        # with timeout argument, may return an earlier frame;
        #   may even be (0,None) if nothing received yet

        with self.cond:
            if wait:
                if seqnumber is None:
                    seqnumber = self.latestnum + 1
                if seqnumber < 1:
                    seqnumber = 1

                rv = self.cond.wait_for(lambda: self.latestnum >= seqnumber, timeout=timeout)
                if not rv:
                    return (self.latestnum, self.frame)

            return (self.latestnum, self.frame)


class TestOpenCVVisibleCamera:
    def __init__(self, rtsp_url):
        # Initialize video capture only once in the constructor
        logging.info(f'Camera {rtsp_url}')
        self.capture = cv2.VideoCapture(rtsp_url)
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
        cnt = 0
        while self.is_running:
            frame = FreshestFrame(self.capture)

            t0 = time.perf_counter()
            cnt, img = frame.read(seqnumber=cnt + 1)
            dt = time.perf_counter() - t0
            if dt > 0.010:  # 10 milliseconds
                print("NOTICE: read() took {dt:.3f} secs".format(dt=dt))

            # let's pretend we need some time to process this frame
            print("processing {cnt}...".format(cnt=cnt), end=" ", flush=True)

            if img is not None:
                ret, jpeg = cv2.imencode('.jpg', img)
                if ret:
                    yield jpeg.tobytes()

