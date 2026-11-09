import cv2
import tkinter as tk
import numpy as np
from datetime import datetime
from pathlib import Path


# Creates an "output" folder next to this Python file.
script_directory = Path(__file__).resolve().parent
output_directory = script_directory / "output"

output_directory.mkdir(
    parents=True,
    exist_ok=True
)

root = tk.Tk()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.destroy()

camera1 = cv2.VideoCapture(
    "/dev/video0",
    cv2.CAP_V4L2
)

camera2 = cv2.VideoCapture(
    "/dev/video2",
    cv2.CAP_V4L2
)


# Most recently captured frame from each camera
latest_frames = {
    1: None,
    2: None
}


# VideoWriter used by each camera.
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
    if camera_number == 1:
        frame = frame1

    elif camera_number == 2:
        frame = frame2

    else:
        print(f"Invalid camera number: {camera_number}")
        return None

    return fit_to_area(
        frame,
        screen_width,
        screen_height
    )

# Function to create a unique filename
def create_file_name(camera_number, file_type):
    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S-%f"
    )

    if file_type == "image":
        extension = "jpg"

    elif file_type == "video":
        extension = "mp4"

    else:
        raise ValueError(
            "file_type must be 'image' or 'video'"
        )

    file_name = (
        f"camera{camera_number}_"
        f"{timestamp}."
        f"{extension}"
    )

    return output_directory / file_name


# Function to save an image from a specified camera
def save_image(camera_number):
    if camera_number not in latest_frames:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return

    frame = latest_frames[camera_number]

    if frame is None:
        print(
            f"No frame available from "
            f"camera {camera_number}"
        )
        return

    file_name = create_file_name(
        camera_number,
        "image"
    )

    success = cv2.imwrite(
        str(file_name),
        frame
    )

    if success:
        print(
            f"Saved image: "
            f"{file_name}"
        )

    else:
        print(
            f"Failed to save image from "
            f"camera {camera_number}"
        )


# Get the FPS reported by a camera
def get_camera_fps(camera_number):
    if camera_number == 1:
        camera = camera1

    elif camera_number == 2:
        camera = camera2

    else:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return 30.0

    fps = camera.get(
        cv2.CAP_PROP_FPS
    )

    # Some cameras/drivers report 0 or an invalid value.
    if fps <= 0 or fps > 120:
        print(
            f"Could not determine FPS for "
            f"camera {camera_number}. "
            f"Using 30 FPS."
        )

        return 30.0

    return fps


# Function to start recording a specified camera
def start_recording(camera_number):
    if camera_number not in video_writers:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return

    # Don't start another recording if this camera is already recording.
    if video_writers[camera_number] is not None:
        print(
            f"Camera {camera_number} "
            f"is already recording"
        )
        return

    frame = latest_frames[camera_number]

    if frame is None:
        print(
            f"No frame available from "
            f"camera {camera_number}"
        )
        return

    frame_height, frame_width = frame.shape[:2]

    file_name = create_file_name(
        camera_number,
        "video"
    )

    fps = get_camera_fps(
        camera_number
    )

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(file_name),
        fourcc,
        fps,
        (frame_width, frame_height)
    )

    if not writer.isOpened():
        print(
            f"Could not start recording "
            f"camera {camera_number}"
        )

        writer.release()
        return

    video_writers[camera_number] = writer

    print(
        f"Started recording camera "
        f"{camera_number}: {file_name}"
    )

    print(
        f"Recording FPS: {fps}"
    )


# Function to stop recording a specified camera
def stop_recording(camera_number):
    if camera_number not in video_writers:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return

    writer = video_writers[camera_number]

    if writer is None:
        print(
            f"Camera {camera_number} "
            f"is not recording"
        )
        return

    writer.release()

    video_writers[camera_number] = None

    print(
        f"Stopped recording camera "
        f"{camera_number}"
    )


if not camera1.isOpened():
    print(
        "Could not open "
        "/dev/video0"
    )

    camera2.release()

    raise SystemExit


if not camera2.isOpened():
    print(
        "Could not open "
        "/dev/video2"
    )

    camera1.release()

    raise SystemExit


cv2.namedWindow(
    "Camera Viewer",
    cv2.WINDOW_NORMAL
)

cv2.setWindowProperty(
    "Camera Viewer",
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)


# Default display mode
mode = "split"

try:
    while True:

        # Read both cameras every loop
        ret1, frame1 = camera1.read()
        ret2, frame2 = camera2.read()

        if not ret1:
            print(
                "Could not read "
                "/dev/video0"
            )
            break

        if not ret2:
            print(
                "Could not read "
                "/dev/video2"
            )
            break


        # Store the most recent original frames
        latest_frames[1] = frame1
        latest_frames[2] = frame2


        # Record camera 1 if recording
        if video_writers[1] is not None:
            video_writers[1].write(
                frame1
            )


        # Record camera 2 if recording
        if video_writers[2] is not None:
            video_writers[2].write(
                frame2
            )


        # Select what will be displayed
        if mode == "split":
            frame = split_screen(
                frame1,
                frame2
            )

        elif mode == "camera1":
            frame = full_screen(
                1,
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


        # waitKeyEx is needed for F1/F2
        key = cv2.waitKeyEx(1)


        # Q = Quit
        if key == ord("q"):
            break


        # S = Split screen
        elif key == ord("s"):
            mode = "split"


        # A = Camera 1 fullscreen
        elif key == ord("a"):
            mode = "camera1"


        # D = Camera 2 fullscreen
        elif key == ord("d"):
            mode = "camera2"


        # Z = Save image from camera 1
        elif key == ord("z"):
            save_image(1)


        # C = Save image from camera 2
        elif key == ord("c"):
            save_image(2)


        # F1 = Start recording camera 1
        elif key in (
            65470,
            16777264
        ):
            start_recording(1)


        # F2 = Start recording camera 2
        elif key in (
            65471,
            16777265
        ):
            start_recording(2)


        # 1 = Stop recording camera 1
        elif key == ord("1"):
            stop_recording(1)


        # 2 = Stop recording camera 2
        elif key == ord("2"):
            stop_recording(2)


finally:

    # Properly finalize active recordings.
    if video_writers[1] is not None:
        stop_recording(1)

    if video_writers[2] is not None:
        stop_recording(2)


    camera1.release()
    camera2.release()

    cv2.destroyAllWindows()
