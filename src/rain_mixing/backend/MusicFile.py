import os
import string
import eyed3.id3
from pydub import AudioSegment


def load_audio(path: string) -> AudioSegment:
    try:
        audio = AudioSegment.from_file(path, path[-3:])
        return audio
    except FileNotFoundError:
        pass


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
            self.dur_s = file_metadata.info.time_secs
        else:
            self.metadata = None

        self.name = os.path.basename(directory)[:-4]

    def get_name(self) -> string:
        return self.name
