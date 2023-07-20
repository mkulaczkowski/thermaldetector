import cv2
import numpy as np
from Focuser import Focuser
import time

# Frame Size. Smaller is faster, but less accurate.
# Wide and short is better, since moving your head up and down is harder to do.
# W = 160 and H = 100 are good settings if you are using and earlier Raspberry Pi Version.
FRAME_W = 640
FRAME_H = 480
image_scale = 1.3


def gstreamer_pipeline(
        capture_width=FRAME_W,
        capture_height=FRAME_H,
        display_width=FRAME_W,
        display_height=FRAME_H,
        framerate=10,
        flip_method=0,
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


def faceDetect():
    print('Focuser Start')
    focuser = Focuser(1)
    focuser.set(Focuser.OPT_MOTOR_X, 90)
    time.sleep(2)
    focuser.set(Focuser.OPT_MOTOR_Y, 90)
    # Obtain device infomation
    focus_value = "Focus    : {}".format(focuser.get(Focuser.OPT_FOCUS))
    zoom_value = "Zoom     : {}".format(focuser.get(Focuser.OPT_ZOOM))
    motor_x_val = "MotorX   : {}".format(focuser.get(Focuser.OPT_MOTOR_X))
    motor_y_val = "MotorY   : {}".format(focuser.get(Focuser.OPT_MOTOR_Y))
    ircut_val = "IRCUT    : {}".format(focuser.get(Focuser.OPT_IRCUT))
    print(focus_value)
    print(zoom_value)
    print(motor_y_val)
    print(motor_x_val)

    cam_pan = focuser.get(Focuser.OPT_MOTOR_X)
    cam_tilt = focuser.get(Focuser.OPT_MOTOR_Y)

    # Obtain face detection Haar cascade XML files from OpenCV
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    # Video Capturing class from OpenCV
    video_capture = cv2.VideoCapture(gstreamer_pipeline(flip_method=2), cv2.CAP_GSTREAMER)
    if video_capture.isOpened():
        cv2.namedWindow("Face Detection Window", cv2.WINDOW_AUTOSIZE)

        while True:
            return_key, image = video_capture.read()
            # image=cv2.flip(image,-1)
            if not return_key:
                break

            grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            detected_faces = face_cascade.detectMultiScale(grayscale_image, scaleFactor=image_scale, minNeighbors=1,
                                                           minSize=[15, 15])
            midFace = None
            for (x, y, w, h) in detected_faces:
                pt1 = (int(x), int(y))
                pt2 = (int((x + w)), int((y + h)))
                cv2.rectangle(image, pt1, pt2, (0, 0, 0), 2)
                # get the xy corner co-ords, calc the midFace location
                x1 = pt1[0]
                x2 = pt2[0]
                y1 = pt1[1]
                y2 = pt2[1]

                midFaceX = x1 + ((x2 - x1) / 2)
                midFaceY = y1 + ((y2 - y1) / 2)
                midFace = (midFaceX, midFaceY)

                offsetX = midFaceX / float(FRAME_W / 2)
                offsetY = midFaceY / float(FRAME_H / 2)
                offsetX -= 1
                offsetY -= 1

                cam_pan -= (offsetX * 8)
                cam_tilt -= (offsetY * 3)
                focuser.set(Focuser.OPT_MOTOR_X, int(cam_pan))
                print(offsetX, offsetY, midFace, cam_pan, cam_tilt)
                time.sleep(0.01)
                focuser.set(Focuser.OPT_MOTOR_Y, int(cam_tilt))
                break

            cv2.imshow("Face Detection Window", image)

            key = cv2.waitKey(30) & 0xff
            # Stop the program on the ESC key
            if key == 27:
                break

        video_capture.release()
        cv2.destroyAllWindows()
    else:
        print("Cannot open Camera")


if __name__ == "__main__":
    faceDetect()
