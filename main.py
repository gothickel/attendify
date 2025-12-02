import cv2
import os
from flask import Flask, Response

# Railway requires port from environment variable
PORT = int(os.environ.get("PORT", 8000))

# RTSP URL via environment variable (BEST)
RTSP_URL = os.environ.get(
    "RTSP_URL",
    "rtsp://admin:Camera123@192.168.100.53:554/stream1"
)

app = Flask(__name__)

# Open camera using FFmpeg
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

# Timeouts (avoid Railway freezing)
cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)


def generate():
    while True:
        success, frame = cap.read()
        if not success:
            continue

        # Prevent async_lock crashes on Railway
        frame = cv2.resize(frame, (640, 360))

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


@app.route("/")
def stream():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
