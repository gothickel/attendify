from flask import Flask
import mysql.connector

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
    try:
        version = cv2.__version__
        return f"OpenCV is installed. Version: {version}"
    except ImportError:
        return "OpenCV (cv2) is NOT installed."
        
if __name__ == "__main__":
    app.run()


