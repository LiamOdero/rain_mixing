import os
import string
import eyed3.id3
from pydub import AudioSegment

"""
Loads an audiosegment from the request path and returns it.

:param
    -   path: The exact path to the file to load
:return
    -   audio: The audiosegment constructed by loading the audio file
:raise
    -   FileNotFoundError: When the requested file cannot be loaded
"""


def load_audio(path: string) -> AudioSegment:
    try:
        audio = AudioSegment.from_file(path, path[-3:])
        return audio
    except FileNotFoundError:
        pass


"""
Defines a music file stored by the user and some associated metadata

:attributes
    -   id: A unique identifier for this music file
    -   path: The full path to the specified file
    PRECONDITION: path refers to a real supported music file at the time of
    file loading (ie: could be deleted before application closes)
    -   metadata: Contains the metadata stored in the associated file
    -   title: The name of the file
"""


class MusicFile:

    def __init__(self, directory: string, id: int) -> None:
        self.id = id
        self.path = directory

        file_metadata = eyed3.load(self.path)
        if file_metadata:
            self.metadata = file_metadata.tag
            self.dur_s = file_metadata.info.time_secs
        else:
            self.metadata = None

        self.title = os.path.basename(directory)[:-4]

    def get_name(self) -> string:
        return self.title
