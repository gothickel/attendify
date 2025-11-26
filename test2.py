from flask import Flask
import mysql.connector
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "MySQL Test App Running"

@app.route("/testdb")
def testdb():
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

if __name__ == "__main__":
    app.run()

