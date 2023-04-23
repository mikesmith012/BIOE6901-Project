import cv2, sys, time
from PyQt5 import QtCore, QtWidgets, QtGui
from gui import Ui_MainWindow

from movement import *
from motion import *
from util import *

""" 
works with python version 3.10

Setup
1.  Create python virtual environment: `python3 -m venv venv`
2.  Activate virtual environment: `source venv/bin/activate`
3.  Install dependencies: `python3 -m pip install -r req.txt`
4.  Run the program: `python3 src/main.py`
5.  To deactivate virtual environment: `deactivate`

generate gui file: pyuic5 -x ui/gui.ui -o gui.py

"""


class MainThread(QtCore.QThread):
    """
    back-end worker thread: handles camera access, motion tracking
    and counting reps

    """

    image = QtCore.pyqtSignal(QtGui.QImage)
    frame_rate = QtCore.pyqtSignal(str)

    """ back-end signals to handle counting reps """
    right_arm_ext = QtCore.pyqtSignal(str)
    left_arm_ext = QtCore.pyqtSignal(str)
    sit_to_stand = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_recording = False
        self._tracking_movements = {}

    def get_frame_rate(self, frame_times):
        """
        calculates frame rate: used for testing

        """
        frame_times["curr time"] = time.time()
        frame_rate = 1 / (frame_times["curr time"] - frame_times["prev time"])
        frame_times["prev time"] = frame_times["curr time"]
        return str(int(frame_rate))

    def run(self):
        """
        main worker thread

        """
        self._active = True

        """ open webcam """
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        """ get camera resolution and show in terminal (for debugging) """
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Resolution: {width} x {height}")

        """ frame rate (for debugging) """
        frame_times = {"curr time": 0, "prev time": 0}

        """ init motion capture """
        self._motion = Motion()
        crop = {"start": INIT, "end": INIT}
        cropped = False

        """ add and init movements """
        self.add_movements()
        self.reset_all_count()

        while cap.isOpened() and self._active:
            ret, img = cap.read()
            if ret == False:
                print("can't connect to camera :(")
                self.stop()

            """ get frame dimensions """
            height, width, _ = img.shape
            crop = {"start": INIT, "end": (width, height)}

            """ display frame rate """
            frame_rate = self.get_frame_rate(frame_times)
            self.frame_rate.emit(frame_rate)

            """ track motion and count movements (only when recording) """
            if self._is_recording:
                self._pose_landmarks = []
                img, cropped = self._motion.track_motion(
                    img, self._pose_landmarks, crop, cropped
                )
                # print(self._pose_landmarks)

                self.count_movements()

            """ show detected elements on screen """
            img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
            QtImg = QtGui.QImage(
                img.data, width, height, QtGui.QImage.Format_RGB888
            ).scaled(int(1280 - 128 / 8), int(720 - 72 / 8), QtCore.Qt.KeepAspectRatio)
            self.image.emit(QtImg)

        cv2.destroyAllWindows()
        cap.release()

    def stop(self):
        """
        stops the worker thread
        """
        self._active = False
        self.wait()

    def get_recording_status(self):
        """
        gets current recording status
        returns True if recording, else returns False
        used in the main window thread to update gui
        """
        return self._is_recording

    def start_stop_recording(self):
        """
        starts and stops recording
        called from the main window thread whenever the start/stop button is pressed
        resets all movement count
        """
        self._is_recording = not self._is_recording
        if self._is_recording:
            self.reset_all_count()

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
                (RIGHT_WRIST, RIGHT_ELBOW, RIGHT_SHOULDER),
                (RIGHT_ELBOW, RIGHT_SHOULDER, LEFT_SHOULDER),
            ],
            [160, 135],
            True,
            init_movement=True,
            init_threshold=100,
        )
        self._tracking_movements.update({"right arm ext": self._right_arm_ext})

        """ add left arm extensions """
        self._left_arm_ext = Movement(
            [
                (LEFT_WRIST, LEFT_ELBOW, LEFT_SHOULDER),
                (LEFT_ELBOW, LEFT_SHOULDER, RIGHT_SHOULDER),
            ],
            [160, 135],
            True,
            init_movement=True,
            init_threshold=100,
        )
        self._tracking_movements.update({"left arm ext": self._left_arm_ext})

        """ add sit to stand movement """
        self._sit_to_stand = Movement(
            [
                (RIGHT_ANKLE, RIGHT_KNEE, RIGHT_HIP),
                (LEFT_ANKLE, LEFT_KNEE, LEFT_HIP),
                (RIGHT_KNEE, RIGHT_HIP, RIGHT_SHOULDER),
                (LEFT_KNEE, LEFT_HIP, LEFT_SHOULDER),
            ],
            [160, 150, 160, 160],
            True,
            init_movement=True,
            init_threshold=120,
        )
        self._tracking_movements.update({"sit to stand": self._sit_to_stand})

    def count_movements(self):
        """right arm extensions (if enabled)"""
        if self._right_arm_ext.get_tracking_status():
            self._right_arm_ext_count = self._right_arm_ext.count_movement(
                self._pose_landmarks
            )
            self.right_arm_ext.emit(str(self._right_arm_ext_count))

        """ left arm extensions (if enabled) """
        if self._left_arm_ext.get_tracking_status():
            self._left_arm_ext_count = self._left_arm_ext.count_movement(
                self._pose_landmarks
            )
            self.left_arm_ext.emit(str(self._left_arm_ext_count))

        """ sit to stand (if enabled) """
        if self._sit_to_stand.get_tracking_status():
            self._sit_to_stand_count = self._sit_to_stand.count_movement(
                self._pose_landmarks
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

        self._main_thread = MainThread()
        self._main_thread.start()

        """ connect back-end signals """
        self._main_thread.image.connect(self.update_frame)
        self._main_thread.frame_rate.connect(self.display_frame_rate)

        """ connect motion traking signals """
        self._main_thread.right_arm_ext.connect(self.display_right_arm_ext_count)
        self._main_thread.left_arm_ext.connect(self.display_left_arm_ext_count)
        self._main_thread.sit_to_stand.connect(self.display_sit_to_stand_count)

        """ connect front-end gui signals """
        self.update_start_pushButton_text()
        self.start_pushButton.clicked.connect(self._main_thread.start_stop_recording)
        self.start_pushButton.clicked.connect(self.update_start_pushButton_text)

    def update_frame(self, img):
        self.img_label.setPixmap(QtGui.QPixmap(img))

    def display_frame_rate(self, frame_rate):
        self.framerate_label.setText(f"Frame Rate: {frame_rate} fps")

    def update_start_pushButton_text(self):
        is_recording = self._main_thread.get_recording_status()
        if is_recording:
            self.start_pushButton.setText("Stop")

            """ 
            get tracking movements status and print to terminal 
            (only used for testing)
            """
            self._movements = self._main_thread.get_tracking_movements()
            for name, movement in self._movements.items():
                print(f"{name}: {movement.get_tracking_status()}")
            # print("\n")

        else:
            self.start_pushButton.setText("Start")

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
