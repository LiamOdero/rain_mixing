import os
import string

"""
Defines a music file stored by the user and some associated metadata
"""


class MusicFile:
    """
    Initializes a directory using a provided file path, and saves the data
    of all associated music files within the directory or any subdirectory
    """

    def __init__(self, directory: string):
        self.path = directory
        self.name = os.path.basename(directory)[:-4]
        # TODO: create audiosegment
