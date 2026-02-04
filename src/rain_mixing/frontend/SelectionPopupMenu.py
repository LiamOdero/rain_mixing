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
from rain_mixing.backend.MusicPlayer import MusicPlayer

BTN_OPTION = {
    "compound": "left",
    "anchor": "w",
    "fg_color": "transparent",
    "text_color": ("black", "white"),
    "corner_radius": 5,
    "hover_color": ("gray90", "gray25")
}

"""
Defines a popup menu that appears when a user right clicks in an area
where music files are shown
"""


class SelectionPopupMenu(CTkPopupMenu):
    def __init__(self, parent: CTkFrame, music_player: MusicPlayer):
        super().__init__(parent,
                         width=250,
                         title="",
                         fg_color="#222222",
                         border_color="#3f3f3f",
                         border_width=2,
                         corner_radius=12)

        self.frame.pack(side="top", fill="x", anchor="n")

        play_path = os.path.join(GUI_ASSET_DIR, "play_menu.png")
        self.play_row = PopupRow(self, play_path, "Play")
        self.music_player = music_player

    """
    Configures the popup to display information for the selected item

    :param
        -   selection: The directory or music file that the user has right
        clicked on
        -   event: Details information on the right click event, used to
        extract mouse position information
    """

    def trigger_popup(self, selection: Union[Directory, MusicFile],
                      event: Event) -> None:
        name = selection.get_name()

        self.title.configure(text=name)

        if isinstance(selection, Directory):
            self.play_row.configure(command=lambda: print(name))
        else:
            self.play_row.configure(
                command=lambda: self.music_player.play_track(selection))

        self.popup(event.x_root, event.y_root)


"""
Defines what one row inside a popup menu should look like
"""


class PopupRow(CTkButton):
    def __init__(self,
                 parent: CTkPopupMenu,
                 path: string,
                 label: string) -> None:
        img_data = Image.open(path)

        self.btn_image = CTkImage(light_image=img_data,
                                  dark_image=img_data,
                                  size=(16, 16))
        super().__init__(parent.frame,
                         text=label,
                         border_color="#3f3f3f",
                         image=self.btn_image,
                         **BTN_OPTION)

        self.pack(side="top", fill="x", padx=10, pady=(2, 2), expand=False)
