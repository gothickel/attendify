import cv2
import requests
from flask import Flask, Response

# Replace this with your ngrok HTTPS MJPEG stream
NGROK_STREAM_URL = "https://shaunte-prebronze-destiny.ngrok-free.dev"

app = Flask(__name__)

def generate():
    stream = requests.get(NGROK_STREAM_URL, stream=True)

    if stream.status_code != 200:
        print("Cannot connect to relay:", stream.status_code)
        return

    bytes_data = b""

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')

@app.route("/")
def home():
    return "<h2>Railway RTSP Stream Relay</h2><p>Go to /video</p>"

@app.route("/video")
def video():
    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
