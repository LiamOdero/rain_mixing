import string
from tkinter import Event
from tkinter.ttk import Style
from typing import Union
from ctkcomponents import CTkTreeview, CTkPopupMenu
from customtkinter import CTkFrame, CTkButton, filedialog, CTkEntry, \
    CTkScrollbar

from constants.file_constants import EXTENSION_LIST, EXTENSION_DIALOGUES
from rain_mixing.backend.Directory import Directory
from rain_mixing.backend.MusicFile import MusicFile


class FileMenu(CTkFrame):

    def __init__(self, parent: CTkFrame):
        super().__init__(parent, fg_color="#1c1c1c")

        # TODO: check if some data has already been saved
        self.root = Directory()

        # init search widgets
        self.search_field = CTkEntry(self, placeholder_text="Search...")
        self.search_field.grid(row=0,
                               column=0,
                               sticky="ew",
                               padx=(30, 30),
                               pady=(30, 30))
        self.search_field.bind("<KeyRelease>", self.search)

        # init button widgets
        self.add_folder = CTkButton(self, text="Add folder:",
                                    command=self.add_folder)

        # init button widgets
        self.add_file = CTkButton(self, text="Add file:",
                                  command=self.add_file)

        self.add_folder.grid(row=0,
                             column=1,
                             sticky="ew",
                             padx=(10, 5),
                             pady=(20, 20))

        self.add_file.grid(row=0,
                           column=2,
                           sticky="ew",
                           padx=(5, 10),
                           pady=(20, 20))

        self.grid_columnconfigure(0, weight=18)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=19)

        # init table widgets
        self.table = CTkTreeview(self, [])
        self.table.grid(row=1,
                        column=0,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(0, 10),
                        columnspan=3)

        self.table.label.grid_forget()
        self.table.treeview.grid_configure(column=0, row=1, sticky="nsew")
        self.table.grid_rowconfigure(1, weight=1)

        self.table_mapping = {}

        style = self.table.tree_style
        style.configure("Treeview",
                        font=("Segoe UI", 14),  # Change font family and size
                        rowheight=30)

        # TODO: scrollbar hiding?

        self.scrollbar = CTkScrollbar(self.table,
                                      command=self.table.treeview.yview)
        self.table.treeview.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 5), pady=10)

        # hover styling
        hover_style = Style()
        hover_style.theme_use("default")
        hover_style.configure("Treeview",
                              background="#2b2b2b",
                              foreground="white",
                              fieldbackground="#2b2b2b",
                              borderwidth=0)
        style.map("Treeview", background=[('selected', '#3D3D3D')])

        self.table.treeview.tag_configure("hover_effect", background="#333333")
        self.last_hovered = ""
        self.table.treeview.bind("<Motion>", self.on_mouse_move)
        self.table.treeview.bind("<Leave>", self.on_mouse_leave)

        # init right-click popup widgets
        self.popup = CTkPopupMenu(self,
                                  width=150,
                                  height=300,
                                  title="",
                                  fg_color="#222222",
                                  border_color="#3f3f3f",
                                  border_width=2,
                                  corner_radius=12)
        self.table.treeview.bind("<Button-3>", self.popup_event)
        self.table.treeview.bind("<Button-3>", self.popup_event)

        self.table.treeview.bind("<MouseWheel>", self.scroll_event)
        self.table.treeview.bind("<Button-4>", self.scroll_event)
        self.table.treeview.bind("<Button-5>", self.scroll_event)

    """
    Adds a user selected folder to a specified folder
    """

    def add_folder(self) -> None:
        path = filedialog.askdirectory(title="Select a Folder")

        # only proceed if the user has added a directory
        if path:
            new_dir = Directory(path)

            selection = self.table.treeview.selection()
            selected_item = None
            if selection:
                selected_item = self.table_mapping[selection[0]]

            if isinstance(selected_item, MusicFile):
                selection = ""
            elif isinstance(selected_item, Directory):
                selected_item.add_folder(new_dir)

            if new_dir.num_files > 0:
                self.root.sub_directories.append(new_dir)
                self.root.num_files += new_dir.num_files + 1
            new_rep = new_dir.get_dict()

            self.insert_items(new_rep, [new_dir], selection)

    def add_file(self) -> None:
        paths = filedialog.askopenfiles(title="Select Files",
                                        filetypes=EXTENSION_DIALOGUES)

        if paths:
            selection = self.table.treeview.selection()
            selected_item = None

            if selection:
                selected_item = self.table_mapping[selection[0]]

            if isinstance(selected_item, MusicFile):
                selection = ""

            new_files = []
            for path in paths:
                new_file = MusicFile(path.name)
                new_files.append(new_file)

                if selection:
                    selected_item.add_file(new_file)

            self.insert_items([file.name for file in new_files], new_files,
                              selection)

    """
    Uses cxtkcomponents implementation of inserting items but stores the ids
    associated with each directory / music file internally for selections
    """

    def insert_items(self, items: list,
                     file_items: list[Union[MusicFile, Directory]],
                     parent="") -> None:
        for i in range(len(items)):
            item = items[i]
            if isinstance(item, dict):
                # inserts the folder to the view
                id = self.table.treeview.insert(
                    parent, 'end', text=item['name'])
                self.table_mapping[id] = file_items[i]

                new_file_items = (file_items[i].files +
                                  file_items[i].sub_directories)

                # recursively call of subdirectories
                self.insert_items(item['children'], new_file_items, id)
            else:
                # inserts files into the view
                id = self.table.treeview.insert(parent, 'end', text=item)
                self.table_mapping[id] = file_items[i]

    """
    Searches the root directory for any matches of a keyword and updates
    the display accordingly
    
    :param
        -   event: Contains information on where the event took place
    """

    def search(self, _event: Event) -> None:
        search_term = self.search_field.get()
        search_results = self.root.search(search_term.lower())

        # it doesn't look like you can disable specific ids from being visible?
        # so aside from a very involved solution, looks like the easiest
        # way to apply a search is to destroy tree data and rebuild

        for item in self.table.treeview.get_children():
            self.table.treeview.delete(item)
        self.table_mapping = {}
        self.last_hovered = ""

        # something something state bug idk but this fixes it
        self.table.treeview.configure(cursor="")

        if search_results:
            file_names = [file.name for file in search_results.files]
            self.insert_items(file_names, search_results.files)

            for sub_dir in search_results.sub_directories:
                self.insert_items(sub_dir.get_dict(), [sub_dir])

    """
    Determines if scrolling should be possible dependant on if the right-click
    popup window is active
    """

    def scroll_event(self, _event: Event) -> string:
        if self.popup.winfo_exists() and self.popup.state() == "normal":
            # when the popup is active, disable scrolling
            return "break"
        else:
            return

    """
    Handles right click events on the table
    
    :param
        -   event: Contains information on where the event took place
    """

    def popup_event(self, event: Event) -> None:
        clicked_row = self.table.treeview.identify_row(event.y)

        if clicked_row:
            self.table.treeview.selection_set(clicked_row)
            self.table.treeview.focus(clicked_row)

            selected = self.table_mapping[clicked_row]

            # Configures the popup to display information for the selected
            # item
            if selected:
                name = ""
                if isinstance(selected, MusicFile):
                    name = selected.name
                elif isinstance(selected, Directory):
                    name = selected.get_name()

                self.popup.title.configure(text=name)
                self.popup.popup(event.x_root, event.y_root)
            else:
                # Close popup if no row clicked
                self.table.treeview.selection_remove(
                    self.table.treeview.selection())

    """
    Determines if hover effects should be applied or removed from a table row
    
    :param
        -   event: Contains information on where the event took place
    """

    def on_mouse_move(self, event: Event):
        item_id = self.table.treeview.identify_row(event.y)
        if item_id != self.last_hovered:
            # Remove the hover effect from the previous row
            if self.last_hovered:
                self.table.treeview.item(self.last_hovered, tags=())

            # Apply the hover effect to the new row
            if item_id:
                self.table.treeview.item(item_id, tags=("hover_effect",))
                self.table.treeview.configure(cursor="hand2")
            else:
                self.table.treeview.configure(cursor="")

            self.last_hovered = item_id

    """
    Removes hover effects when leaving the treeview

    :param
        -   event: Contains information on where the event took place
    """

    def on_mouse_leave(self, _event: Event):
        # Clear any hover effects
        if self.last_hovered:
            self.table.treeview.item(self.last_hovered, tags=())
            self.last_hovered = ""
