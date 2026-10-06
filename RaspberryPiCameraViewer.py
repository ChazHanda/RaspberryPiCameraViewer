import cv2
import tkinter as tk
import numpy as np

# Get screen resolution
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

half_width = screen_width // 2

camera1 = cv2.VideoCapture("/dev/video0")
camera2 = cv2.VideoCapture("/dev/video2")

if not camera1.isOpened():
    print("Could not open /dev/video0")
    exit()

if not camera2.isOpened():
    print("Could not open /dev/video2")
    exit()

def fit_to_half_screen(frame):
    frame_height, frame_width = frame.shape[:2]

    # Scale image while keeping aspect ratio
    scale = min(
        half_width / frame_width,
        screen_height / frame_height
    )

    new_width = int(frame_width * scale)
    new_height = int(frame_height * scale)

    resized = cv2.resize(
        frame,
        (new_width, new_height)
    )

    # Create a black area exactly half the screen width
    canvas = np.zeros(
        (screen_height, half_width, 3),
        dtype=np.uint8
    )

    # Center the camera image
    x = (half_width - new_width) // 2
    y = (screen_height - new_height) // 2

    canvas[
        y:y + new_height,
        x:x + new_width
    ] = resized

    return canvas
    
while True:
    ret1, frame1 = camera1.read()
    ret2, frame2 = camera2.read()

    if not ret1:
        print("Could not read camera frame /dev/video0")
        break
        
    if not ret2:
        print("Could not read camera frame /dev/video2")
        break

    # Put camera feeds side-by-side
    frame1 = fit_to_half_screen(frame1)
    frame2 = fit_to_half_screen(frame2)
    
    combined_frame = cv2.hconcat([frame1, frame2])

    cv2.namedWindow("Camera Viewer", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Camera Viewer",
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )
  
    cv2.imshow("Camera Viewer", combined_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera1.release()
camera2.release()

cv2.destroyAllWindows()
