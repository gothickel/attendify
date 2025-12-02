import cv2
from flask import Flask, Response

app = Flask(__name__)

# --- CHANGE THIS TO YOUR CAMERA ---
RTSP_URL = "rtsp://admin:Camera123@192.168.100.53:554/stream1"

def generate_frames():
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("❌ Cannot connect to RTSP camera")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield frame as multipart stream
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )

@app.route("/")
def home():
    return "<h2>RTSP Camera is Running!</h2><p>Go to: /video</p>"

@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    # Railway uses PORT environment variable
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
