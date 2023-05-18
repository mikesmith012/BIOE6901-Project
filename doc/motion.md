# Motion Tracking Module
- Author: Mike Smith
- Email: dongming.shi@uqconnect.edu.au
- Date of Implementation: 12/04/2023
- Status: Prototype
- Credits: Agnethe Kaasen, Live Myklebust, Amber Spurway

## Description:

Motion tracking module. Handles the passing of information between the "MediaPipe Pose Estimation" library and the main application.

Motion tracking confidence levels:
```
min_detection_confidence = 0.9
min_tracking_confidence = 0.5
```

Motion tracking landmark ID's:
```
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
```

## Module methods:

`def __init__(self,
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        smooth_segmentation=True,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence)`
- Initialises "MediaPipe Pose Estimation" for motion tracking.

`def track_motion(self, img, landmarks)`
- Used for tracking motion within a bounding box
- `img`: Current video frame
- `landmarks`: List of co-ordinate values of all detected landmarks.
- Crops the frame based on the position of the detected person in the previous frame
- If human motion is detected, overlay the stick figure on the frame
- Calculates co-ordinate values in pixels to be used later for drawing the bounding box and to crop the next frame
- Highlight important points
- Draws connections between detected points
- Returns the current video frame with the detected elements back-projected onto the frame and a copy of the landmark co-ordinated in pixel values.