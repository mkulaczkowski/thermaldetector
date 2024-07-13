import threading
import numpy as np
import cv2
import subprocess as sp

class ThermalCamera:
    def __init__(self, rtsp_url):
        ffmpeg_options = "ffmpeg -rtsp_transport udp -i " + rtsp_url + " -fflags nobuffer -flags low_delay -strict experimental -fflags discardcorrupt -analyzeduration 0 -probesize 32 -flags +low_delay"
        print(ffmpeg_options)
        self.cap = cv2.VideoCapture(ffmpeg_options, cv2.CAP_FFMPEG)
        self.is_running = False
        # Set the buffer size to a smaller value to reduce latency
        # CAP_PROP_BUFFERSIZE property might not be supported by all backends
        # The value is in frames, so setting it to 1 or 2 can help reduce latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def start(self):
        if not self.is_running:
            self.is_running = True

    def stop(self):
        self.is_running = False

    def frames(self):

        # Check if the video capture is opened
        if not self.cap.isOpened():
            print("Error: Unable to open the RTSP stream.")
            return None

        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Creating a black frame with default resolution
        while self.is_running:
            ret, frame = self.cap.read()
            if frame is None:
                yield cv2.imencode('.jpg', black_frame)[1].tobytes()
            else:
                yield cv2.imencode('.jpg', frame)[1].tobytes()

# Example usage:
# camera = ThermalCamera(rtsp_url="your_rtsp_url_here", skip_frames=5)
# camera.start()
# for frame in camera.frames():
#     # process frame
# camera.stop()
