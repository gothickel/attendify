# IP Camera (RTSP) → WebSocket → Browser (Python, Flask, ffmpeg)

## What this project contains
- `main.py` - Flask app that spawns `ffmpeg` and relays the MPEG-TS stream over WebSocket using `flask-sock`.
- `index.html` - Simple viewer using JSMpeg (connects to `/stream` websocket).
- `requirements.txt` - Python dependencies.
- `Procfile` - For deployment with gunicorn (Railway).
- `start.sh` - helper to run locally.

## Configure
Edit `main.py` and change `RTSP_URL` to your camera's RTSP address, for example:

```
RTSP_URL = "rtsp://username:password@192.168.1.50:554/stream1"
```

Or set it as an environment variable before starting (you can modify `main.py` to read from `os.environ`).

## Run locally (Linux / WSL)
1. Install ffmpeg on your machine (apt / brew / choco).
2. Create and activate a Python virtualenv.
3. `pip install -r requirements.txt`
4. `python main.py` (then open http://localhost:3000)

For production-like behavior use the Procfile command:
```
gunicorn -k flask_sock.worker main:app -b 0.0.0.0:3000
```

## Deploy to Railway
1. Push this repo to GitHub.
2. Create a new Railway project and connect your GitHub repository.
3. Set Railway start command to the Procfile command (Railway runs the Procfile automatically).
4. IMPORTANT: Railway images need ffmpeg. Set the following environment variable in Railway (Project > Variables) so ffmpeg is installed at build:
   ```
   NIXPACKS_BUILD_COMMAND=apt-get update && apt-get install -y ffmpeg
   ```
5. Deploy — Railway will build the container, install ffmpeg, and run the web process.

## Notes & troubleshooting
- Railway cannot accept RTSP directly from your local LAN. Your camera must be reachable from the Railway host (public IP) unless you're running Railway locally (or using a tunnel).
- If the ffmpeg process crashes or disconnects, reload the page to reconnect.
- For multiple cameras, run multiple endpoints or spawn ffmpeg per-connection with different RTSP URLs.
