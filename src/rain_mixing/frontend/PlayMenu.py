from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkSlider

from rain_mixing.frontend.StateObserver import StateObserver


class PlayMenu(StateObserver):

    def __init__(self, parent: CTkFrame):
        super().__init__(parent)
        self.configure(corner_radius=0,
                       height=90,
                       fg_color="#1c1c1c")

        self.information_frame = InformationFrame(self)
        self.information_frame.grid(row=0, column=0,
                                    sticky="nsew",
                                    padx=(10, 30),
                                    pady=(15, 5))
        self.grid_columnconfigure(0, weight=1, uniform="group1")

        self.control_frame = ControlFrame(self)
        self.control_frame.grid(row=0, column=1,
                                sticky="nsew",
                                padx=(30, 30),
                                pady=(15, 5)),
        self.grid_columnconfigure(1, weight=5)

        self.volume_frame = VolumeFrame(self)
        self.volume_frame.grid(row=0, column=2,
                               sticky="nsew",
                               padx=(30, 10),
                               pady=(15, 5))
        self.grid_columnconfigure(2, weight=1, uniform="group1")


class InformationFrame(CTkFrame):

    def __init__(self, parent: CTkFrame) -> None:
        super().__init__(parent, fg_color="#1c1c1c")
        self.configure(corner_radius=0,
                       height=90)

        self.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_label = CTkLabel(self, text="Select A Track...",
                                    anchor="center", justify="center",
                                    font=("Segoe UI", 16))
        self.title_label.grid(column=0, row=0, sticky="nsew")

        self.author_label = CTkLabel(self, text="...",
                                     anchor="center", justify="center",
                                     font=("Segoe UI", 12))
        self.author_label.grid(column=0, row=1, sticky="nsew")


class ControlFrame(CTkFrame):
    def __init__(self, parent: CTkFrame) -> None:
        super().__init__(parent, fg_color="#1c1c1c")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        # setting up buttons on row 0
        self.button_container = CTkFrame(self, fg_color="transparent")
        self.button_container.grid(row=0, column=1,
                                   sticky="n", pady=10)

        self.shuffle_button = CTkButton(self.button_container, text="shuffle",
                                        width=60)
        self.shuffle_button.grid(row=0, column=0, padx=2)

        self.prev_button = CTkButton(self.button_container, text="prev",
                                     width=60)
        self.prev_button.grid(row=0, column=1, padx=2)

        self.play_button = CTkButton(self.button_container, text="play",
                                     width=60)
        self.play_button.grid(row=0, column=2, padx=2)

        self.next_button = CTkButton(self.button_container, text="next",
                                     width=60)
        self.next_button.grid(row=0, column=3, padx=2)

        self.loop_button = CTkButton(self.button_container, text="loop",
                                     width=60)
        self.loop_button.grid(row=0, column=4, padx=2)

        # labels and slider on row 2

        self.elapsed_label = CTkLabel(self, text="0:00")
        self.elapsed_label.grid(row=1, column=0, padx=10)

        self.play_slider = CTkSlider(self, state="disabled")
        self.play_slider.grid(row=1, column=1,
                              sticky="ew")
        self.play_slider.set(0)

        self.total_label = CTkLabel(self, text="- - : - -")
        self.total_label.grid(row=1, column=2, padx=10)


class VolumeFrame(CTkFrame):

    def __init__(self, parent: CTkFrame) -> None:
        super().__init__(parent, fg_color="#1c1c1c")
        self.configure(corner_radius=0,
                       height=90)
        self.grid_propagate(False)

        self.mute_button = CTkButton(self, text="mute", width=60)
        self.mute_button.grid(column=0, row=0, padx=5)

        self.vol_slider = CTkSlider(self)
        self.vol_slider.grid(column=1, row=0, sticky="we", padx=5)

        self.grid_rowconfigure(0, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
