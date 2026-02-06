import queue
import random
import string

import numpy as np
import sounddevice as sd
from multiprocessing import Process, Event, Value, Queue

from customtkinter import CTk

from rain_mixing.backend.MusicFile import MusicFile, load_audio
from rain_mixing.backend.MusicNotifier import MusicNotifier

"""
Worker function that manages playing a single music file to the player

:param
    -   audio_bytes: The raw bytes read from the audio file
    -   sample_rate: Sample rate recorded in the original music file
    -   channels: Number of channels recorded in the original music file
    -   sample_width: Sample width recorded in the original music file
    -   pause_event: A shared memory event determining if music should be
    paused
    -   stop_event: A shared memory event determining if this worker should
    terminate
    -   current_frame: A shared memory value of the frame currently
    played by the worker
    -   frame_total: A shared memory value of the total number of frames in
    the current music
    -   volume_val: A shared memory value of a value from 0-2.0 of modifiers to
    the base volume
"""


def playback_worker(file_dict: dict[string, string],
                    message_queue: Queue,
                    pause_event: Event,
                    stop_event: Event,
                    next_queue: Queue,
                    prev_queue: Queue,
                    current_frame: Value,
                    frame_total: Value,
                    volume_val: Value,
                    loop_flag: Value,
                    random_flag: Value):
    while not stop_event.is_set():
        file_paths = list(file_dict)
        random_idxs = [i for i in range(len(file_paths))]
        random.shuffle(random_idxs)

        i = 0
        curr_idx = 0
        while i < len(file_paths):
            if stop_event.is_set():
                break

            path = file_paths[curr_idx % len(file_paths)]
            file_id = file_dict[path]
            audio = load_audio(path)

            audio_bytes = audio.raw_data
            sample_rate = audio.frame_rate
            channels = audio.channels
            sample_width = audio.sample_width
            dtype = np.int16 if sample_width == 2 else np.int32
            audio_array = np.frombuffer(audio_bytes,
                                        dtype=dtype).reshape(-1, channels)
            current_frame.value = 0
            frame_total.value = len(audio_array)

            message_queue.put(file_id)

            def callback(outdata, frames, _time, _status):
                if stop_event.is_set():
                    raise sd.CallbackStop()
                if pause_event.is_set():
                    outdata.fill(0)
                    return

                idx = current_frame.value
                chunk = audio_array[idx: idx + frames]

                if len(chunk) == 0 and not (
                        next_queue.empty() or prev_queue.empty()):
                    raise sd.CallbackStop()

                if len(chunk) < frames:
                    # Process final partial chunk
                    res = (chunk * volume_val.value).astype(dtype)
                    outdata[:len(chunk)] = res
                    outdata[len(chunk):].fill(0)
                    current_frame.value += len(chunk)
                    raise sd.CallbackStop()
                else:
                    # Normal playback math
                    boosted = chunk.astype(np.float32) * volume_val.value
                    # Clipping logic
                    outdata[:] = boosted.astype(dtype)
                    current_frame.value += frames

            with sd.OutputStream(samplerate=sample_rate, channels=channels,
                                 callback=callback, dtype=dtype):
                # This loop keeps the 'with' block alive while the song plays
                while not stop_event.is_set() and current_frame.value < len(
                        audio_array) and next_queue.empty() and prev_queue.empty():
                    sd.sleep(100)

            add_val = 0
            if not next_queue.empty() or not prev_queue.empty():
                while not next_queue.empty():
                    add_val += next_queue.get()

                while not prev_queue.empty():
                    add_val -= prev_queue.get()
            else:
                add_val = 1 - loop_flag.value

            i += add_val
            if random_flag.value:
                curr_idx = random_idxs[i]
            else:
                curr_idx = i



"""
Manages playing and controlling a MusicFile selected by the user

:attributes
    -   music_process: The current process managing the playing of music
    -   pause_event: A shared memory event determining if music should be
    paused
    -   stop_event: A shared memory event determining if this worker should
    terminate
    -   volume: A shared memory value of a value from 0-2.0 of modifiers to
    the base volume
    -   prev_volume: Volume set prior to muting a track
    -   curr_frame: A shared memory value of the frame currently
    played by the worker
    -   curr_frame_total: A shared memory value of the total number of frames
    in the current music
    -   notifier: A MusicNotifier used to make updates to the frontend
"""


class MusicPlayer:
    def __init__(self, root: CTk):
        self.music_process = None

        self.pause_event = Event()
        self.stop_event = Event()

        self.prev_queue = Queue()
        self.next_queue = Queue()

        self.updates_queue = Queue()

        self.volume = Value('d', 1.0)
        self.muted = False
        self.prev_volume = 0

        self.curr_frame = Value('i', 0)
        self.curr_frame_total = Value('i', 0)

        self.loop_flag = Value('i', 0)

        self.shuffle_flag = Value('i', 0)

        self.music_lookup = {}

        self.root = root

        self.notifier = MusicNotifier()

    """
    Spawns a process to play a tracks selected by the user

    :param
        -   file: The file selected for playing
    """

    def play_tracks(self, files: list[MusicFile]) -> None:
        self.kill_music_thread()

        # Reset flags
        self.stop_event.clear()
        self.pause_event.clear()
        self.curr_frame.value = 0

        worker_dict = self.build_lookup(files)

        self.music_process = Process(
            target=playback_worker,
            args=(
                worker_dict,
                self.updates_queue,
                self.pause_event,
                self.stop_event,
                self.next_queue,
                self.prev_queue,
                self.curr_frame,
                self.curr_frame_total,
                self.volume,
                self.loop_flag,
                self.shuffle_flag,
            )
        )
        self.music_process.start()
        self.check_updates()

    def check_updates(self) -> None:
        try:
            if not self.updates_queue.empty():
                new_file_id = self.updates_queue.get_nowait()
                new_file = self.music_lookup[new_file_id]

                self.notifier.notify_observers(new_file)
        except queue.Empty:
            pass
        finally:
            if self.music_process and self.music_process.is_alive():
                self.root.after(100, self.check_updates)

    def build_lookup(self, files: list[MusicFile]) -> dict[string: string]:
        self.music_lookup = {}
        worker_dict = {}

        for file in files:
            self.music_lookup[file.id] = file
            worker_dict[file.path] = file.id

        return worker_dict

    """
    Clears pause events and plays the current track
    """

    def play(self) -> None:
        self.pause_event.clear()

    """
    Sets the pause event and pauses the current track
    """

    def pause(self) -> None:
        self.pause_event.set()

    """
    Sets the currently played frame to one selected by the user

    :param
        -   value: The frame selected to be played
    """

    def seek(self, value: int) -> None:
        self.curr_frame.value = value

    def toggle_loop(self) -> None:
        self.loop_flag.value = 1 - self.loop_flag.value

    def toggle_shuffle(self) -> None:
        self.shuffle_flag.value = 1 - self.shuffle_flag.value

    """
    Returns a value from 0.0-1.0 representing percent completion of the current
    track

    :return
        -   progress: The % completion of the current track
    """

    def get_progress(self) -> float:
        curr_frame = self.curr_frame
        total_frames = self.curr_frame_total

        progress = curr_frame.value / total_frames.value
        return progress

    """
    Sets volume from 0.0 to 2.0 (2.0 is 200% volume)

    :param
        -   value: The volume modifier to apply
    """

    def set_volume(self, value: float) -> None:
        if not self.muted:
            # Clamping between 0.0 and 2.0
            self.volume.value = max(0.0, min(2.0, value))
        else:
            # Only change prev_volume so that track stays muted
            self.prev_volume = max(0.0, min(2.0, value))

    """
    Toggles whether or not the current track is muted
    """

    def toggle_mute(self) -> None:
        if self.muted:
            # set volume to the stored value of what the slider is currently on
            self.volume.value = self.prev_volume
        else:
            self.prev_volume = self.volume.value
            self.volume.value = 0

        self.muted = not self.muted

    def fire_next(self) -> None:
        self.next_queue.put(1)

    def fire_prev(self) -> None:
        self.prev_queue.put(1)

    def kill_music_thread(self) -> None:
        if self.music_process and self.music_process.is_alive():
            self.stop_event.set()
            self.music_process.terminate()
            self.music_process.join(0.1)

    """
    Kills all threads managed by the music player, for usage when the user
    closes the app
    """

    def kill_threads(self) -> None:
        self.kill_music_thread()
