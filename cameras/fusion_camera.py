import logging
import os
import time

import cv2


from cameras.opencv_thermal_camera import thermal_gstreamer_pipeline
from cameras.opencv_visible_camera import visible_gstreamer_pipeline

logger = logging.getLogger('tester.sub')


class FusionCamera:
    def __init__(self, visible_camera_source=visible_gstreamer_pipeline(), thermal_camera_source=thermal_gstreamer_pipeline()):
        self.visible_camera = cv2.VideoCapture(visible_camera_source)
        self.thermal_camera = cv2.VideoCapture(thermal_camera_source)
        if not self.visible_camera.isOpened():
            raise RuntimeError('Could not start visible camera.')
        if not self.thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')
        self.prev_frame_time = time.time()
        self.new_frame_time = time.time()

    def __del__(self):
        if self.visible_camera.isOpened():
            self.visible_camera.release()
        if self.thermal_camera.isOpened():
            self.thermal_camera.release()

    def get_frame(self):
        while True:
            # Read current frame from visible camera
            ret_visible, outputFrame = self.visible_camera.read()
            if not ret_visible or outputFrame is None:
                logger.info('No frame received from visible camera.')
                break

            # Read current frame from thermal camera
            ret_thermal, thermalFrame = self.thermal_camera.read()
            if not ret_thermal or thermalFrame is None:
                logger.info('No frame received from thermal camera.')
                continue

            try:
                # Resize thermal frame and convert to grayscale
                resized = cv2.resize(thermalFrame, (1920, 1080), interpolation=cv2.INTER_AREA)
                img_gray1 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                ret, thresh1 = cv2.threshold(img_gray1, 150, 255, cv2.THRESH_BINARY)

                # Find contours and draw them on the output frame
                contours2, _ = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(outputFrame, contours2, -1, (0, 255, 0), 2, cv2.LINE_AA)

            except Exception as e:
                logger.info('Fusion video feed Error: ' + str(e))
                continue

            # Calculate FPS
            self.new_frame_time = time.time()
            fps = 1 / (self.new_frame_time - self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time

            # Convert FPS to string and put on frame
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(outputFrame, fps_text, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

            # Encode as a JPEG image and return it
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            ret, jpeg = cv2.imencode('.jpg', outputFrame, encode_param)
            if not ret:
                logger.info('Failed to encode frame to JPEG.')
                continue

            yield jpeg.tobytes()


class VisibleThermalCamera:
    def __init__(self,  visible_camera_source=visible_gstreamer_pipeline(), thermal_camera_source=thermal_gstreamer_pipeline()):
        self.visible_camera = cv2.VideoCapture(visible_camera_source)
        self.thermal_camera = cv2.VideoCapture(thermal_camera_source)
        if not self.visible_camera.isOpened():
            raise RuntimeError('Could not start visible camera.')
        if not self.thermal_camera.isOpened():
            raise RuntimeError('Could not start thermal camera.')
        self.prev_frame_time = time.time()
        self.new_frame_time = time.time()

    def __del__(self):
        if self.visible_camera.isOpened():
            self.visible_camera.release()
        if self.thermal_camera.isOpened():
            self.thermal_camera.release()

    def get_frame(self):
        while True:
            # Read current frame from visible camera
            ret_visible, visible_frame = self.visible_camera.read()
            if not ret_visible or visible_frame is None:
                logger.info('No frame received from visible camera.')
                break

            # Read current frame from thermal camera
            ret_thermal, thermal_frame = self.thermal_camera.read()
            if not ret_thermal or thermal_frame is None:
                logger.info('No frame received from thermal camera.')
                continue

            try:
                # Resize thermal frame to match the size of the visible frame
                thermal_frame_resized = cv2.resize(thermal_frame, (visible_frame.shape[1], visible_frame.shape[0]))

                # Blend the frames with 50% transparency
                blended_frame = cv2.addWeighted(visible_frame, 0.5, thermal_frame_resized, 0.5, 0)

            except Exception as e:
                logger.info('Fusion video feed Error: ' + str(e))
                continue

            # Calculate FPS
            self.new_frame_time = time.time()
            fps = 1 / (self.new_frame_time - self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time

            # Convert FPS to string and put on frame
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(blended_frame, fps_text, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

            # Encode as a JPEG image and return it
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            ret, jpeg = cv2.imencode('.jpg', blended_frame, encode_param)
            if not ret:
                logger.info('Failed to encode frame to JPEG.')
                continue

            yield jpeg.tobytes()