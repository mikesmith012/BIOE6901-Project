import csv, time, os, util


class File:
    """
    file module: handles reading and writing files

    """

    """ default file path """
    file_path = "../files"
    supported_files = {util.CSV: ".csv", util.MP4: ".mp4"}

    def __init__(self, save=False):
        """
        save_file: a boolean to specify whether or not to generate a file

        """
        self._save_file = save

        self._data = []
        self._prev_time = 0

    def get_file_type(self, filename):
        """
        checks that the file is supported by the program
        returns the file type

        """
        for file_type, file_ext in self.supported_files.items():
            if file_ext in filename:
                return file_type

        return util.FILE_NOT_SUPPORTED
    
    def read(self):
        """
        not implemented yet

        """
        pass

    def write(self):
        """
        takes the parsed data and writes it to a csv file

        """
        if not self._save_file:
            return

        try:
            """create a directory to store the saved files"""
            if not os.path.exists(self.file_path):
                os.mkdir(self.file_path)

            """ make sure there are no existing files with duplicate names """
            dir = os.scandir(self.file_path)
            files = [a.name for a in dir]
            filename = self.create_filename()
            print(filename) if filename not in files else print("file already exists")

            """ create a csv file and write to it"""
            with open(filename, "w", newline="") as new_file:
                writer = csv.DictWriter(new_file, fieldnames=self._keys)
                writer.writeheader()

                for d in self._data:
                    writer.writerow(d)

        except:
            print("unable to generate csv file")

    def create_filename(self):
        """
        creates a unique filename using the current system time and date

        """
        localtime = time.localtime()
        return "%s/%04d-%02d-%02d-%02d-%02d-%02d.csv" % (
            self.file_path,
            localtime[0],
            localtime[1],
            localtime[2],
            localtime[3],
            localtime[4],
            localtime[5],
        )

    def parse_movements(self, movements, landmarks, curr_time):
        """
        parses the movement data periodically and stores it to be written later

        """
        if not self._save_file:
            return

        """ init field names for csv file """
        if self._prev_time == 0:
            self._prev_time = time.time()
            self._keys = [
                key for key in movements.keys() if movements[key].get_tracking_status()
            ]
            self._keys.insert(0, "time")
            self._keys.insert(1, "")
            self._keys.append("")

            for i in range(33):
                self._keys.append(i)

        """ update data every ~100ms """
        if time.time() > self._prev_time + 0.1:
            data = {
                "time": f"%d:%02d:%02d.%02d"
                % (
                    curr_time // 3600,
                    curr_time // 60,
                    curr_time % 60,
                    (curr_time % 1) * 100,
                )
            }
            for key, value in movements.items():
                if movements[key].get_tracking_status():
                    data[key] = value.get_count()

            if len(landmarks) > 0:
                for i, lm in enumerate(landmarks):
                    data[i] = (round(lm[1], 5), round(lm[2], 5))

            self._data.append(data)
            self._prev_time = time.time()
