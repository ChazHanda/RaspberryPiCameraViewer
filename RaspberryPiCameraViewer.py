import cv2

camera = cv2.VideoCapture("/dev/video0")

if not camera.isOpened():
    print("Could not open /dev/video0")
    exit()

while True:
    ret, frame = camera.read()

    if not ret:
        print("Could not read camera frame")
        break

    cv2.imshow("Camera", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
