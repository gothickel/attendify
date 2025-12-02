import subprocess
import signal
from flask import Flask, send_from_directory
from flask_sock import Sock
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
sock = Sock(app)

# Load RTSP URL from Railway environment variable
RTSP_URL = os.getenv("RTSP_URL")

def ffmpeg_process(rtsp_url):
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-f", "mpegts",
        "-codec:v", "mpeg1video",
        "-s", "640x360",
        "-b:v", "800k",
        "-r", "20",
        "-"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/video")
def video():
    return send_from_directory(".", "index.html")

@sock.route("/stream")
def stream(ws):
    process = ffmpeg_process(RTSP_URL)
    try:
        while True:
            data = process.stdout.read(1024)
            if not data:
                break
            ws.send(data, binary=True)
    except:
        pass
    finally:
        try:
            process.kill()
        except:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
