# File Module

Author: Mike Smith

Date of Implementation: 01/05/2023

## Description:

Handles reading and writing files. Contains methods for parsing movement data and writing to csv files.

Supported files:
- `.csv`
- `.mp4`

## Module methods:

`def __init__(self, save=True)`
- `save`: a boolean to specify whether or not to generate a file

`def set_save_status(self, save)`
- Set whether or not to generate a file
- `save`: a boolean to specify whether or not to generate a file

`def get_file_type(self, filename)`
- Checks that the file is supported by the program
- Returns the file type
- `filename`: the name of the file to be opened

`def read(self):`
- Not implemented yet

`def write(self)`
- Takes the parsed data and writes it to a csv file

`def create_filename(self)`
- Creates a unique filename using the current system time and date
- Returns a unique filename

`def parse_movements(self, movements, landmarks, curr_time)`
- Parses the movement data periodically and stores it to be written later
- `movements`: dictionary of movements containing tracking status
- `landmarks`: list containing all motion tracking landmark co-ordinates
- `curr_time`: time elapsed since start of the session in seconds