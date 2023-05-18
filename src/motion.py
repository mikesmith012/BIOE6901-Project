"""
motion.py

Motion tracking module. 
Handles the passing of information between the "MediaPipe Pose Estimation" library 
and the main application.

"""

import cv2, util
import mediapipe as mp


__author__ = "Mike Smith"
__email__ = "dongming.shi@uqconnect.edu.au"
__date__ = "12/04/2023"
__status__ = "Prototype"
__credits__ = ["Agnethe Kaasen", "Live Myklebust", "Amber Spurway"]


class Motion:
    """
    motion capture module

    """

    """ motion capture parameters """
    min_detection_confidence = 0.9
    min_tracking_confidence = 0.5

    """ tracking id's """
    left_shoulder = 11
    right_shoulder = 12
    left_elbow = 13
    right_elbow = 14
    left_wrist = 15
    right_wrist = 16
    left_hip = 23
    right_hip = 24
    left_knee = 25
    right_knee = 26
    left_ankle = 27
    right_ankle = 28

    crop = {"start": util.INIT, "end": util.INIT}
    cropped = False

    def __init__(
        self,
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        smooth_segmentation=True,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    ):
        self._static_image_mode = static_image_mode
        self._model_complexity = model_complexity
        self._smooth_landmarks = smooth_landmarks
        self._enable_segmentation = enable_segmentation
        self._smooth_segmentation = smooth_segmentation
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence

        self._pose_param_dict = {
            "mp pose": mp.solutions.pose,
            "mp draw": mp.solutions.drawing_utils,
        }
        self._pose = self._pose_param_dict["mp pose"].Pose(
            static_image_mode=self._static_image_mode,
            model_complexity=self._model_complexity,
            smooth_landmarks=self._smooth_landmarks,
            enable_segmentation=self._enable_segmentation,
            smooth_segmentation=self._smooth_segmentation,
            min_detection_confidence=self._min_detection_confidence,
            min_tracking_confidence=self._min_tracking_confidence,
        )

    def track_motion(self, img, landmarks):
        """
        used for tracking motion within a bounding box

        """
        self._landmark_x_min = -1
        self._landmark_x_max = -1

        adjust = [0, 0]
        lm_pixels = []

        """ 
        crop frame based on the position of the detected person 
        in the previous frame
        
        """
        height, width, _ = img.shape
        if self.cropped:
            img_crop = img[
                self.crop["start"][util.Y] : self.crop["end"][util.Y],
                self.crop["start"][util.X] : self.crop["end"][util.X],
            ]

            """ calculate positional adjustment needed for the cropped frame """
            adjust[util.X] = self.crop["start"][util.X] / width
            adjust[util.Y] = self.crop["start"][util.Y] / height
        else:
            img_crop = img

        """ look for human motion in the bounding box / cropped frame """
        img_crop = cv2.cvtColor(img_crop, cv2.COLOR_BGR2RGB)
        results = self._pose.process(img_crop)
        img_crop = cv2.cvtColor(img_crop, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            """
            if human motion is detected, overlay the stick figure on the frame

            """
            for id, landmark in enumerate(results.pose_landmarks.landmark):
                """
                apply positional adjustment for the cropped frame

                """
                if self.cropped:
                    landmark.x = landmark.x + adjust[util.X]
                    landmark.y = landmark.y + adjust[util.Y]

                """ append raw co-ordinate values (ranges from 0 to 1) """
                landmarks.append((id, landmark.x, landmark.y, landmark.visibility))

                """ 
                calculate co-ordinate values in pixels to be used later for 
                drawing the bounding box and to crop the next frame
                
                """
                lm_pixels.append((int(landmark.x * width), int(landmark.y * height)))

                """ highlight important points """
                wrists = id == self.left_wrist or id == self.right_wrist
                elbows = id == self.left_elbow or id == self.right_elbow
                shoulders = id == self.left_shoulder or id == self.right_shoulder
                hips = id == self.left_hip or id == self.right_hip
                knees = id == self.left_knee or id == self.right_knee
                ankles = id == self.left_ankle or id == self.right_ankle

                if any([wrists, elbows, shoulders, hips, knees, ankles]):
                    x, y = lm_pixels[-1][util.X], lm_pixels[-1][util.Y]
                    cv2.circle(img, (x, y), 8, util.YELLOW, cv2.FILLED)

            """ draw connections between detected points """
            self._pose_param_dict["mp draw"].draw_landmarks(
                img,
                results.pose_landmarks,
                self._pose_param_dict["mp pose"].POSE_CONNECTIONS,
            )

            """ draw the bounding box """
            if len(lm_pixels) > 0:
                self._landmark_x_min = min([lm[util.X] for lm in lm_pixels]) - int(
                    0.03 * width
                )
                self._landmark_x_max = max([lm[util.X] for lm in lm_pixels]) + int(
                    0.03 * width
                )
                self._landmark_y_min = min([lm[util.Y] for lm in lm_pixels]) - int(
                    0.05 * height
                )
                self._landmark_y_max = max([lm[util.Y] for lm in lm_pixels]) + int(
                    0.04 * height
                )

                x_min, y_min = self._landmark_x_min, self._landmark_y_min
                x_max, y_max = self._landmark_x_max, self._landmark_y_max
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), util.BLUE, 3)

                self.cropped = True

            else:
                self.cropped = False

        """ returns image frame and landmark pixel co-ordinates """
        return img, lm_pixels.copy()
