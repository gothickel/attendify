import subprocess
import signal
from flask import Flask, send_from_directory
from flask_sock import Sock
import os
app = Flask(__name__, static_folder='static', static_url_path='/static')
sock = Sock(app)

# CHANGE THIS to your camera RTSP URL or set as environment variable before deploy
RTSP_URL = os.getenv("RTSP_URL")

def ffmpeg_process(rtsp_url):
    # ffmpeg command: read RTSP and output MPEG1 video to stdout
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
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, preexec_fn=None)

@app.route("/")
def index():
    # serve the static index.html
    return send_from_directory(".", "index.html")

@sock.route("/stream")
def stream(ws):
    # For every new websocket connection, spawn ffmpeg
    process = ffmpeg_process(RTSP_URL)
    try:
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            ws.send(chunk, binary=True)
    except Exception:
        pass
    finally:
        try:
            process.kill()
        except Exception:
            pass

if __name__ == "__main__":
    # For local testing only. Railway will use gunicorn command in README/Procfile
    app.run(host="0.0.0.0", port=3000)
