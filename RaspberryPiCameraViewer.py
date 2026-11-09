import cv2
import tkinter as tk
import numpy as np
from datetime import datetime

# Get screen resolution
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()


camera1 = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
camera2 = cv2.VideoCapture("/dev/video2", cv2.CAP_V4L2)

# Most recently captured frame from each camera
latest_frames = {
    1: None,
    2: None
}


# VideoWriter used by each camera.
# None means that camera is not currently recording.
video_writers = {
    1: None,
    2: None
}

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
def split_screen(frame1, frame2):
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

    return cv2.hconcat([
        frame1,
        frame2
    ])



# Function to full-screen one camera feed
def full_screen(camera_number, frame1, frame2):
    if camera_number == 0:
        frame = frame1

    elif camera_number == 2:
        frame = frame2

    else:
        print("Invalid camera number")
        return None

    return fit_to_area(
        frame,
        screen_width,
        screen_height
    )
    
# Function to create a filename
def create_file_name(camera_number, file_type):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

    if file_type == "image":
        extension = "jpg"

    elif file_type == "video":
        extension = "mp4"

    else:
        raise ValueError("file_type must be 'image' or 'video'")

    return f"camera{camera_number}_{timestamp}.{extension}"

# Function to save an image on a specified camera
def save_image(camera_number):

    if camera_number not in latest_frames:
        print(f"Invalid camera number: {camera_number}")
        return

    frame = latest_frames[camera_number]

    if frame is None:
        print(f"No frame available from camera {camera_number}")
        return

    file_name = create_file_name(
        camera_number,
        "image"
    )

    success = cv2.imwrite(
        file_name,
        frame
    )

    if success:
        print(f"Saved image: {file_name}")

    else:
        print(f"Failed to save image from camera {camera_number}")

# Function starts recording on specified camera
def start_recording(camera_number):

    if camera_number not in video_writers:
        print(f"Invalid camera number: {camera_number}")
        return

    if video_writers[camera_number] is not None:
        print(f"Camera {camera_number} is already recording")
        return

    frame = latest_frames[camera_number]

    if frame is None:
        print(f"No frame available from camera {camera_number}")
        return

    frame_height, frame_width = frame.shape[:2]

    file_name = create_file_name(
        camera_number,
        "video"
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        file_name,
        fourcc,
        30.0,
        (frame_width, frame_height)
    )

    if not writer.isOpened():
        print(f"Could not start recording camera {camera_number}")
        return

    video_writers[camera_number] = writer

    print(
        f"Started recording camera {camera_number}: "
        f"{file_name}"
    )
# Function stops recording on specified camera
def stop_recording(camera_number):

    if camera_number not in video_writers:
        print(f"Invalid camera number: {camera_number}")
        return

    writer = video_writers[camera_number]

    if writer is None:
        print(f"Camera {camera_number} is not recording")
        return

    writer.release()

    video_writers[camera_number] = None

    print(f"Stopped recording camera {camera_number}")

    
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

    # Read both cameras every loop
    ret1, frame1 = camera1.read()
    ret2, frame2 = camera2.read()

    if not ret1:
        print("Could not read /dev/video0")
        break

    if not ret2:
        print("Could not read /dev/video2")
        break


    # Store the most recent original frames
    latest_frames[1] = frame1
    latest_frames[2] = frame2


    # Record camera1 if recording
    if video_writers[1] is not None:
        video_writers[1].write(frame1)

    # Record camera2 if recording
    if video_writers[2] is not None:
        video_writers[2].write(frame2)


    # Select what will be displayed
    if mode == "split":
        frame = split_screen(
            frame1,
            frame2
        )

    elif mode == "camera0":
        frame = full_screen(
            0,
            frame1,
            frame2
        )

    elif mode == "camera2":
        frame = full_screen(
            2,
            frame1,
            frame2
        )

    else:
        frame = None


    if frame is None:
        break


    cv2.imshow(
        "Camera Viewer",
        frame
    )

    # WaitKeyEx because F1/F2 are extended keys
    key = cv2.waitKeyEx(1)

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


    # Z = Save image from camera1
    elif key == ord("z"):
        save_image(1)

    # C = Save image from camera2
    elif key == ord("c"):
        save_image(2)


    # F1 = Start recording camera1
    elif key in (65470, 16777264):
        start_recording(1)

    # F2 = Start recording camera2
    elif key in (65471, 16777265):
        start_recording(2)


    # 1 = Stop recording camera1
    elif key == ord("1"):
        stop_recording(1)

    # 2 = Stop recording camera2
    elif key == ord("2"):
        stop_recording(2)


# Finish any active video files before closing
stop_recording(1)
stop_recording(2)

camera1.release()
camera2.release()

cv2.destroyAllWindows()
