"""
config.py

Contains angular and positional threshold values used to determine movement repititions.

Contains thresholds for the following movements:
- Right arm extensions
- Left arm extensions
- Sit to stand

"""

from motion import Motion


__author__ = "Mike Smith"
__email__ = "dongming.shi@uqconnect.edu.au"
__date__ = "18/05/2023"
__status__ = "Prototype"
__credits__ = ["Agnethe Kaasen", "Live Myklebust", "Amber Spurway"]


"""
right arm extension thresholds

"""
RIGHT_ARM_EXT_ANGULAR_THRESH = [
    (Motion.right_wrist, Motion.right_elbow, Motion.left_shoulder, 130),
    (Motion.right_elbow, Motion.right_shoulder, Motion.right_hip, 30),
]

RIGHT_ARM_EXT_POSITIONAL_THRESH = [
    (Motion.right_elbow, Motion.right_shoulder, ">", 1),
]


"""
left arm extension thresholds

"""
LEFT_ARM_EXT_ANGULAR_THRESH = [
    (Motion.left_wrist, Motion.left_elbow, Motion.left_shoulder, 130),
    (Motion.left_elbow, Motion.left_shoulder, Motion.left_hip, 30),
]

LEFT_ARM_EXT_POSITIONAL_THRESH = [
    (Motion.left_elbow, Motion.left_shoulder, ">", 1),
]


"""
sit to stand thresholds

"""
SIT_TO_STAND_ANGULAR_THRESH = [
    (Motion.right_ankle, Motion.right_knee, Motion.right_hip, 150),
    (Motion.left_ankle, Motion.left_knee, Motion.left_hip, 150),
    (Motion.right_knee, Motion.right_hip, Motion.right_shoulder, 150),
    (Motion.left_knee, Motion.left_hip, Motion.left_shoulder, 150),
]

SIT_TO_STAND_POSITIONAL_THRESH = [
    (Motion.left_knee, Motion.left_hip, ">", 0.2),
    (Motion.right_knee, Motion.right_hip, ">", 0.2),
]