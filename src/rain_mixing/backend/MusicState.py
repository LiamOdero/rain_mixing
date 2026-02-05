from rain_mixing.backend.MusicFile import MusicFile

"""
Defines the state of the music currently being played. Does not include the
actual music file to prevent giving unnecessary information to observers

:attributes
    - dur_s: the duration in seconds of the music
    - title: the title of the music
    - id: the id associated with the music
    - metadata: all of the metadata associated with the music file
"""


class MusicState:
    def __init__(self, file: MusicFile) -> None:
        self.title = file.name
        self.id = file.id

        self.metadata = file.metadata
        self.dur_s = file.dur_s
