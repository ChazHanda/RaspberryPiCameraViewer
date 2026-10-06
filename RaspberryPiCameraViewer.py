import cv2

camera1 = cv2.VideoCapture("/dev/video0")
camera2 = cv2.VideoCapture("/dev/video2")

if not camera1.isOpened():
    print("Could not open /dev/video0")
    exit()

if not camera2.isOpened():
    print("Could not open /dev/video2")
    exit()

while True:
    ret1, frame1 = camera1.read()
    ret2, frame2 = camera2.read()

    if not ret1:
        print("Could not read camera frame /dev/video0")
        break
        
    if not ret2:
        print("Could not read camera frame /dev/video2")
        break
        
    # Match camera height
    height1 = frame1.shape[0]
    height2 = frame2.shape[0]
    
    if height1 != height2:
        scale = height1 / height2
        new_width = int(frame2.shape[1] * scale)

        frame2 = cv2.resize(
            frame2,
            (new_width, height1)
        )
    # Combine the feeds
    combined_frame = cv2.hconcat([frame1, frame2])

    cv2.imshow("Camera Viewer", combined_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera1.release()
camera2.release()

cv2.destroyAllWindows()
