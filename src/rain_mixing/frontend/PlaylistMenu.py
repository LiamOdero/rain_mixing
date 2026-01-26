from customtkinter import CTkFrame
from rain_mixing.frontend.StateObserver import StateObserver


class PlaylistMenu(StateObserver):

    def __init__(self, parent: CTkFrame):
        super().__init__(parent)
        self.configure(fg_color="#1c1c1c")
