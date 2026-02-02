from rain_mixing.backend.MusicFile import MusicFile
from rain_mixing.backend.MusicState import MusicState
from rain_mixing.frontend.StateObserver import StateObserver

"""
Observes the current state of the currently played music file and notifies
front end components of updates

Implements the observer design pattern
"""


class MusicNotifier:
    def __init__(self):
        # List of observers only of what music is playing and in what state
        self.state_observers = []

    def add_state_observer(self, state_observer: StateObserver) -> None:
        self.state_observers.append(state_observer)

    def notify_observers(self, file: MusicFile) -> None:
        curr_state = MusicState(file)
        for observer in self.state_observers:
            observer.update_state(curr_state)
