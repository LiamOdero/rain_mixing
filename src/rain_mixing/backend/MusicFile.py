import os
import string
import eyed3.id3
from pydub import AudioSegment

"""
Defines a music file stored by the user and some associated metadata

:attributes
    -   directory: The full path where the actual music file this class
    represents is held
    -   id: A unique identifier for this music file
"""


class MusicFile:

    def __init__(self, directory: string, id: int) -> None:
        self.audio = None
        self.id = id
        self.path = directory

        file_metadata = eyed3.load(self.path)
        if file_metadata:
            self.metadata = file_metadata.tag
        else:
            self.metadata = None

        self.name = os.path.basename(directory)[:-4]

    def load_audio(self) -> None:
        try:
            self.audio = AudioSegment.from_file(self.path, self.path[-3:])
        except FileNotFoundError:
            pass

    def get_name(self) -> string:
        return self.name
