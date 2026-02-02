from multiprocessing import Process, Lock
from pydub.playback import play
from rain_mixing.backend.MusicFile import MusicFile
from rain_mixing.backend.MusicNotifier import MusicNotifier


"""
Defines the class that manages queuing and playing music to the user according
to their requests
"""

class MusicPlayer:
    def __init__(self):
        self.music_thread = None
        self.lock = Lock()
        self.notifier = MusicNotifier()

    """
    Loads in <file> then plays it on a new thread. Kills the current thread
    that is playing music
    """
    def play_track(self, file: MusicFile) -> None:

        with self.lock:
            # file loading should be locked since if two files are selected
            # to be played without locks, race conditions could on which one
            # ends up getting played

            print("loading")
            file.load_audio()
            print("file load complete")

            # override the current queue
            if self.music_thread:
                self.music_thread.kill()

            play_thread = Process(target=play,
                                  args=(file.audio,))
            self.music_thread = play_thread

            play_thread.start()
            self.notifier.notify_observers(file)

    def kill_threads(self) -> None:
        self.music_thread.kill()
