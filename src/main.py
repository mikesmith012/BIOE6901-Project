import cv2, sys, time, util
from PyQt5 import QtCore, QtWidgets, QtGui
from gui import Ui_MainWindow
from statistics import mean
from movement import Movement
from motion import Motion
from file import File

""" 
works with python version 3.10

Setup (Mac / Linux)
1.  Create python virtual environment: `python3 -m venv venv`
2.  Activate virtual environment: `source venv/bin/activate`
3.  Install dependencies: `python3 -m pip install -r req.txt`
4.  Run the program: `python3 src/main.py`
5.  To deactivate virtual environment: `deactivate`

Setup (Windows)
1.  Create python virtual environment: `py -m venv venv`
2.  Activate virtual environment: `.\\venv\Scripts\activate`
3.  Install dependencies: `py -m pip install -r req.txt`
4.  Run the program: `py src/main.py`
5.  To deactivate virtual environment: `deactivate`

generate gui file: `pyuic5 -x ui/gui.ui -o gui.py`

"""


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
        self._tracking_movements = {}
        self._start_time = None
        self._stop_time = None
        self._session_time = None
        self._source = None
        self._delay = 0
        self._read_file = None
        self._write_file = None

    def run(self):
        """
        main worker thread

        """
        self._active = True
        self._cap = self.get_video_capture(self._cap)

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
            if (ret == False or self._img is None) and self._is_recording:
                self.start_stop_recording()
                while not self._is_recording:
                    pass
                continue

            """ get frame dimensions """
            height, width, _ = self._img.shape
            self._motion.crop = {"start": util.INIT, "end": (width, height)}

            """ display frame rate """
            frame_rate = self.get_frame_rate(frame_times)
            self.frame_rate.emit(frame_rate)

            """ get the time since start of session """
            if self._start_time is not None and self._is_recording:
                self._session_time = time.time() - self._start_time
                self.session_time.emit(int(self._session_time))

            """ track motion and count movements (only when recording) """
            if self._is_recording:
                self._pose_landmarks = []
                self._img, self._pixels = self._motion.track_motion(
                    self._img,
                    self._pose_landmarks,
                )
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
            while self._source == util.VIDEO and not self._is_recording:
                pass

        cv2.destroyAllWindows()
        self._cap.release()

    def stop(self):
        """
        stops the worker thread

        """
        self._active = False
        self.wait()

    def get_video_capture(self, cap, name=None):
        """
        get video capture from webcam or video file

        """
        
        if name is not None:
            cap = cv2.VideoCapture(name)
            self._source = util.VIDEO
            self.get_frame_details(cap, "video")

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
        self.get_frame_details(cap, "webcam")

        if cap.isOpened():
            return cap

        print("error opening video stream or file")
        return None

    def get_frame_details(self, cap, source):
        """
        get camera or video resolution and show in terminal (for debugging)

        """
        if cap is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, util.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, util.FRAME_HEIGHT)

            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"{source} resolution: {int(width)} x {int(height)}")

    def get_file(self, name):
        """
        read the file specified by the user

        """
        self._read_file = File()
        if self._read_file.get_file_type(name) == util.MP4:
            print(name)
            self._cap = self.get_video_capture(self._cap, name=name)
        elif self._read_file.get_file_type(name) == util.CSV:
            print(name)
        else:
            print("file not supported")

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
            """create new file object"""
            self._write_file = File()

            """ handles pausing for videos """
            if self._stop_time is not None and self._source == util.VIDEO:
                self._start_time = time.time() - (self._stop_time - self._start_time)
            else:
                self._start_time = time.time()

            """ resets all movement count if accessed from webcam """
            if self._source == util.WEBCAM:
                self.reset_all_count()

        else:
            self._stop_time = time.time()

            """ write to csv file """
            self._write_file.write()

    def reset_all_count(self):
        """
        resets count for all movements
        make sure to update when adding new movements
        """
        self._right_arm_ext.reset_count()
        self._left_arm_ext.reset_count()
        self._sit_to_stand.reset_count()

    def add_movements(self):
        """add right arm extensions"""
        self._right_arm_ext = Movement(
            [
                (Motion.right_wrist, Motion.right_elbow, Motion.left_shoulder, 130),
                (Motion.right_elbow, Motion.right_shoulder, Motion.right_hip, 30),
            ],
            [
                (Motion.right_elbow, Motion.right_shoulder, ">", 1),
            ],
            True,
            debug=True,
        )
        self._tracking_movements.update({"right arm ext": self._right_arm_ext})

        """ add left arm extensions """
        self._left_arm_ext = Movement(
            [
                (Motion.left_wrist, Motion.left_elbow, Motion.left_shoulder, 130),
                (Motion.left_elbow, Motion.left_shoulder, Motion.left_hip, 30),
            ],
            [
                (Motion.left_elbow, Motion.left_shoulder, ">", 1),
            ],
            True,
            debug=True,
        )
        self._tracking_movements.update({"left arm ext": self._left_arm_ext})

        """ add sit to stand movement """
        self._sit_to_stand = Movement(
            [
                (Motion.right_ankle, Motion.right_knee, Motion.right_hip, 150),
                (Motion.left_ankle, Motion.left_knee, Motion.left_hip, 150),
                (Motion.right_knee, Motion.right_hip, Motion.right_shoulder, 150),
                (Motion.left_knee, Motion.left_hip, Motion.left_shoulder, 150),
            ],
            [
                (Motion.left_knee, Motion.left_hip, ">", 0.2),
                (Motion.right_knee, Motion.right_hip, ">", 0.2),
            ],
            True,
            ignore_vis=True,
            debug=True,
        )
        self._tracking_movements.update({"sit to stand": self._sit_to_stand})

    def count_movements(self):
        """right arm extensions (if enabled)"""
        if self._right_arm_ext.get_tracking_status():
            self._img, self._right_arm_ext_count = self._right_arm_ext.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            self.right_arm_ext.emit(str(self._right_arm_ext_count))

        """ left arm extensions (if enabled) """
        if self._left_arm_ext.get_tracking_status():
            self._img, self._left_arm_ext_count = self._left_arm_ext.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            self.left_arm_ext.emit(str(self._left_arm_ext_count))

        """ sit to stand (if enabled) """
        if self._sit_to_stand.get_tracking_status():
            self._img, self._sit_to_stand_count = self._sit_to_stand.count_movement(
                self._pose_landmarks,
                self._pixels,
                self._img,
                self._source,
            )
            # print(self._sit_to_stand_count)
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

        """ connect back-end signals """
        self._main_thread.image.connect(self.update_frame)
        self._main_thread.frame_rate.connect(self.display_frame_rate)
        self._main_thread.session_time.connect(self.display_session_time)

        """ connect motion traking signals """
        self._main_thread.right_arm_ext.connect(self.display_right_arm_ext_count)
        self._main_thread.left_arm_ext.connect(self.display_left_arm_ext_count)
        self._main_thread.sit_to_stand.connect(self.display_sit_to_stand_count)

        """ connect start/stop bushbutton """
        self.start_pushButton.clicked.connect(self._main_thread.start_stop_recording)
        self.start_pushButton.clicked.connect(self.update_start_pushButton)

        """ connect action triggers """
        self.actionOpen.triggered.connect(self.open_file)

        self._frame_rates = []

    def update_frame(self, img):
        self.img_label.setPixmap(QtGui.QPixmap(img))

        if self._main_thread.get_recording_status():
            self.start_pushButton.setText("Stop")
        else:
            self.start_pushButton.setText("Start")

    def display_frame_rate(self, frame_rate):
        self._frame_rates.append(frame_rate)
        if len(self._frame_rates) > 10:
            self.framerate_label.setText(
                f"Frame Rate: {round(mean(self._frame_rates), 1)} fps"
            )
            self._frame_rates = []

    def display_session_time(self, time):
        self.sessiontime_label.setText(
            "Session Time: %d:%02d:%02d" % (time // 3600, time // 60, time % 60)
        )

    def update_start_pushButton(self):
        self._movements = self._main_thread.get_tracking_movements()

        if self._main_thread.get_recording_status():
            """
            print tracking movements status to terminal
            (only used for testing)
            
            """
            for name, movement in self._movements.items():
                print(f"{name}: {movement.get_tracking_status()}")
            print("")

    def open_file(self):
        self._file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "./")
        self._main_thread.get_file(self._file_name[0])

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
