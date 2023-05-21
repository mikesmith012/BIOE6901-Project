# Configuration File
- Author: Mike Smith
- Email: dongming.shi@uqconnect.edu.au
- Date of Implementation: 18/05/2023
- Status: Prototype
- Credits: Agnethe Kaasen, Live Myklebust, Amber Spurway

## Description

Contains angular and positional threshold values used to determine movement repititions.

Contains thresholds for the following movements:
- Right arm extensions
- Left arm extensions
- Sit to stand

## Definitions

Angular Thresholds:

- Refers to the limit used to determine whether a change in angle surpasses a predefined threshold.
- Each angle is defined by three points with the centre point being where the angle is evaluated.
- One or more angular threshold can be used to define a movement.
- If multiple angular thresholds are defined, all must be satisfied for the movement to count.

Positional Thresholds:

- Refers to the limit used to determine whether a change in relative positions surpasses a predefined threshold.
- Relative positions are defined by two points and the x or y distance between them. 
- Currently, only y-axis values are used to evaluate relative positions between points. So far, there has not been a need to use any x-axis values.
- One or more positional threshold can be used to define a movement.
- If multiple positional thresholds are defined, all must be satisfied for the movement to count.

## Example Usage

```
EXAMPLE_ANGULAR_THRESH = [
    (<point_1>, <point_2>, <point_3>, <angluar_threshold_1>),
    (<point_4>, <point_5>, <point_6>, <angluar_threshold_2>),
    ...
]

EXAMPLE_POSITIONAL_THRESH = [
    (<point_1>, <point_2>, ">" or "<", <positional_threshold_1>),
    (<point_3>, <point_4>, ">" or "<", <positional_threshold_2>),
    ...
]
```

## Chosen Thresholds

The chosen angular and positional thresholds are based on the physiological properties of the human anatomy. Chosen thresholds are tested extensively to provide the highest possible accuracy for the given movement while ignoring unintentional movements to avoid miscounts. A combination of multiple angular and positional thresholds can be used to define a specific movement. All threshold requirements must be satisfied for the movement to count.

### Arm Extensions
- wrist-elbow-shoulder angle: 130 degrees
- elbow-shoulder-hip angle: 30 degrees

### Sit to Stand
- ankle-knee-hip angle: 150 degrees
- knee-hip-shoulder angle: 150 degrees