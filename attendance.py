import cv2
import numpy as np
import pickle
from random import randint 
import mysql.connector
from datetime import datetime
import os
import pyttsx3
mydb = mysql.connector.connect(
      host="localhost",
      user="root",
      passwd="",
      database="attendify",
      use_pure=True
)
roomno = "201"

def is_hour_between(start, end):
    # Time Now
    now = datetime.now().time()
    # Format the datetime string
    time_format = '%H:%M'
    # Convert the start and end datetime to just time
    start = datetime.strptime(start, time_format).time()
    end = datetime.strptime(end, time_format).time()

    is_between = False
    is_between |= start <= now <= end
    is_between |= end <= start and (start <= now or now <= end)

    return is_between


# Load the trained model
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))  # current script folder
    model_path = os.path.join(script_dir, "defect_model.pkl")  # find file beside script

    with open(model_path, "rb") as f:
        model = pickle.load(f)
    print(f"✅ Model loaded successfully from: {model_path}")

except FileNotFoundError:
    print("❌ Error: defect_model.pkl not found. Please run train.py first.")
    exit()
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Error: defect_model.pkl not found. Train the model first.")
    exit()

def preprocess_image(image):
    """
    Resize the image to 64x64 and flatten it for model prediction.
    """
    resized = cv2.resize(image, (64, 64))
    flattened = resized.flatten()
    return flattened

def is_object_present_and_centered(roi_frame):
    """
    Check if an object is present in the ROI and centered.
    Uses color masking to detect the object and ensures it is near the center.
    """
    hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
    lower = np.array([10, 100, 100])
    upper = np.array([25, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    detected_pixels = cv2.countNonZero(mask)

    # Check if enough pixels are detected (object is present)
    if detected_pixels > 500:  # Adjust threshold as needed
        # Calculate the moments of the mask to find the center
        moments = cv2.moments(mask)
        if moments["m00"] > 0:
            cx = int(moments["m10"] / moments["m00"])  # X center of the object
            cy = int(moments["m01"] / moments["m00"])  # Y center of the object
            height, width = mask.shape

            # Check if the object's center is close to the ROI's center
            if abs(cx - width // 2) < 30 and abs(cy - height // 2) < 30:  # 30-pixel tolerance
                return True
    return False


# Initialize the camera
camera = cv2.VideoCapture(0)

# Initialize counters for each category
count_defect_free = 0
count_defective = 0
count_neutral = 0

# Flag to ensure an object is counted only once
object_in_roi = False
counterin = 0
counterout = 0
print("Press 'q' to quit.")

def sayWord(word):
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    engine.say(word)
    engine.runAndWait()

while True:
    subject = ""
    subjectid = ""
    scheduleid = ""
    counttext = ""
    timein = "00:00"
    timeout = "00:00"
    timelate = "00:00"
    timeabsent = "00:00"
    timestatus = ""
    timelatestatus = ""
    timeabsentstatus = ""
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    datetoday = current_datetime.strftime("%Y-%m-%d")
    timenow = current_datetime.strftime("%H:%M")
    timenowatt = current_datetime.strftime("%H:%M:%S")
    daytoday = current_datetime.strftime("%A")

    mycursor = mydb.cursor()
    mycursor.execute("SELECT sj.code, s.id, s.timelate, s.timeabsent, s.timein, s.timeout FROM schedule s LEFT JOIN subject sj ON s.sjid=sj.id WHERE s.day='" + daytoday + "' AND '" + timenow + "' BETWEEN s.timein AND s.timeout AND s.roomno='" + roomno + "'")    
    row = mycursor.fetchall()
    if mycursor.rowcount == 0:
        subject = ""
        scheduleid = ""
        timein = "00:00"
        timeout = "00:00"
        timelate = "00:00"
        timeabsent = "00:00"
        timestatus = ""
        if counterin > 0:
            counterin = 0
            sayWord("The subject has ended.")

    for rowsched in row:
        subject = rowsched[0]
        scheduleid = rowsched[1]
        timelate = rowsched[2]
        timeabsent = rowsched[3]
        timein = rowsched[4]
        timeout = rowsched[5]
        counterin += 1
        if counterin == 10:
            sayWord("The subject " + subject + " has started.")
            
    mydb.commit()
    

    for i in range(1, 16):
        mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat " + str(i) + "'")    
        row21 = mycursor.fetchall()
        mydb.commit()
        for rowseat in row21:
            mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat[1]) + "'")    
            row31 = mycursor.fetchall()
            mydb.commit()
            if mycursor.rowcount == 0:
                mycursor.execute("INSERT INTO attendance (timein, status, sdid, sid, timelate, timeabsent) VALUES('" + datetoday + "','Absent','" + str(scheduleid) + "','" + str(rowseat[1]) + "','Empty','Empty')")
                mydb.commit()

    checkpresent = is_hour_between(timein, timelate)
    if checkpresent == True:
        timestatus = "Present"
    
    checklate = is_hour_between(timelate, timeabsent)
    if checklate == True:
        timelatestatus = "Present"
        timestatus = "Late"
    else:
        timelatestatus = "Empty"

    checkabsent = is_hour_between(timeabsent, timeout)
    if checkabsent == True:
        timeabsentstatus = "Present"
        timestatus = "Absent"
    else:
        timeabsentstatus = "Empty"

    # Capture a frame
    success, frame = camera.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    resized_frame = cv2.resize(frame, (900, 800))
    assert success

    left1, top1, right1, bottom1 = 20, 150, 150, 300
    left6, top6, right6, bottom6 = 20, 350, 150, 500
    left11, top11, right11, bottom11 = 20, 550, 150, 700
    left2, top2, right2, bottom2 = 200, 150, 330, 300
    left7, top7, right7, bottom7 = 200, 350, 330, 500
    left12, top12, right12, bottom12 = 200, 550, 330, 700
    left3, top3, right3, bottom3 = 380, 150, 510, 300
    left8, top8, right8, bottom8 = 380, 350, 510, 500
    left13, top13, right13, bottom13 = 380, 550, 510, 700
    left4, top4, right4, bottom4 = 560, 150, 690, 300
    left9, top9, right9, bottom9 = 560, 350, 690, 500
    left14, top14, right14, bottom14 = 560, 550, 690, 700
    left5, top5, right5, bottom5 = 740, 150, 870, 300
    left10, top10, right10, bottom10 = 740, 350, 870, 500
    left15, top15, right15, bottom15 = 740, 550, 870, 700
        
    cv2.rectangle(resized_frame, (left1, top1), (right1, bottom1), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left2, top2), (right2, bottom2), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left3, top3), (right3, bottom3), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left4, top4), (right4, bottom4), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left5, top5), (right5, bottom5), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left6, top6), (right6, bottom6), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left7, top7), (right7, bottom7), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left8, top8), (right8, bottom8), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left9, top9), (right9, bottom9), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left10, top10), (right10, bottom10), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left11, top11), (right11, bottom11), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left12, top12), (right12, bottom12), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left13, top13), (right13, bottom13), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left14, top14), (right14, bottom14), (255, 255, 0), 2)
    cv2.rectangle(resized_frame, (left15, top15), (right15, bottom15), (255, 255, 0), 2)

    seat1 = resized_frame[top1:bottom1, left1:right1]
    seat2 = resized_frame[top2:bottom2, left2:right2]
    seat3 = resized_frame[top3:bottom3, left3:right3]
    seat4 = resized_frame[top4:bottom4, left4:right4]
    seat5 = resized_frame[top5:bottom5, left5:right5]
    seat6 = resized_frame[top6:bottom6, left6:right6]
    seat7 = resized_frame[top7:bottom7, left7:right7]
    seat8 = resized_frame[top8:bottom8, left8:right8]
    seat9 = resized_frame[top9:bottom9, left9:right9]
    seat10 = resized_frame[top10:bottom10, left10:right10]
    seat11 = resized_frame[top11:bottom11, left11:right11]
    seat12 = resized_frame[top12:bottom12, left12:right12]
    seat13 = resized_frame[top13:bottom13, left13:right13]
    seat14 = resized_frame[top14:bottom14, left14:right14]
    seat15 = resized_frame[top15:bottom15, left15:right15]

    if is_object_present_and_centered(seat1):
        processed = preprocess_image(seat1)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left1, top1), (right1, bottom1), color, 2)
        cv2.putText(resized_frame, f"{label}", (left1, top1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 1'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False

    if is_object_present_and_centered(seat6):
        processed = preprocess_image(seat6)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left6, top6), (right6, bottom6), color, 2)
        cv2.putText(resized_frame, f"{label}", (left6, top6 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 6'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False

    if is_object_present_and_centered(seat11):
        processed = preprocess_image(seat11)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left11, top11), (right11, bottom11), color, 2)
        cv2.putText(resized_frame, f"{label}", (left11, top11 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 11'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False

    if is_object_present_and_centered(seat2):
        processed = preprocess_image(seat2)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left2, top2), (right2, bottom2), color, 2)
        cv2.putText(resized_frame, f"{label}", (left2, top2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 2'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False   

    if is_object_present_and_centered(seat7):
        processed = preprocess_image(seat7)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left7, top7), (right7, bottom7), color, 2)
        cv2.putText(resized_frame, f"{label}", (left7, top7 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 7'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat12):
        processed = preprocess_image(seat12)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left12, top12), (right12, bottom12), color, 2)
        cv2.putText(resized_frame, f"{label}", (left12, top12 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 12'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat3):
        processed = preprocess_image(seat3)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left3, top3), (right3, bottom3), color, 2)
        cv2.putText(resized_frame, f"{label}", (left3, top3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 3'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False 

    if is_object_present_and_centered(seat8):
        processed = preprocess_image(seat8)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left8, top8), (right8, bottom8), color, 2)
        cv2.putText(resized_frame, f"{label}", (left8, top8 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 8'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False 

    if is_object_present_and_centered(seat13):
        processed = preprocess_image(seat13)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left13, top13), (right13, bottom13), color, 2)
        cv2.putText(resized_frame, f"{label}", (left13, top13 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 13'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat4):
        processed = preprocess_image(seat4)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left4, top4), (right4, bottom4), color, 2)
        cv2.putText(resized_frame, f"{label}", (left4, top4 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 4'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat9):
        processed = preprocess_image(seat9)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yelloww
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left9, top9), (right9, bottom9), color, 2)
        cv2.putText(resized_frame, f"{label}", (left9, top9 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 9'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat14):
        processed = preprocess_image(seat14)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left14, top14), (right14, bottom14), color, 2)
        cv2.putText(resized_frame, f"{label}", (left14, top14 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 14'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False  

    if is_object_present_and_centered(seat5):
        processed = preprocess_image(seat5)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left5, top5), (right5, bottom5), color, 2)
        cv2.putText(resized_frame, f"{label}", (left5, top5 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 5'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False 

    if is_object_present_and_centered(seat10):
        processed = preprocess_image(seat10)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left10, top10), (right10, bottom10), color, 2)
        cv2.putText(resized_frame, f"{label}", (left10, top10 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 10'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False 

    if is_object_present_and_centered(seat15):
        processed = preprocess_image(seat15)
        prediction = model.predict([processed])[0]
        confidence = model.predict_proba([processed])[0]  # Get confidence scores
        labels_map = {0: "Empty", 1: "Present"}
        label = labels_map[prediction]
        colors_map = {0: (0, 0, 255), 1: (0, 255, 0)}  # Green, Red, Yellow
        color = colors_map[prediction]
        cv2.rectangle(resized_frame, (left15, top15), (right15, bottom15), color, 2)
        cv2.putText(resized_frame, f"{label}", (left15, top15 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        if not object_in_roi:
            if prediction == 1:  # Defective
                
                mycursor.execute("SELECT * FROM seat WHERE sdid='" + str(scheduleid) + "' AND position='Seat 15'")    
                rowseat1 = mycursor.fetchall()
                mydb.commit()
                for rowseat11 in rowseat1:
                    mycursor.execute("SELECT * FROM attendance WHERE timein LIKE '%" + datetoday + "%' AND sdid='" + str(scheduleid) + "' AND sid='" + str(rowseat11[1]) + "' AND timeabsent='Empty'")    
                    rowatty1 = mycursor.fetchall()
                    mydb.commit()
                    if mycursor.rowcount > 0:
                        for rowatty11 in rowatty1:
                            if timestatus == "Present":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Late":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Present', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
                            elif timestatus == "Absent":
                                
                                mycursor.execute("UPDATE attendance SET status='" + timestatus + "', timelate='Empty', timeabsent='Present', timein='" + formatted_date + "' WHERE id='" + str(rowatty11[0]) + "'")
                                mydb.commit()
            object_in_roi = True  # Mark object as counted
    else:
        object_in_roi = False 
    # Display counters on the frame
    cv2.putText(resized_frame, f"Current Subject: {subject}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Display the live feed with prediction and counters
    cv2.imshow("Attendify", resized_frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



cv2.destroyAllWindows()
camera.release()
