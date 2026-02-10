from rain_mixing.backend.MusicFile import MusicFile
from rain_mixing.frontend.StateObserver import StateObserver

"""
Observes the current state of the currently played music file and notifies
front end components of updates

Implements the observer design pattern

:attributes
    -   state_observers: A list of instances of <StateObserver>
    to notify on any updates
"""


class MusicNotifier:
    def __init__(self):
        # List of observers only of what music is playing and in what state
        self.state_observers = []

    """
    Adds an observer to self.state_observers

    :param
        -   state_observer: the observer to add
    """

    def add_state_observer(self, state_observer: StateObserver) -> None:
        self.state_observers.append(state_observer)

    """
    Calls the update function of all observer this notifier manages

    :param
        -   file: The music file relevant to the state update
    """

    def notify_observers(self, state: MusicFile) -> None:
        for observer in self.state_observers:
            observer.update_state(state)
