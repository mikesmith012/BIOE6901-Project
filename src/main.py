import cv2, sys, time
from PyQt5 import QtCore, QtWidgets, QtGui
from gui import Ui_MainWindow

from motion import *
from util import *

""" 
works with python version 3.10

install dependencies: numpy, opencv_python, mediapipe, PyQt5, pyqt5-tools

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

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_recording = False
        self.reset_all_count()

        """ set default movements to track """
        self._track_movements = {
            "right arm ext": True, 
            "left arm ext": True,
        }

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

            """ track motion (only when recording) """
            if self._is_recording:
                self._pose_landmarks = []
                img, cropped = self._motion.track_motion(
                    img, self._pose_landmarks, crop, cropped
                )
                # print(self._pose_landmarks)

                """ right arm extensions (if enabled) """
                if self._track_movements["right arm ext"]:
                    self.update_right_arm_ext_count()

                """ left arm extensions (if enabled) """
                if self._track_movements["left arm ext"]:
                    self.update_left_arm_ext_count()

            """ show detected elements on screen """
            img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
            QtImg = QtGui.QImage(
                img.data, width, height, QtGui.QImage.Format_RGB888
            ).scaled(int(1280 - 128 / 8), int(720 - 72 / 8), QtCore.Qt.KeepAspectRatio)
            self.image.emit(QtImg)

        cv2.destroyAllWindows()
        cap.release()

    def stop(self):
        self._active = False
        self.wait()

    def get_recording_status(self):
        return self._is_recording

    def start_stop_recording(self):
        self._is_recording = not self._is_recording
        if self._is_recording:
            self.reset_all_count()
    
    def reset_all_count(self):

        """ reset count values """
        self._right_arm_ext_count = 0
        self._left_arm_ext_count = 0

        """ reset angles """
        self._right_arm_ext_angles = {"prev": [-1, -1], "curr": [-1, -1]}
        self._left_arm_ext_angles = {"prev": [-1, -1], "curr": [-1, -1]}

    def get_tracking_movements(self):
        return self._track_movements
    
    def update_tracking_movements(self, movement, status):
        try:
            self._track_movements[movement] = status
        except:
            print("index error")

    def update_right_arm_ext_count(self):
        self._right_arm_ext_count = self._motion.arm_extensions(
            self._pose_landmarks,
            self._right_arm_ext_count, 
            self._right_arm_ext_angles,
            "r",
        )
        self.right_arm_ext.emit(str(self._right_arm_ext_count))

    def update_left_arm_ext_count(self):
        self._left_arm_ext_count = self._motion.arm_extensions(
            self._pose_landmarks, 
            self._left_arm_ext_count, 
            self._left_arm_ext_angles,
            "l",
        )
        self.left_arm_ext.emit(str(self._left_arm_ext_count))


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

        """
        connect front-end gui signals
        
        """
        self.update_start_pushButton_text()
        self.start_pushButton.clicked.connect(self._main_thread.start_stop_recording)
        self.start_pushButton.clicked.connect(self.update_start_pushButton_text)

        self._movements = self._main_thread.get_tracking_movements()

    def update_frame(self, img):
        self.img_label.setPixmap(QtGui.QPixmap(img))

    def display_frame_rate(self, frame_rate):
        self.framerate_label.setText(f"Frame Rate: {frame_rate} fps")

    def update_start_pushButton_text(self):
        is_recording = self._main_thread.get_recording_status()
        if is_recording:
            self.start_pushButton.setText("Stop")
        else:
            self.start_pushButton.setText("Start")

    def display_right_arm_ext_count(self, count):
        self.right_arm_ext_count_label.setText(f"Right Arm Extensions: {count}")

    def display_left_arm_ext_count(self, count):
        self.left_arm_ext_count_label.setText(f"Left Arm Extensions: {count}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
