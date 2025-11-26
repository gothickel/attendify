import cv2

# Initialize the camera
camera = cv2.VideoCapture(1)

save_path = "/home/pi/" # replace with your path directory
image_count = 0
roi = (300, 100, 440, 380)
print("Press 'c' to capture an image and 'q' to quit.")

while True:
    # Capture a frame
    success, frame=camera.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    resize = cv2.resize(frame, (900, 800)) 
    # Display the live feed
    cv2.imshow("Capturing Images", resize)
    assert success
    # Save an image when 'c' is pressed
    key = cv2.waitKey(1)
    if key & 0xFF == ord('c'):
        # Save the cropped image
        image_path = f"nochair/image_{image_count}.jpg"
        cv2.imwrite(image_path, resize)
        print(f"Saved: {image_path}")
        image_count += 1

    # Exit on 'q' key press
    elif key & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
camera.release()

