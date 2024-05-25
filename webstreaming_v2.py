import cv2
import threading
from flask import Flask, Response

app = Flask(__name__)

# URLs of the RTSP streams
rtsp_url_1 = 'rtsp://192.168.20.94:554/user=admin_password=oTyLhoPM_channel=1_stream=0&onvif=0.sdp?real_stream'
rtsp_url_2 = 'rtsp://192.168.20.249:554/ONVIFMedia'

# Create VideoCapture objects for each stream
cap1 = cv2.VideoCapture(rtsp_url_1)
cap2 = cv2.VideoCapture(rtsp_url_2)

def combine_streams():
    while True:
        # Capture frame-by-frame from both streams
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()

        if not ret1 or not ret2:
            break

        # Resize frames to the same size if necessary
        frame1 = cv2.resize(frame1, (640, 480))
        frame2 = cv2.resize(frame2, (640, 480))

        # Combine frames side by side
        combined_frame = cv2.hconcat([frame1, frame2])

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', combined_frame)
        combined_frame = buffer.tobytes()

        # Yield the output frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + combined_frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # Route to display the video stream in the browser
    return Response(combine_streams(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

# Release resources
cap1.release()
cap2.release()
cv2.destroyAllWindows()