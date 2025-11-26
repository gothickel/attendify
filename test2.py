from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "MySQL Test App Running"

@app.route("/testdb")
def testdb():
    try:
        return f"Connected: Server time: {datetime.now().time()}"
    except Exception as e:
        return f"Connection error: {str(e)}"

if __name__ == "__main__":
    app.run()
