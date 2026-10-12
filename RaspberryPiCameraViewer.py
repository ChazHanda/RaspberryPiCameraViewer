import cv2
import tkinter as tk
import numpy as np

# Get screen resolution
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()


camera1 = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
camera2 = cv2.VideoCapture("/dev/video2", cv2.CAP_V4L2)

# Function to size screen areas
def fit_to_area(frame, width, height):
    frame_height, frame_width = frame.shape[:2]

    scale = min(
        width / frame_width,
        height / frame_height
    )

    new_width = int(frame_width * scale)
    new_height = int(frame_height * scale)

    resized = cv2.resize(
        frame,
        (new_width, new_height)
    )

    canvas = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    x = (width - new_width) // 2
    y = (height - new_height) // 2

    canvas[
        y:y + new_height,
        x:x + new_width
    ] = resized

    return canvas


# Function for side-by-side screens
def split_screen():
    ret1, frame1 = camera1.read()
    ret2, frame2 = camera2.read()

    if not ret1:
        print("Could not read /dev/video0")
        return None

    if not ret2:
        print("Could not read /dev/video2")
        return None

    half_width = screen_width // 2

    frame1 = fit_to_area(
        frame1,
        half_width,
        screen_height
    )

    frame2 = fit_to_area(
        frame2,
        half_width,
        screen_height
    )

    combined_frame = cv2.hconcat([
        frame1,
        frame2
    ])

    return combined_frame


# Function to full-screen one camera feed
def full_screen(camera_number):
    if camera_number == 0:
        camera = camera1

    elif camera_number == 2:
        camera = camera2

    else:
        print("Invalid camera number")
        return None

    ret, frame = camera.read()

    if not ret:
        print(f"Could not read /dev/video{camera_number}")
        return None

    frame = fit_to_area(
        frame,
        screen_width,
        screen_height
    )

    return frame

if not camera1.isOpened():
    print("Could not open /dev/video0")
    exit()

if not camera2.isOpened():
    print("Could not open /dev/video2")
    exit()

cv2.namedWindow(
    "Camera Viewer",
    cv2.WINDOW_NORMAL
)

cv2.setWindowProperty(
    "Camera Viewer",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

# Default split-screen
mode = "split"


while True:

    if mode == "split":
        frame = split_screen()

    elif mode == "camera0":
        frame = full_screen(0)

    elif mode == "camera2":
        frame = full_screen(2)

    else:
        frame = None


    if frame is None:
        break


    cv2.imshow(
        "Camera Viewer",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    # Q = Quit
    if key == ord("q"):
        break

    # S = Split screen
    elif key == ord("s"):
        mode = "split"

    # A = /dev/video0 fullscreen
    elif key == ord("a"):
        mode = "camera0"

    # D = /dev/video2 fullscreen
    elif key == ord("d"):
        mode = "camera2"

camera1.release()
camera2.release()

cv2.destroyAllWindows()
