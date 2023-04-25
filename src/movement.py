import math
from util import *


class Movement:
    """
    generic movement class

    """

    def __init__(self, points, thresholds, is_tracking):
        """
        points: a list containing tuples of three points
        thresholds: a list of threshold angle values (in degrees)
        is_tracking: a boolean to specify whether tracking is enabled

        note: number of elements in "points" must match number of elements in "thresholds"
        """

        """ check is "points" and "thresholds" are the same length """
        if len(points) != len(thresholds):
            self.element_mismatch_err()

        self._points = points
        self._thresholds = thresholds
        self._is_tracking = is_tracking

        self._reset = False
        self._angles = []
        self._less_than_thresh = []
        self._greater_than_thresh = []
        for i, p in enumerate(self._points):
            self._angles.append({"prev": -1, "curr": -1})
            self._less_than_thresh.append(False)
            self._greater_than_thresh.append(False)

            """ check is each element in "points" is a tuple of three values """
            if len(p) != 3:
                self.invalid_num_of_elements_err(i)

        self.reset_count()

    def element_mismatch_err(self):
        raise ValueError("element mismatch")

    def invalid_num_of_elements_err(self, i):
        raise ValueError(f"invalid number of elements in index {i}")

    def reset_count(self):
        """
        init count to zero by default
        """
        self._count = 0

    def set_tracking_status(self, is_tracking):
        """
        set the tracking status
        can be used to turn on/off tracking for certain movements
        """
        self._is_tracking = is_tracking

    def get_tracking_status(self):
        """
        get the current tracking status
        returns True is tracking is active, else returns False
        """
        return self._is_tracking

    def count_movement(self, landmarks):
        """
        count the number of reps for the movement

        """
        for angle in self._angles:
            angle["prev"] = angle["curr"]
        
        if len(landmarks) != 0:
            for i, angle in enumerate(self._angles):
                angle["curr"] = self.find_angle(
                    landmarks[self._points[i][0]],
                    landmarks[self._points[i][1]],
                    landmarks[self._points[i][2]],
                )
        else:
            for i, angle in enumerate(self._angles):
                angle["curr"] = -1

        # print(self._angles[0]["curr"])

        """ specify conditions using the threshold values """
        for i, angle in enumerate(self._angles):
            if angle["curr"] > 0 and angle["prev"] > 0:
                if angle["curr"] < self._thresholds[i]:
                    self._less_than_thresh[i] = True
                    self._greater_than_thresh[i] = False
                else:
                    self._less_than_thresh[i] = False
                    self._greater_than_thresh[i] = True
        
        if all(self._less_than_thresh):
            self._reset = True

        """ if all conditions are met, increment count """
        if all(self._greater_than_thresh) and self._reset:
            self._count += 1
            self._reset = False

        return self._count

    def find_angle(self, p1, p2, p3):
        """
        generic function for calutating the angle between two lines
        defined by three points

        note: p2 must be the common point between the two lines

        """
        _, x1, y1 = p1
        _, x2, y2 = p2
        _, x3, y3 = p3

        """
        check that points are not too close to the edge of the frame
        otherwise, ignore points as this can lead to inaccurate angle values

        """
        c1 = [x1 > MIN, x1 < MAX, y1 > MIN, y1 < MAX]
        c2 = [x2 > MIN, x2 < MAX, y2 > MIN, y2 < MAX]
        c3 = [x3 > MIN, x3 < MAX, y3 > MIN, y3 < MAX]

        if all(c1) and all(c2) and all(c3):
            angle_rad = math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
            angle_deg = abs(math.degrees(angle_rad))
        else:
            angle_deg = -1

        """ make sure all angle values are between 0 and 180 degrees """
        if angle_deg < 180:
            return angle_deg
        else:
            return 360 - angle_deg