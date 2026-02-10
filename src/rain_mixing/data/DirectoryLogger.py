import os
import string

from constants.file_constants import USER_DIR
from rain_mixing.backend.Directory import Directory
from rain_mixing.utils.utils import verify_dir

"""
Manages saving and loading directory data persistently
"""


class DirectoryLogger:

    def __init__(self, logging_dir: string = USER_DIR):
        verify_dir(logging_dir)
        self.data_file = os.path.join(logging_dir, "data.txt")

    """
    Writes all directories in the root to the data file

    :param
        -   root: The directory containing all saved folders by the user
    """

    def log_dirs(self, root: Directory) -> None:
        with open(self.data_file, "w") as data_file:
            for sub_dir in root.sub_directories:
                data_file.write(sub_dir.path)
                data_file.write("\n")

    """
    Loads a directory from storage and returns it

    :return
        -   new_root: The directory in the same state as how the user last
        saved it
    """

    def load_dirs(self) -> Directory:
        new_root = Directory()

        if os.path.isfile(self.data_file):
            with open(self.data_file, "r") as data_file:
                for line in data_file:
                    try:
                        line = line[:-1]
                        new_root.add_folder(line)
                    except FileNotFoundError:
                        pass

        return new_root
