# Main File

Author: Mike Smith

Date of Implementation: 12/04/2023

## Desription:

The main file contains two threads:
- `class MainThread(QtCore.QThread)`
    - Back-end thread
    - Handles camera access, motion tracking
    and counting reps
- `class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow)`
    - Front-end thread
    - Handles user input to the graphical user interface

## Main Worker Thread methods:

`def __init__(self, parent=None)`
- Initialises all variables to be used in this thread.

`def run(self)`
- Main worker thread
- Called when `self.start()` is called

`def stop(self)`
- Stops the worker thread

`def start_video_capture(self)`
- Starts video capture
- Uses webcam by default

`def get_video_capture(self, cap, name=None)`
- Gets video capture from webcam or video file
- `cap`: video capture object returned from calling `cv2.VideoCapture()`
- `name`: filename of the file to be opened. Defaults to `none` to open webcam.
- returns a `cap` object from `cv2.VideoCapture()`, else returns `None` if failed to create a `cap` object.

`def set_frame_dimensions(self, cap, source)`
- Set the camera or video resolution and show in terminal
- `cap`: video capture object
- `source`: video source: video or webcam

`def get_file(self, name)`
- Gets the file specified by the user
- Checks if the file is a valid format supported by the program. See the "File Module" for a list of supported file formats.
- `name`: name of the file to be retrieved

`def generate_file(self, generate)`
- callback function for the main-window thread
- `generate`: a boolean value to specify whether or not a csv file should be generated at the end of the session

`def get_frame_rate(self, frame_times)`
- Calculates frame rate
- `frame_times`: dictionary containing the timestamps for the previous and current frames.
- Returns the calculate frame rate.

`def get_recording_status(self)`
- Gets current recording status
- Returns True if recording, else returns False
- Used in the main window thread to update gui

`def get_input_source(self)`
- Gets current input source
- Returns the input source: video or webcam

`def start_stop_recording(self)`
- Starts and stops recording
- Called from the main window thread whenever the start/stop button is pressed

`def pause(self)`
- Pauses the recording

`def get_pause_status(self)`
- Gets the current pause status
- Used in the main window thread
- Returns the pause status

`def update_name_id(self, name_id)`
- Updates the session identifier with patient name or ID
- Used to name the outputted CSV files to associate them with each patient
- `name_id`: string containing the patient or ID, passed in from the main-window thread

`def reset_all_count(self)`
- Resets count for all movements
- Can be used to reset other parameters at the start of a recording session
- Make sure to update when adding new movements

`def add_movements(self)`
- Add movements to be tracked
- Calls the "Movement Module"

`def count_movements(self)`
- Used to count movements during a session
- Will only count movements if enabled
- Emits the updated movement count to the main-window thread to be displayed on the user interface.

`def get_tracking_movements(self)`
- Returns a dictionary containing all movements
- Called by the main-window thread to update gui

## Main Mindow Thread methods:

`def __init__(self, parent=None)`
- Sets up graphical user interface
- Creates an instance of the main-worker thread.
- Connects the following signals:
    - All back-end signals
    - Motion tracking signals
    - Pushbutton signals
    - Line-edit signals
    - Action menu triggers

`def update_frame(self, img)`
- Updates GUI interface whenever a new video frame is received from the main worker thread
- `img`: object containing the current video frame, emitted by the main-worker thread

`def display_frame_rate(self, frame_rate)`
- Shows the current frame rate on the gui 
- Takes the average of the last ten frame rates for smoother output
- `frame_rate`: the current calculated frame rate emitted from the main-worker thread

`def display_session_time(self, time)`
- Displays the time since the start of session formatted as "h:mm:ss"
- `time`: the elapsed time since the start of the session

`def update_start_pushButton(self)`
- Updates the gui interface whenever the start / stop button is pressed

`def update_name_id(self)`
- Called whenever the user enters anything into the name line edit
- Passes this information to the main-worker thread

`def open_file(self)`
- Callback for when the open action is triggered from the file menu
- Gets the file name / path and sends to the main-worker thread

`def open_webcam(self)`
- Callback for when the webcam action is triggered from the file menu
- Starts the video capture from the webcam in the main-worker thread

`def generate_file(self)`
- Callback for when the generate csv file action is triggeres from the file menu
- Passes the current "generate file" status to the main-worker thread

