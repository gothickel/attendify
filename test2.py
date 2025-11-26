import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="attendify",
    use_pure=True
)

if conn.is_connected():
    print("Database connected successfully")
else:
    print("Failed to connect to the database")