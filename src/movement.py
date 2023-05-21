"""
movement.py

Contains a generic movement class. 
Each movement is defined by a set of angle (each defined by three points) 
and a set of positional thresholds (each define by two points).

see "doc/movement.md" for more details

"""

import math, cv2, util


__author__ = "Mike Smith"
__email__ = "dongming.shi@uqconnect.edu.au"
__date__ = "23/04/2023"
__status__ = "Prototype"
__credits__ = ["Agnethe Kaasen", "Live Myklebust", "Amber Spurway"]


class Movement:
    """
    generic movement class

    """

    def __init__(self, points, positions, is_tracking, ignore_vis=False, debug=False):
        """
        points: a list containing tuples of three points and the threshold angle
        positions: a list containing pairs of point with thresholds for relative positioning
        is_tracking: a boolean to specify whether tracking is enabled

        ignore_vis: a boolean to ignore visibility thresholds
            set to "True" if tracking full-body / compound movements
        debug: a boolean to allow program to overlay angle values on frame

        """

        self._points = points
        self._positions = positions
        self._is_tracking = is_tracking
        self._ignore_vis = ignore_vis
        self._debug = debug

        self._reset = False
        self._angles = []
        self._less_than_thresh = []
        self._greater_than_thresh = []

        for i, p in enumerate(self._points):
            self._angles.append({"prev": -1, "curr": -1})
            self._less_than_thresh.append(False)
            self._greater_than_thresh.append(False)

            """ check is each element in "points" is a tuple of three values """
            if len(p) != 4:
                self.invalid_num_of_elements_err(i)

        self._position_conditions = []
        for i, p in enumerate(self._positions):
            self._position_conditions.append(False)

        self.reset_count()

    def invalid_num_of_elements_err(self, i):
        """
        checks for invalid lengths in the input arrays.
        raises a `ValueError` is invalid number of elements is detected.
        
        """
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

    def count_movement(self, landmarks, pixels, img, source):
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

                """ if debug mode, annotate video frames with angle values """
                if self._debug:
                    img = self.annotate(img, source, pixels, angle, i)

            """ check the relative positions of specified points """
            for i, pos in enumerate(self._positions):
                if pos[2] == "<":
                    if (
                        self.get_position(pos[1], landmarks, util.Y)
                        < self.get_position(pos[0], landmarks, util.Y) + pos[3]
                    ):
                        self._position_conditions[i] = True
                    else:
                        self._position_conditions[i] = False
                elif pos[2] == ">":
                    if (
                        self.get_position(pos[1], landmarks, util.Y)
                        > self.get_position(pos[0], landmarks, util.Y) - pos[3]
                    ):
                        self._position_conditions[i] = True
                    else:
                        self._position_conditions[i] = False

        else:
            for i, angle in enumerate(self._angles):
                angle["curr"] = -1

        """ specify conditions using the threshold values """
        for i, angle in enumerate(self._angles):
            if angle["curr"] > 0 and angle["prev"] > 0:
                if angle["curr"] < self._points[i][3]:
                    self._less_than_thresh[i] = True
                    self._greater_than_thresh[i] = False
                else:
                    self._less_than_thresh[i] = False
                    self._greater_than_thresh[i] = True

        if all(self._less_than_thresh):
            self._reset = True

        """ if all conditions are met, increment count """
        if (
            all(self._greater_than_thresh)
            and all(self._position_conditions)
            and self._reset
        ):
            self._count += 1
            self._reset = False

        return img, self._count

    def get_count(self):
        """
        returns the current movement count value

        """
        return self._count

    def find_angle(self, p1, p2, p3):
        """
        generic function for calutating the angle between two lines
        defined by three points

        note: p2 must be the common point between the two lines

        """
        _, x1, y1, v1 = p1
        _, x2, y2, v2 = p2
        _, x3, y3, v3 = p3

        """
        check that the visibility of the points is above the visibility threshold
        otherwise, ignore points as this can lead to program guessing position of points

        """
        if self._ignore_vis:
            c0 = [True]
        else:
            c0 = [v1 > util.VIS, v2 > util.VIS, v3 > util.VIS]

        """
        check that points are not too close to the edge of the frame
        otherwise, ignore points as this can lead to inaccurate angle values

        """
        c1 = [x1 > util.MIN, x1 < util.MAX, y1 > util.MIN, y1 < util.MAX]
        c2 = [x2 > util.MIN, x2 < util.MAX, y2 > util.MIN, y2 < util.MAX]
        c3 = [x3 > util.MIN, x3 < util.MAX, y3 > util.MIN, y3 < util.MAX]

        if all(c0) and all(c1) and all(c2) and all(c3):
            angle_rad = math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
            angle_deg = abs(math.degrees(angle_rad))
        else:
            angle_deg = -1

        """ make sure all angle values are between 0 and 180 degrees """
        if angle_deg < 180:
            return angle_deg
        else:
            return 360 - angle_deg

    def get_position(self, pos, landmarks, x_or_y):
        """
        returns the current x or y position of specifies landmark
        pos: the index position of the specified landmark (same ad the landmark id)
        landmarks: a list of all tracking landmarks
        x_or_y: whether to get the x or y co-ordinate of the given point

        """
        return landmarks[pos][x_or_y]

    def annotate(self, img, source, pixels, angle, index):
        """
        overlays angle values onto video frames

        """
        h, w, _ = img.shape
        angle = round(angle["curr"])
        colour = util.RED if angle < 0 else util.GREEN
        font = cv2.FONT_HERSHEY_SIMPLEX

        if source == util.WEBCAM:
            img = cv2.flip(img, 1)

            x = w - pixels[self._points[index][1]][util.X]
            y = pixels[self._points[index][1]][util.Y]

            cv2.putText(img, str(angle), (x, y), font, 0.8, colour, 2)
            img = cv2.flip(img, 1)

        else:
            x, y = pixels[self._points[index][1]]
            cv2.putText(img, str(angle), (x, y), font, 0.8, colour, 2)

        return img
