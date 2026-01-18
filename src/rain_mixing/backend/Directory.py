import functools
import os
import string
from typing import Union

from constants.file_constants import EXTENSION_LIST
from rain_mixing.backend.MusicFile import MusicFile

"""
Defines a directory that can hold other directories or music files
"""


class Directory:
    """
    Initializes a directory using a provided file path, and saves the data
    of all associated music files within the directory or any subdirectory

    :param
        - directory: The directory in user storage that this instance will
        represent
    """

    def __init__(self, directory: string = "") -> None:

        self.files: list[MusicFile] = []
        self.num_files = 0
        self.sub_directories: list[Directory] = []

        if directory:
            self.path = directory
            self.scan_dir()
        else:
            self.path = ""

    """
    Empties self.files and self.sub_directories and scans self.path for files 
    and directories
    """

    def scan_dir(self) -> None:
        self.sub_directories = []
        self.files = []

        for path in os.listdir(self.path):
            path = os.path.join(self.path, path)

            if os.path.isdir(path):
                # Recursively constructs the subdirectory
                new_dir = Directory(path)

                # Ignore directories without any music files within them
                if new_dir.num_files > 0:
                    self.num_files += new_dir.num_files + 1
                    self.sub_directories.append(new_dir)
            elif os.path.isfile(path) and path[-3:] in EXTENSION_LIST:
                self.num_files += 1
                new_file = MusicFile(path)
                self.files.append(new_file)

    """
    Returns a list of every music file stored within this directory and 
    and subdirectories
    
    :return
        - all_files: A list of every MusicFile instance stored somewhere within
        this directory
    """

    def get_files(self) -> list[MusicFile]:
        all_files = []
        all_files += self.files

        for sub_directory in self.sub_directories:
            all_files += sub_directory.get_files()
        return all_files

    @functools.lru_cache(maxsize=100, typed=False)
    def search(self, term: string) -> Union["Directory", None]:
        new_dir = None

        if term in self.get_name().lower():
            new_dir = self
        else:
            file_matches = []
            total_files = 0
            for file in self.files:
                if term in file.name.lower():
                    file_matches.append(file)
                    total_files += 1

            sub_dir_matches = []
            for sub_dir in self.sub_directories:
                sub_result = sub_dir.search(term)
                if sub_result:
                    sub_dir_matches.append(sub_result)
                    total_files += sub_result.num_files

            if file_matches or sub_dir_matches:
                new_dir = Directory()
                new_dir.path = self.path
                new_dir.num_files = total_files
                new_dir.files = file_matches
                new_dir.sub_directories = sub_dir_matches

        return new_dir

    """
    Returns the treeview representation of this directory
    
    :return
        - self rep: A list of the following format: TODO
    """

    def get_dict(self) -> list:
        self_name = os.path.basename(self.path)
        self_rep = []

        self_dict = {"name": self_name, "children": []}

        for file in self.files:
            self_dict["children"].append(file.name)

        for sub_dir in self.sub_directories:
            sub_dict = sub_dir.get_dict()
            self_dict["children"].append(sub_dict[0])

        self_rep.append(self_dict)
        return self_rep

    """
    Returns the name of this directory
    
    :return
        - The name of the folder used to initialize this directory
    """

    def get_name(self) -> string:
        return os.path.basename(self.path)
