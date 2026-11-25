import cv2
# import tkinter as tk  # OLD: Kivy now owns the application window.
import numpy as np
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard, Window
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup



# Creates an "output" folder next to this Python file.
script_directory = Path(__file__).resolve().parent
output_directory = script_directory / "output"

output_directory.mkdir(
    parents=True,
    exist_ok=True
)


Window.fullscreen = "auto"

camera1 = cv2.VideoCapture(
    "/dev/video0",
    cv2.CAP_V4L2
)

camera2 = cv2.VideoCapture(
    "/dev/video2",
    cv2.CAP_V4L2
)


# Most recently captured original frame from each camera.
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

# Function to size a frame inside a screen area without changing its aspect ratio.
def fit_to_area(frame, width, height):
    width = max(int(width), 1)
    height = max(int(height), 1)

    frame_height, frame_width = frame.shape[:2]

    scale = min(
        width / frame_width,
        height / frame_height
    )

    new_width = max(int(frame_width * scale), 1)
    new_height = max(int(frame_height * scale), 1)

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

# Function for side-by-side camera feeds.

def split_screen(frame1, frame2, width, height):
    width = max(int(width), 2)
    height = max(int(height), 1)

    left_width = width // 2
    right_width = width - left_width

    frame1 = fit_to_area(
        frame1,
        left_width,
        height
    )

    frame2 = fit_to_area(
        frame2,
        right_width,
        height
    )

    return cv2.hconcat([
        frame1,
        frame2
    ])

# Function to full-screen one camera feed.
def full_screen(camera_number, frame1, frame2, width, height):
    if camera_number == 1:
        frame = frame1

    elif camera_number == 2:
        frame = frame2

    else:
        print(f"Invalid camera number: {camera_number}")
        return None

    return fit_to_area(
        frame,
        width,
        height
    )

# Function to create a unique filename.
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


# Function to save an image from a specified camera.
def save_image(camera_number):
    if camera_number not in latest_frames:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return False

    frame = latest_frames[camera_number]

    if frame is None:
        print(
            f"No frame available from "
            f"camera {camera_number}"
        )
        return False

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
        return True

    print(
        f"Failed to save image from "
        f"camera {camera_number}"
    )
    return False


# Get the FPS reported by a camera.
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


# Function to start recording a specified camera.
def start_recording(camera_number):
    if camera_number not in video_writers:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return False

    # Don't start another recording if this camera is already recording.
    if video_writers[camera_number] is not None:
        print(
            f"Camera {camera_number} "
            f"is already recording"
        )
        return False

    frame = latest_frames[camera_number]

    if frame is None:
        print(
            f"No frame available from "
            f"camera {camera_number}"
        )
        return False

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
        return False

    video_writers[camera_number] = writer

    print(
        f"Started recording camera "
        f"{camera_number}: {file_name}"
    )

    print(
        f"Recording FPS: {fps}"
    )

    return True


# Function to stop recording a specified camera.
def stop_recording(camera_number):
    if camera_number not in video_writers:
        print(
            f"Invalid camera number: "
            f"{camera_number}"
        )
        return False

    writer = video_writers[camera_number]

    if writer is None:
        print(
            f"Camera {camera_number} "
            f"is not recording"
        )
        return False

    writer.release()
    video_writers[camera_number] = None

    print(
        f"Stopped recording camera "
        f"{camera_number}"
    )

    return True

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

# class for handling downward swipe for pop-up
class SwipeDismissPopup(Popup):
    SWIPE_DISTANCE = dp(60)
    SWIPE_AXIS_RATIO = 1.2

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud["popup_swipe_start"] = touch.pos

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        start_position = touch.ud.get(
            "popup_swipe_start"
        )

        if start_position is not None:
            start_x, start_y = start_position
            end_x, end_y = touch.pos

            delta_x = end_x - start_x
            delta_y = end_y - start_y

            horizontal_distance = abs(delta_x)
            vertical_distance = abs(delta_y)

            # Downward swipe
            if (
                delta_y <= -self.SWIPE_DISTANCE
                and vertical_distance >= (
                    horizontal_distance * self.SWIPE_AXIS_RATIO
                )
            ):
                self.dismiss()
                return True

        return super().on_touch_up(touch)
        
        
class CameraViewer(FloatLayout):
    # Minimum distance a touch/mouse drag must travel to count as a swipe.
    SWIPE_DISTANCE = dp(60)

    # A gesture must favor one axis by this ratio before it is treated as a swipe.
    SWIPE_AXIS_RATIO = 1.2

    # Horizontal order of the three display modes.
    DISPLAY_MODES = [
        "camera1",
        "split",
        "camera2"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Default display mode
        self.mode = "split"

        # The Kivy Image widget replaces cv2.imshow().
        self.camera_image = Image(
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0
            },
            fit_mode="fill"
        )

        self.add_widget(
            self.camera_image
        )

        # Reuse one Texture when the displayed frame size stays the same.
        self.display_texture = None
        self.display_texture_size = None

        # Kivy keyboard events replace cv2.waitKeyEx().
        Window.bind(
            on_key_down=self.handle_key_down
        )

        # Kivy needs its own event loop, so Clock calls update_frames repeatedly.
        # An interval of 0 means "once per Kivy frame". 
        self.frame_event = Clock.schedule_interval(
            self.update_frames,
            0
        )

    def update_frames(self, _delta_time):

        ret1, frame1 = camera1.read()
        ret2, frame2 = camera2.read()

        if not ret1:
            print(
                "Could not read "
                "/dev/video0"
            )
            App.get_running_app().stop()
            return

        if not ret2:
            print(
                "Could not read "
                "/dev/video2"
            )
            App.get_running_app().stop()
            return

        # Store the original, unscaled frames for screenshots and recordings.
        latest_frames[1] = frame1
        latest_frames[2] = frame2

        # Record each camera independently.
        if video_writers[1] is not None:
            video_writers[1].write(
                frame1
            )

        if video_writers[2] is not None:
            video_writers[2].write(
                frame2
            )

        display_width = max(
            int(self.camera_image.width),
            1
        )

        display_height = max(
            int(self.camera_image.height),
            1
        )

        if self.mode == "split":
            display_frame = split_screen(
                frame1,
                frame2,
                display_width,
                display_height
            )

        elif self.mode == "camera1":
            display_frame = full_screen(
                1,
                frame1,
                frame2,
                display_width,
                display_height
            )

        elif self.mode == "camera2":
            display_frame = full_screen(
                2,
                frame1,
                frame2,
                display_width,
                display_height
            )

        else:
            print(
                f"Invalid display mode: "
                f"{self.mode}"
            )
            self.mode = "split"
            return


        self.show_frame(
            display_frame
        )

    # Convert an OpenCV BGR frame into a Kivy Texture and display it.
    def show_frame(self, frame):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # OpenCV and Kivy use opposite vertical image origins.
        rgb_frame = cv2.flip(
            rgb_frame,
            0
        )

        frame_height, frame_width = rgb_frame.shape[:2]
        texture_size = (
            frame_width,
            frame_height
        )

        if (
            self.display_texture is None
            or self.display_texture_size != texture_size
        ):
            self.display_texture = Texture.create(
                size=texture_size,
                colorfmt="rgb"
            )

            self.display_texture_size = texture_size

        self.display_texture.blit_buffer(
            rgb_frame.tobytes(),
            colorfmt="rgb",
            bufferfmt="ubyte"
        )

        self.camera_image.texture = self.display_texture

    # Remember where a touch/mouse drag started.
    def on_touch_down(self, touch):

        if self.camera_image.collide_point(*touch.pos):
            touch.ud["camera_viewer_start"] = touch.pos
            return True

        return super().on_touch_down(touch)

    # Interpret horizontal and upward swipes.
    def on_touch_up(self, touch):

        start_position = touch.ud.get(
            "camera_viewer_start"
        )

        if start_position is None:
            return super().on_touch_up(touch)

        start_x, start_y = start_position
        end_x, end_y = touch.pos

        delta_x = end_x - start_x
        delta_y = end_y - start_y

        horizontal_distance = abs(delta_x)
        vertical_distance = abs(delta_y)

        # Horizontal swipe:
        # camera1 <-> split <-> camera2
        if (
            horizontal_distance >= self.SWIPE_DISTANCE
            and horizontal_distance >= (
                vertical_distance * self.SWIPE_AXIS_RATIO
            )
        ):
            self.handle_horizontal_swipe(
                delta_x
            )
            return True

        # Upward swipe:
        # Open options for the camera that was swiped upward.
        if (
            delta_y >= self.SWIPE_DISTANCE
            and vertical_distance >= (
                horizontal_distance * self.SWIPE_AXIS_RATIO
            )
        ):
            camera_number = self.camera_at_position(
                start_x
            )

            if camera_number is not None:
                self.show_camera_options(
                    camera_number
                )

            return True

        return True

    # handle left and right swipes for camera1 <-> split <-> camera2
    def handle_horizontal_swipe(self, delta_x):

        try:
            current_index = self.DISPLAY_MODES.index(
                self.mode
            )

        except ValueError:
            self.mode = "split"
            return

        if delta_x < 0:
            # Swipe left: move toward camera 2.
            new_index = min(
                current_index + 1,
                len(self.DISPLAY_MODES) - 1
            )

        else:
            # Swipe right: move toward camera 1.
            new_index = max(
                current_index - 1,
                0
            )

        self.mode = self.DISPLAY_MODES[
            new_index
        ]

    # Return which camera camera mode for upward swipe
    def camera_at_position(self, x_position):

        if self.mode == "camera1":
            return 1

        if self.mode == "camera2":
            return 2

        if self.mode == "split":
            middle_x = self.x + (self.width / 2)

            if x_position < middle_x:
                return 1

            return 2

        return None

    # Touch control handling 
    def show_camera_options(self, camera_number):

        options_layout = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12)
        )

        camera_label = Label(
            text=f"Camera {camera_number}",
            size_hint_y=None,
            height=dp(42)
        )

        screenshot_button = Button(
            text="Save Screenshot",
            size_hint_y=None,
            height=dp(64)
        )

        if video_writers[camera_number] is None:
            recording_button_text = "Start Recording"
        else:
            recording_button_text = "Stop Recording"

        recording_button = Button(
            text=recording_button_text,
            size_hint_y=None,
            height=dp(64)
        )

        close_button = Button(
            text="Close",
            size_hint_y=None,
            height=dp(56)
        )

        options_layout.add_widget(
            camera_label
        )
        options_layout.add_widget(
            screenshot_button
        )
        options_layout.add_widget(
            recording_button
        )
        options_layout.add_widget(
            close_button
        )

        popup = SwipeDismissPopup(
            title=f"Camera {camera_number} Options",
            content=options_layout,
            size_hint=(0.82, 0.78),
            auto_dismiss=True
        )

        screenshot_button.bind(
            on_release=lambda _button: self.handle_screenshot_option(
                camera_number,
                popup
            )
        )

        recording_button.bind(
            on_release=lambda _button: self.handle_recording_option(
                camera_number,
                popup
            )
        )

        close_button.bind(
            on_release=lambda _button: popup.dismiss()
        )

        popup.open()

    # Save a screenshot and close the options popup
    def handle_screenshot_option(self, camera_number, popup):

        save_image(
            camera_number
        )

        popup.dismiss()

    # Start or stop recording, depending on the camera's current state.
    def handle_recording_option(self, camera_number, popup):

        if video_writers[camera_number] is None:
            start_recording(
                camera_number
            )

        else:
            stop_recording(
                camera_number
            )

        popup.dismiss()

    def handle_key_down(
        self,
        _window,
        key,
        _scancode,
        _codepoint,
        _modifiers
    ):

        if key == Keyboard.keycodes["q"]:
            App.get_running_app().stop()
            return True

        if key == Keyboard.keycodes["s"]:
            self.mode = "split"
            return True

        if key == Keyboard.keycodes["a"]:
            self.mode = "camera1"
            return True

        if key == Keyboard.keycodes["d"]:
            self.mode = "camera2"
            return True

        if key == Keyboard.keycodes["z"]:
            save_image(1)
            return True

        if key == Keyboard.keycodes["c"]:
            save_image(2)
            return True

        if key == Keyboard.keycodes["f1"]:
            start_recording(1)
            return True

        if key == Keyboard.keycodes["f2"]:
            start_recording(2)
            return True

        if key == Keyboard.keycodes["1"]:
            stop_recording(1)
            return True

        if key == Keyboard.keycodes["2"]:
            stop_recording(2)
            return True

        return False
    
    # Stop scheduled frame updates and remove Kivy input bindings.
    def stop_updates(self):

        if self.frame_event is not None:
            self.frame_event.cancel()
            self.frame_event = None

        Window.unbind(
            on_key_down=self.handle_key_down
        )

class RaspberryPiCameraViewerApp(App):
    def build(self):
        return CameraViewer()

    # Finalize recordings and release both cameras when the app closes.
    def on_stop(self):

        if self.root is not None:
            self.root.stop_updates()

        if video_writers[1] is not None:
            stop_recording(1)

        if video_writers[2] is not None:
            stop_recording(2)

        camera1.release()
        camera2.release()


if __name__ == "__main__":
    RaspberryPiCameraViewerApp().run()
