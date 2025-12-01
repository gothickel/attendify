from flask import Flask
import mysql.connector
import cv2

app = Flask(__name__)

@app.route("/")
def home():
    return "MySQL Test App Running"

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

@app.route('/check_cv2')
def check_cv2():
    url = "http://192.168.100.90:8080/video"

    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print("❌ Cannot connect to IP camera")
        exit()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame")
            break
    
        cv2.imshow("IP Camera Stream", frame)
    
        if cv2.waitKey(1) == 27:  # press ESC to exit
            break
    
    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    app.run(debug=True)

