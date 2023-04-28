import cv2
import mediapipe as mp
from util import *

""" motion capture parameters """
MIN_DETECTION_CONFIDENCE = 0.9
MIN_TRACKING_CONFIDENCE = 0.9

""" tracking id's """
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


class Motion:
    """
    motion capture module

    """

    def __init__(
        self,
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        smooth_segmentation=True,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
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

    def track_motion(self, img, landmarks, crop, cropped):
        """
        used for tracking motion within a bounding box

        """
        self._landmark_x_min = -1
        self._landmark_x_max = -1

        adjust = [0, 0]
        landmark_x = []
        landmark_y = []

        """ 
        crop frame based on the position of the detected person 
        in the previous frame
        
        """
        height, width, _ = img.shape
        if cropped:
            img_crop = img[
                crop["start"][Y] : crop["end"][Y],
                crop["start"][X] : crop["end"][X],
            ]

            """ calculate positional adjustment needed for the cropped frame """
            adjust[X] = crop["start"][X] / width
            adjust[Y] = crop["start"][Y] / height
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
                """apply positional adjustment for the cropped frame"""
                if cropped:
                    landmark.x = landmark.x + adjust[X]
                    landmark.y = landmark.y + adjust[Y]

                """ append raw co-ordinate values (ranges from 0 to 1) """
                landmarks.append((id, landmark.x, landmark.y))

                """ 
                calculate co-ordinate values in pixels to be used later for 
                drawing the bounding box and to crop the next frame
                
                """
                cX = int(landmark.x * width)
                cY = int(landmark.y * height)
                landmark_x.append(cX)
                landmark_y.append(cY)

                """ highlight important points """
                wrists = id == LEFT_WRIST or id == RIGHT_WRIST
                elbows = id == LEFT_ELBOW or id == RIGHT_ELBOW
                shoulders = id == LEFT_SHOULDER or id == RIGHT_SHOULDER
                hips = id == LEFT_HIP or id == RIGHT_HIP
                knees = id == LEFT_KNEE or id == RIGHT_KNEE
                ankles = id == LEFT_ANKLE or id == RIGHT_ANKLE
                if any([wrists, elbows, shoulders, hips, knees, ankles]):
                    cv2.circle(img, (cX, cY), 10, MAGENTA, cv2.FILLED)

            """ draw connections between detected points """
            self._pose_param_dict["mp draw"].draw_landmarks(
                img,
                results.pose_landmarks,
                self._pose_param_dict["mp pose"].POSE_CONNECTIONS,
            )

            """ draw the bounding box """
            if len(landmark_x) > 0 and len(landmark_y) > 0:
                self._landmark_x_min = min(landmark_x) - int(0.06 * width)
                self._landmark_x_max = max(landmark_x) + int(0.06 * width)
                self._landmark_y_min = min(landmark_y) - int(0.10 * height)
                self._landmark_y_max = max(landmark_y) + int(0.08 * height)
                cv2.rectangle(
                    img,
                    (self._landmark_x_min, self._landmark_y_min),
                    (self._landmark_x_max, self._landmark_y_max),
                    MAGENTA,
                    3,
                )
                cropped = True
            else:
                cropped = False

        """ returns image frame and cropped status """
        return img, cropped
