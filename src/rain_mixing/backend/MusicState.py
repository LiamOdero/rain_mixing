from rain_mixing.backend.MusicFile import MusicFile

"""
Defines the state of the music currently being played. Does not include the
actual music file to prevent giving unnecessary information to observers
"""
class MusicState:
    def __init__(self, file: MusicFile) -> None:
        self.playing = False
        self.dur_s = file.audio.duration_seconds
        self.elapsed_dur_s = 0
        self.title = file.name
        self.metadata = file.metadata
