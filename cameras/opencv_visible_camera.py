import os
import cv2

def visible_gstreamer_pipeline(
        capture_width=1920,
        capture_height=1080,
        display_width=1920,
        display_height=1080,
        framerate=25,
):
    video_source = "rtsp://192.168.20.94:554/user=admin_password=oTyLhoPM_channel=1_stream=0&onvif=0.sdp?real_stream"
    pipeline = (
            f"rtspsrc location={video_source} ! rtph264depay ! avdec_h264 ! videoconvert ! appsink name=sink"
            # % (
            #     capture_width,
            #     capture_height,
            #     framerate,
            # )
    )
    return video_source

class VisibleCamera:
    video_source = visible_gstreamer_pipeline()

    def __init__(self):
        # Initialize video capture only once in the constructor
        #self.visible_camera = cv2.VideoCapture(VisibleCamera.video_source, cv2.CAP_GSTREAMER)
        self.visible_camera = cv2.VideoCapture("rtsp://192.168.20.94:554/user=admin_password=oTyLhoPM_channel=1_stream=0&onvif=0.sdp?real_stream")
        if not self.visible_camera.isOpened():
            raise RuntimeError('Could not start visible camera.')

    def __del__(self):
        # Release the video capture object when the instance is destroyed
        if self.visible_camera.isOpened():
            self.visible_camera.release()

    def get_frame(self):
        while True:
            # Read current frame
            ret, frame_stab = self.visible_camera.read()
            if not ret:
                # Break the loop if the frame could not be read
                break
            # Encode as a jpeg image and yield the byte array
            ret, jpeg = cv2.imencode('.jpg', frame_stab)
            if not ret:
                # Break the loop if the frame could not be encoded
                break
            yield jpeg.tobytes()