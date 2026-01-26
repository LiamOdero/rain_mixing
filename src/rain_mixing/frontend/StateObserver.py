from customtkinter import CTkFrame

"""
Defines an interface for parts of the GUI that react to changes in the
currently played music
"""


class StateObserver(CTkFrame):
    def __init__(self, parent: CTkFrame):
        super().__init__(parent)

    def update(self) -> None:
        pass
