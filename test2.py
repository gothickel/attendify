from flask import Flask, Response
import mysql.connector
import cv2

app = Flask(__name__)

@app.route("/")
def home():
    return "MySQL + IP Camera (Railway) Flask App Running"

@app.route("/attendance")
def attendance():
    try:
        db = mysql.connector.connect(
            host="mysql1001.site4now.net",
            user="ac0ccf_att",
            password="attendify123",
            database="db_ac0ccf_att",
            use_pure=True
        )

        cursor = db.cursor()
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()

        return f"Connected to MySQL! Server time: {result[0]}"

    except Exception as e:
        return f"Database connection error: {str(e)}"


# ------- IP CAMERA STREAMING ---------

def generate_frames():
    url = "http://192.168.100.90:8080/video"   # DroidCam or IP Cam

    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        raise Exception("Cannot connect to IP camera")

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Encode frame as JPEG → Browser friendly
        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        # Stream MJPEG frames
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/camera")
def camera():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
