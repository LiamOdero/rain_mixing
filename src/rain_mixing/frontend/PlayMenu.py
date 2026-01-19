from customtkinter import CTkFrame


class PlayMenu(CTkFrame):

    def __init__(self, parent: CTkFrame):
        super().__init__(parent,
                         corner_radius=0,
                         height=90,
                         fg_color="#1c1c1c")
