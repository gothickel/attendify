from flask import Flask, Response
import cv2

app = Flask(__name__)

# YOUR LOCAL IP WEBCAM STREAM
# If using IP Webcam (Android), use:
# http://<phone-ip>:8080/video
camera_url = "http://192.168.100.90:8080/video"

cap = cv2.VideoCapture(camera_url)

def generate_frames():
    while True:
        success, frame = cap.read()

        if not success:
            continue

        # Convert frame to JPG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Create streaming frame format
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\n' + frame + b'\r\n'
        )

@app.route('/video')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/')
def home():
    return "Video stream is running! Go to /video"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
