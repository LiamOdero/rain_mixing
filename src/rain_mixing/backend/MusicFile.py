import os
import string

from pydub import AudioSegment

"""
Defines a music file stored by the user and some associated metadata
"""


class MusicFile:
    """
    Initializes a directory using a provided file path, and saves the data
    of all associated music files within the directory or any subdirectory

    :param
        -   directory: The full path where the actual music file this class
        represents is held
    """

    def __init__(self, directory: string) -> None:
        self.audio = None
        self.path = directory
        self.name = os.path.basename(directory)[:-4]

    def load_audio(self) -> None:
        try:
            self.audio = AudioSegment.from_file(self.path, self.path[-3:])
        except FileNotFoundError:
            pass
