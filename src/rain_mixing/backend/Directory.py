import functools
import os
import string
from typing import Union

from constants.file_constants import EXTENSION_LIST
from rain_mixing.backend.MusicFile import MusicFile

"""
Defines a directory that can hold other directories or music files

:attributes
    - directory: The directory in user storage that this instance will
    represent
    - max_id: The maximum id held by any music file in this folder + 1
"""


class Directory:
    def __init__(self, directory: string = "", max_id: int = 0) -> None:

        self.files: list[MusicFile] = []
        self.num_files = 0
        self.max_id = max_id
        self.sub_directories: list[Directory] = []

        if directory:
            self.path = directory
            self.scan_dir()
        else:
            self.path = "root"

    """
    Scans self.path for files and directories to add to this directory
    """

    def scan_dir(self) -> None:

        for path in os.listdir(self.path):
            path = os.path.join(self.path, path)

            if os.path.isdir(path):
                # Recursively constructs the subdirectories
                new_dir = Directory(path, self.max_id)

                # Ignore directories without any music files within them
                if new_dir.num_files > 0:
                    self.max_id = new_dir.max_id
                    self.num_files += new_dir.num_files + 1
                    self.sub_directories.append(new_dir)

            elif os.path.isfile(path) and path[-3:] in EXTENSION_LIST:
                self.num_files += 1
                new_file = MusicFile(path, self.max_id)
                self.max_id += 1
                self.files.append(new_file)

    """
    Searches itself and all subdirectories / files for any whose name
    matches the search term (with fuzzy matches), and returns a new directory
    representing those that satisfy the search term

    Results cached for efficiency since this involves recursion

    :param
        -   term: The search term to match files / directories to
    :return
        -   new_dir: A directory of all matches within this directory. If no
        matches are found, return None
    """

    @functools.lru_cache(maxsize=100, typed=False)
    def search(self, term: string) -> Union["Directory", None]:
        new_dir = None

        if term in self.get_name().lower():
            # If this directory satisfies the search, return all of it's
            # contents
            new_dir = self
        else:
            file_matches = []
            total_files = 0

            # finding all file matches
            for file in self.files:
                if term in file.title.lower():
                    file_matches.append(file)
                    total_files += 1

            # finding all subdirectory matches
            sub_dir_matches = []
            for sub_dir in self.sub_directories:
                sub_result = sub_dir.search(term)
                if sub_result:
                    sub_dir_matches.append(sub_result)
                    total_files += sub_result.num_files + 1

            # If no matches found at all, ensures None is returned
            if file_matches or sub_dir_matches:
                # Copying relevant data to the new directory
                new_dir = Directory()
                new_dir.path = self.path
                new_dir.num_files = total_files
                new_dir.files = file_matches
                new_dir.sub_directories = sub_dir_matches

        return new_dir

    """
    Returns the treeview representation of this directory

    :return
        - self rep: A list of the following format:
            - Contains a dict with "name" and "children"
            - All subdirectories and files of this folder are contained in
            children
            - Subdirectories are represented under this format
    """

    def get_dict(self) -> list:
        self_name = os.path.basename(self.path)
        self_rep = []

        self_dict = {"name": self_name, "children": []}

        for file in self.files:
            self_dict["children"].append(file.title)

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

    """
    Adds an existing folder to this directory's sub-directories

    :param
        - directory: The already initialized directory to add
    """

    def add_folder(self, path: string) -> "Directory":
        new_dir = Directory(path, self.max_id)
        self.sub_directories.append(new_dir)
        self.num_files += new_dir.num_files + 1
        self.max_id = new_dir.max_id

        return new_dir
