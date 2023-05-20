# BIOE6901-Project

## Project
- [NRM-HT_2] Quantifying physical therapy with an easy-to-use, intuitive tool

## Description & Features
- A motion tracking application for counting reps during a physiotherapy session.
- Uses computer webcan by default, able to use an external USB webcam.
- Tracks motion and counts in real-time.
- Saves recorded session information to a csv file under patient name or ID number.
- Able to apply motion tracking and counting reps on mp4 videos.

## Requirements
- Works on Windows 10 or later
- Works with Python version 3.10

## Setup

<!--
### Mac / Linux
1.  Create python virtual environment: `python3 -m venv venv`
2.  Activate virtual environment: `source venv/bin/activate`
3.  Install dependencies: `python3 -m pip install -r req.txt`
4.  Run the program: `python3 src/main.py`
5.  To deactivate virtual environment: `deactivate`
-->

### Windows
1.  Create python virtual environment: `py -m venv venv`
2.  Activate virtual environment: `.\\venv\Scripts\activate`
3.  Install dependencies: `py -m pip install -r req.txt`
4.  Run the program: `py src/main.py`
5.  To deactivate virtual environment: `deactivate`

## Graphical User Interface
- Generate GUI File: `pyuic5 -x ui/gui.ui -o gui.py`