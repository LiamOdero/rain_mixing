from tkinter import Tk
from customtkinter import CTkFrame

from rain_mixing.backend.Directory import Directory
from rain_mixing.backend.MusicPlayer import MusicPlayer
from rain_mixing.frontend.FileMenu import FileMenu
from rain_mixing.frontend.PlayMenu import PlayMenu
from rain_mixing.frontend.PlaylistMenu import PlaylistMenu
from rain_mixing.frontend.PlaylistSelector import PlaylistSelector


class Screen(CTkFrame):

    def __init__(self, window: Tk, root: Directory, music_player: MusicPlayer):
        super().__init__(window, fg_color="#141414")

        self.playlist_selector = PlaylistSelector(self)

        self.file_menu = FileMenu(self, root, music_player)

        self.playlist_menu = PlaylistMenu(self)

        self.play_menu = PlayMenu(self, music_player)
        music_player.notifier.add_state_observer(self.play_menu)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=19)

        self.grid_rowconfigure(0, weight=19)
        self.grid_rowconfigure(1, weight=1)

        self.playlist_selector.grid(row=0,
                                    column=0,
                                    sticky="nsew",
                                    padx=(10, 5),
                                    pady=(30, 20))

        self.playlist_menu.grid(row=0,
                                column=1,
                                sticky="nsew",
                                padx=(5, 10),
                                pady=(30, 20))

        self.file_menu.grid(row=0,
                            column=1,
                            sticky="nsew",
                            padx=(5, 10),
                            pady=(30, 20))

        self.file_menu.tkraise()

        self.play_menu.grid(row=1,
                            column=0,
                            columnspan=2,
                            sticky="nsew")
