from customtkinter import CTk

from rain_mixing.backend.MusicNotifier import MusicNotifier
from rain_mixing.backend.MusicPlayer import MusicPlayer
from rain_mixing.data.DirectoryLogger import DirectoryLogger
from rain_mixing.frontend.Screen import Screen

"""
Defines basic properties of the window of the application
"""


class Window(CTk):

    def __init__(self):
        super().__init__()

        self.title("Rain Music Player")

        # Window Resolution
        # TODO: Initial geometry + placement
        self.geometry("1600x800")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.logger = DirectoryLogger()

        self.music_player = MusicPlayer()

        self.root = self.logger.load_dirs()
        self.screen = Screen(self, self.root, self.music_player)
        self.screen.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self) -> None:
        self.destroy()
        self.music_player.kill_threads()

        print("Logging user data...")
        self.logger.log_dirs(self.root)
        print("Finished")
