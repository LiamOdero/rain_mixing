import os
import string
from tkinter import Event
from typing import Union

from PIL import Image
from ctkcomponents import CTkPopupMenu
from customtkinter import CTkFrame, CTkButton, CTkImage

from constants.file_constants import GUI_ASSET_DIR
from rain_mixing.backend.Directory import Directory
from rain_mixing.backend.MusicFile import MusicFile

BTN_OPTION = {
    "compound": "left",
    "anchor": "w",
    "fg_color": "transparent",
    "text_color": ("black", "white"),
    "corner_radius": 5,
    "hover_color": ("gray90", "gray25")
}


class SelectionPopupMenu(CTkPopupMenu):
    def __init__(self, parent: CTkFrame):
        super().__init__(parent,
                         width=150,
                         title="",
                         fg_color="#222222",
                         border_color="#3f3f3f",
                         border_width=2,
                         corner_radius=12)

        self.frame.pack(side="top", fill="x", anchor="n")
        play_path = os.path.join(GUI_ASSET_DIR, "play_menu.png")
        self.play_row = PopupRow(self, play_path, "Play")

    def trigger_popup(self, selection: Union[Directory, MusicFile],
                      event: Event) -> None:

        # Configures the popup to display information for the selected
        # item

        name = ""
        if isinstance(selection, MusicFile):
            name = selection.name
        elif isinstance(selection, Directory):
            name = selection.get_name()

        self.title.configure(text=name)
        self.play_row.configure(command=lambda: print(name))

        self.popup(event.x_root, event.y_root)


class PopupRow(CTkButton):
    def __init__(self,
                 parent: CTkPopupMenu,
                 path: string,
                 label: string) -> None:

        img_data = Image.open(path)

        self.btn_image = CTkImage(light_image=img_data,
                                  dark_image=img_data,
                                  size=(16, 16))  # Standard icon size
        super().__init__(parent.frame,
                         text=label,
                         border_color="#3f3f3f",
                         image=self.btn_image,
                         **BTN_OPTION)

        self.pack(side="top", fill="x", padx=10, pady=(2, 2), expand=False)
