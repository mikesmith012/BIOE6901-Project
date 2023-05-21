"""
main.py

The main file contains two thread classes:
- `class MainThread(QtCore.QThread)`
    - Back-end thread
    - Handles camera access, motion tracking
    and counting reps
- `class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow)`
    - Front-end thread
    - Handles user input to the graphical user interface

see "doc/main.md" for more details

"""

import cv2, sys, time, util, config
from PyQt5 import QtCore, QtWidgets, QtGui
from gui import Ui_MainWindow
from statistics import mean
from movement import Movement
from motion import Motion
from file import File


__author__ = "Mike Smith"
__email__ = "dongming.shi@uqconnect.edu.au"
__date__ = "12/04/2023"
__status__ = "Prototype"
__credits__ = ["Agnethe Kaasen", "Live Myklebust", "Amber Spurway"]


class MainThread(QtCore.QThread):
    """
    back-end worker thread: handles camera access, motion tracking
    and counting reps

    """

    image = QtCore.pyqtSignal(QtGui.QImage)
    frame_rate = QtCore.pyqtSignal(float)
    session_time = QtCore.pyqtSignal(int)

    """ back-end signals to handle counting reps """
    right_arm_ext = QtCore.pyqtSignal(str)
    left_arm_ext = QtCore.pyqtSignal(str)
    sit_to_stand = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._cap = None
        self._is_recording = False
        self._is_paused = False
        self._pause_time = 0
        self._tracking_movements = {}
        self._start_time = None
        self._stop_time = None
        self._session_time = None
        self._source = None
        self._delay = 0
        self._read_file = None
        self._write_file = None
        self._save_file = True
        self._name_id = ""

    def run(self):
        """
        main worker thread

        """
        self._active = True
        self.start_video_capture()

        """ frame rate (for debugging) """
        frame_times = {"curr time": 0, "prev time": 0}

        """ init motion capture """
        self._motion = Motion()

        """ add and init movements """
        self.add_movements()
        self.reset_all_count()

        """ while camera / video file is opened """
        while self._cap.isOpened() and self._active:
            ret, self._img = self._cap.read()

            """ if camera not accessed or end of video """
            if ret == False or self._img is None:
                """
                if error accessing camera or end of video and program is not recording:
                - keep iterating through the main while loop until an image signal is received

                """
                if not self._is_recording:
                    continue

                """ 
                if error accessing camera or end of video and program was recording:
                - stop the recording
                - wait until recording starts again (by playing another video) or
                - wait until user switches back to the webcam
                
                """
                self.start_stop_recording()
                while not self._is_recording and self._source != util.WEBCAM:
                    pass
                continue

            """ get frame dimensions """
            height, width, _ = self._img.shape
            self._motion.crop = {"start": util.INIT, "end": (width, height)}

            """ display frame rate """
            frame_rate = self.get_frame_rate(frame_times)
            self.frame_rate.emit(frame_rate)

            """ get the time since start of session """
            if (
                self._start_time is not None
                and self._is_recording
                and not self._is_paused
            ):
                self._session_time = time.time() - self._start_time - self._pause_time
                self.session_time.emit(int(self._session_time))

            """ track motion and count movements (only when recording) """
            if self._is_recording and not self._is_paused:
                self._pose_landmarks = []
                self._img, self._pixels = self._motion.track_motion(
                    self._img,
                    self._pose_landmarks,
                )

                """ count the number of reps for each movement """
                self.count_movements()

                """ parse movement data to file object """
                if self._session_time is not None:
                    self._write_file.parse_movements(
                        self._tracking_movements,
                        self._pose_landmarks,
                        self._session_time,
                    )

            """ flip image if accessed from webcam """
            if self._source == util.WEBCAM:
                self._img = cv2.flip(self._img, 1)

            """ emit image signal to the main-window thread to be displayed """
            self._img = cv2.cvtColor(self._img, cv2.COLOR_BGR2RGB)
            QtImg = QtGui.QImage(
                self._img.data, width, height, QtGui.QImage.Format_RGB888
            ).scaled(int(1280 - 128 / 8), int(720 - 72 / 8), QtCore.Qt.KeepAspectRatio)
            self.image.emit(QtImg)

            """ maintain max frame rate of ~30fps (mainly for smooth video playback) """
            self._delay = self._delay + 0.001 if frame_rate - 30 > 0 else 0
            time.sleep(self._delay)

            """ pause video if stop button is pressed """
            while not self._is_recording and self._source != util.WEBCAM:
                pass

        """ handles program exit """
        cv2.destroyAllWindows()
        self._cap.release()

    def stop(self):
        """
        stops the worker thread

        """
        self._active = False
        self.wait()

    def start_video_capture(self):
        """
        starts video capture from webcam by default

        """
        if self._source == util.WEBCAM:
            return

        self._cap = self.get_video_capture(self._cap)

    def get_video_capture(self, cap, name=None):
        """
        get video capture from webcam or video file

        """
        if name is not None:
            cap = cv2.VideoCapture(name)
            self._source = util.VIDEO
            self.set_frame_dimensions(cap, "video")

            if not self._is_recording:
                self.start_stop_recording()
            else:
                self.start_stop_recording()
                self.start_stop_recording()

            self._start_time = time.time()
            self.reset_all_count()

            if cap.isOpened():
                return cap

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self._source = util.WEBCAM
        self.set_frame_dimensions(cap, "webcam")

        if self._is_recording:
            self.start_stop_recording()

        if cap.isOpened():
            return cap

        print("error opening video stream or file")
        return None

    def set_frame_dimensions(self, cap, source):
        """
        set the camera or video resolution and show in terminal (for debugging)

        """
        if cap is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, util.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, util.FRAME_HEIGHT)

            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"{source} resolution: {int(width)} x {int(height)}")

    def get_file(self, name):
        """
        get the file specified by the user

        """
        self._read_file = File()
        file_type = self._read_file.get_file_type(name)

        """ check that the file is valid and supported by program """
        if file_type == util.MP4:
            self._cap = self.get_video_capture(self._cap, name=name)
            print(f'video file: "{name}"')

        elif file_type == util.CSV:
            print(f'csv file: "{name}"')

        elif file_type == util.FILE_NOT_SUPPORTED:
            invalid_file_msg_box = QtWidgets.QMessageBox()
            invalid_file_msg_box.setWindowTitle("File Not Supported")
            invalid_file_msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            invalid_file_msg_box.setText(
                "The file you have chosen is not supported by the program.\n\n"
                + "Please choose a different file and try again."
            )
            invalid_file_msg_box.exec()

    def generate_file(self, generate):
        """
        callback function for the main-window thread to update whether or not
        a csv file should be generated at the end of the session

        """
        self._save_file = generate

    def handle_exit(self, event):
        """
        handles user exit
        will prompt the user to save recording if user exits while recording in active

        """

        if self._is_recording and self._save_file:
            handle_exit_msg_box = QtWidgets.QMessageBox()
            handle_exit_msg_box.setWindowTitle("Save session?")
            handle_exit_msg_box.setIcon(QtWidgets.QMessageBox.Question)
            handle_exit_msg_box.setText("Would you like to save the recorded session?")
            handle_exit_msg_box.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            handle_exit_msg_box.exec()

            button_handler = handle_exit_msg_box.clickedButton()
            button_clicked = handle_exit_msg_box.standardButton(button_handler)
            if button_clicked == QtWidgets.QMessageBox.Yes:
                self._write_file.write(self._name_id)

    def get_frame_rate(self, frame_times):
        """
        calculates frame rate: used for testing

        """
        frame_times["curr time"] = time.time()
        frame_rate = 1 / (frame_times["curr time"] - frame_times["prev time"])
        frame_times["prev time"] = frame_times["curr time"]
        return frame_rate

    def get_recording_status(self):
        """
        gets current recording status
        returns True if recording, else returns False
        used in the main window thread to update gui

        """
        return self._is_recording

    def get_input_source(self):
        """
        gets current input source (video or webcam)

        """
        return self._source

    def start_stop_recording(self):
        """
        starts and stops recording
        called from the main window thread whenever the start/stop button is pressed

        """
        self._is_recording = not self._is_recording

        if self._is_recording:
            """
            create new file object

            """
            self._write_file = File(save=self._save_file)

            if self._stop_time is not None and (
                self._source == util.VIDEO or self._is_paused
            ):
                self._start_time = time.time() - (self._stop_time - self._start_time)
            else:
                self._start_time = time.time()

            """ resets all movement count if accessed from webcam """
            if self._source == util.WEBCAM:
                self.reset_all_count()

        else:
            self._stop_time = time.time()

            """ write to csv file """
            self._write_file.write(self._name_id)

    def pause(self):
        """
        pauses the recording

        """
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_start_time = time.time()
        else:
            self._pause_stop_time = time.time()
            self._pause_time += self._pause_stop_time - self._pause_start_time

    def get_pause_status(self):
        """
        returns the current pause status
        used by the main window thread to update gui

        """
        return self._is_paused

    def update_name_id(self, name_id):
        """
        updated the name of id
        called from the main window thread when user updated line edit

        """
        self._name_id = name_id

    def reset_all_count(self):
        """
        resets count for all movements
        make sure to update when adding new movements

        """
        self._pause_time = 0
        self._is_paused = False

        self._right_arm_ext.reset_count()
        self._left_arm_ext.reset_count()
        self._sit_to_stand.reset_count()

    def add_movements(self):
        """
        add right arm extensions

        """
        self._right_arm_ext = Movement(
            config.RIGHT_ARM_EXT_ANGULAR_THRESH,
            config.RIGHT_ARM_EXT_POSITIONAL_THRESH,
            True,
            debug=False,
        )
        self._tracking_movements.update({"right arm ext": self._right_arm_ext})

        """ 
        add left arm extensions 
        
        """
        self._left_arm_ext = Movement(
            config.LEFT_ARM_EXT_ANGULAR_THRESH,
            config.LEFT_ARM_EXT_POSITIONAL_THRESH,
            True,
            debug=False,
        )
        self._tracking_movements.update({"left arm ext": self._left_arm_ext})

        """ 
        add sit to stand movement 
        
        """
        self._sit_to_stand = Movement(
            config.SIT_TO_STAND_ANGULAR_THRESH,
            config.SIT_TO_STAND_POSITIONAL_THRESH,
            True,
            ignore_vis=True,
            debug=False,
        )
        self._tracking_movements.update({"sit to stand": self._sit_to_stand})

    def count_movements(self):
        """
        right arm extensions (if enabled)

        """
        if self._right_arm_ext.get_tracking_status():
            self._img, self._right_arm_ext_count = self._right_arm_ext.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            self.right_arm_ext.emit(str(self._right_arm_ext_count))

        """ 
        left arm extensions (if enabled) 
        
        """
        if self._left_arm_ext.get_tracking_status():
            self._img, self._left_arm_ext_count = self._left_arm_ext.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            self.left_arm_ext.emit(str(self._left_arm_ext_count))

        """ 
        sit to stand (if enabled) 
        
        """
        if self._sit_to_stand.get_tracking_status():
            self._img, self._sit_to_stand_count = self._sit_to_stand.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            self.sit_to_stand.emit(str(self._sit_to_stand_count))

    def get_tracking_movements(self):
        """
        returns a dictionary containing all movements
        called by the main-window thread to update gui

        """
        return self._tracking_movements.copy()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    front-end main-window thread: handles graphical user interface

    """

    def __init__(self, parent=None):
        super().__init__(parent)

        """ set up gui """
        self.setupUi(self)
        self.setWindowTitle("BIOE6901 Project")

        """ create the worker thread """
        self._main_thread = MainThread()
        self._main_thread.start()
        # self._main_thread.setTerminationEnabled(True)

        """ connect back-end signals """
        self._main_thread.image.connect(self.update_frame)
        self._main_thread.frame_rate.connect(self.display_frame_rate)
        self._main_thread.session_time.connect(self.display_session_time)

        """ connect motion traking signals """
        self._main_thread.right_arm_ext.connect(self.display_right_arm_ext_count)
        self._main_thread.left_arm_ext.connect(self.display_left_arm_ext_count)
        self._main_thread.sit_to_stand.connect(self.display_sit_to_stand_count)

        """ connect start/stop pushbutton """
        self.start_pushButton.clicked.connect(self._main_thread.start_stop_recording)
        self.start_pushButton.clicked.connect(self.update_start_pushButton)

        """ connect pause pushbutton """
        self.pause_pushButton.clicked.connect(self._main_thread.pause)

        """ connect line edit """
        self.name_id_lineEdit.editingFinished.connect(self.update_name_id)

        """ connect action triggers """
        self.actionOpen.triggered.connect(self.open_file)
        self.actionWebcam.triggered.connect(self.open_webcam)
        self.actionGenerate_CSV_File.triggered.connect(self.generate_file)

        self._frame_rates = []

    def closeEvent(self, event):
        """
        callback for when the user exit the program

        """
        self._main_thread.handle_exit(event)

    def update_frame(self, img):
        """
        updated gui interface whenever a new video frame is received from the
        main worker thread

        """
        self.img_label.setPixmap(QtGui.QPixmap(img))

        if self._main_thread.get_recording_status():
            self.start_pushButton.setText("Stop")

            if self._main_thread.get_input_source() == util.WEBCAM:
                self.pause_pushButton.setVisible(True)

        else:
            self.start_pushButton.setText("Start")
            self.pause_pushButton.setVisible(False)

        if self._main_thread.get_pause_status():
            self.pause_pushButton.setText("Resume")
        else:
            self.pause_pushButton.setText("Pause")

    def display_frame_rate(self, frame_rate):
        """
        shows the current frame rate on the gui
        takes the average of the last ten frame rates for smoother output

        """
        self._frame_rates.append(frame_rate)
        if len(self._frame_rates) > 10:
            self.framerate_label.setText(
                f"Frame Rate: {round(mean(self._frame_rates), 1)} fps"
            )
            self._frame_rates = []

    def display_session_time(self, time):
        """
        displays the time since the start of session
        formatted as "h:mm:ss"

        """
        self.sessiontime_label.setText(
            "Session Time: %d:%02d:%02d" % (time // 3600, time // 60, time % 60)
        )

    def update_start_pushButton(self):
        """
        updates the gui interface whenever the start / stop button is pressed

        """
        self._movements = self._main_thread.get_tracking_movements()

        if self._main_thread.get_recording_status():
            """
            print tracking movements status to terminal
            (only used for testing)

            """
            print("")
            for name, movement in self._movements.items():
                print(f"{name}: {movement.get_tracking_status()}")
            print("")

    def update_name_id(self):
        self._main_thread.update_name_id(self.name_id_lineEdit.text())

    def open_file(self):
        """
        callback for when the open action is triggered from the file menu
        gets the file name / path and sends to the main-worker thread

        """
        self._file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "./")
        self._main_thread.get_file(self._file_name[0])

    def open_webcam(self):
        """
        callback for when the webcam action is triggered from the file menu
        starts the video capture from the webcam in the main-worker thread

        """
        self._main_thread.start_video_capture()

    def generate_file(self):
        """
        callback for when the generate csv file action is triggeres from the file menu
        passes the current "generate file" status to the main-worker thread

        """
        self._main_thread.generate_file(self.actionGenerate_CSV_File.isChecked())

    """ 
    main-window methods for updating the count values for counting movements

    """

    def display_right_arm_ext_count(self, count):
        self.right_arm_ext_count_label.setText(f"Right Arm Extensions: {count}")

    def display_left_arm_ext_count(self, count):
        self.left_arm_ext_count_label.setText(f"Left Arm Extensions: {count}")

    def display_sit_to_stand_count(self, count):
        self.sit_to_stand_count_label.setText(f"Sit to Stand: {count}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
