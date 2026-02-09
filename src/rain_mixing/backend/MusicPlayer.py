import multiprocessing
import queue
import random
import string
from typing import Union

import numpy as np
import sounddevice as sd
from torch.multiprocessing import Process, Event, Value, Queue

from customtkinter import CTk

from auto_mixing.data.logging import load_model
from auto_mixing.models.ChunkMixingNN import ChunkMixingNN
from auto_mixing.models.MixingNN import MixingNN
from constants.file_constants import RAIN_FILE, MODEL_NUM
from rain_mixing.backend.MusicFile import MusicFile, load_audio
from rain_mixing.backend.MusicNotifier import MusicNotifier

"""
Worker function that manages playing a single music file to the player

:param
    -   file_queue: Message Queue detailing requested files to play
    -   sample_rate: The model used to mix file audio, if any
    -   out_queue: Message queue to inform main thread of changes in played
    music
    -   pause_event: A shared memory event determining if music should be
    paused
    -   stop_event: A shared memory event determining if this worker should
    terminate
    -   next_queue: Message Queue to make requests to go to next file
    -   prev_queue: Message Queue to make requests to go to the previous file
    -   frame_total: A shared memory value of the current total number of
    frames in the currently played music
    -   volume_val: A shared memory value of a value from 0-2.0 of modifiers to
    the base volume
    -   loop_flag: Determines if the currently played music should be looped
    -   random_flag: Determines if the next selected track should be random
"""


def playback_worker(file_queue: Queue,
                    model: Union[MixingNN, None],
                    out_queue: Queue,
                    pause_event: Event,
                    stop_event: Event,
                    next_queue: Queue,
                    prev_queue: Queue,
                    current_frame: Value,
                    frame_total: Value,
                    volume_val: Value,
                    loop_flag: Value,
                    random_flag: Value):
    file_dict = {}
    while not stop_event.is_set():
        while not file_queue.empty():
            # empty the file queue and only play the most recent request
            file_dict = file_queue.get()

        file_paths = list(file_dict)
        random_idxs = [i for i in range(len(file_paths))]
        random.shuffle(random_idxs)

        i = 0

        while file_queue.empty() and file_paths:
            if stop_event.is_set():
                break

            if random_flag.value and not loop_flag.value:
                curr_idx = random_idxs[i]
            else:
                curr_idx = i

            path = file_paths[curr_idx % len(file_paths)]
            file_id = file_dict[path]
            audio = load_audio(path)

            if model:
                audio = model.mix_track(audio)

            audio_bytes = audio.raw_data
            sample_rate = audio.frame_rate
            channels = audio.channels
            sample_width = audio.sample_width
            dtype = np.int16 if sample_width == 2 else np.int32
            audio_array = np.frombuffer(audio_bytes,
                                        dtype=dtype).reshape(-1, channels)
            current_frame.value = 0
            frame_total.value = len(audio_array)

            out_queue.put(file_id)

            def callback(outdata, frames, _time, _status):
                if stop_event.is_set():
                    raise sd.CallbackStop()
                if pause_event.is_set():
                    outdata.fill(0)
                    return

                idx = current_frame.value
                chunk = audio_array[idx: idx + frames]

                if len(chunk) == 0 and not (
                        next_queue.empty() or prev_queue.empty() or
                        file_queue.empty() or loop_flag.value):
                    raise sd.CallbackStop()

                if len(chunk) < frames:
                    # Process final partial chunk
                    res = (chunk * volume_val.value).astype(dtype)
                    outdata[:len(chunk)] = res
                    outdata[len(chunk):].fill(0)
                    current_frame.value += len(chunk)

                    if not loop_flag.value:
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
                while not stop_event.is_set() and (
                        current_frame.value < len(audio_array) and (
                        next_queue.empty() and prev_queue.empty() and (
                        file_queue.empty()
                        ))):
                    sd.sleep(100)

            if not file_queue.empty():
                # reset loop to get the next file
                break

            add_val = 0
            # emptying next / prev requests
            if not next_queue.empty() or not prev_queue.empty():
                while not next_queue.empty():
                    add_val += next_queue.get()

                while not prev_queue.empty():
                    add_val -= prev_queue.get()
            else:
                add_val = 1 - loop_flag.value
            i += add_val


"""
Manages playing and controlling a MusicFile selected by the user

:attributes
    -   music_process: The process managing the playing of music
    -   file_queue: Message Queue detailing requested files to play
    -   pause_event: A shared memory event determining if music should be
    paused
    -   stop_event: A shared memory event determining if this worker should
    terminate
    -   next_queue: Message Queue to make requests to go to next file
    -   prev_queue: Message Queue to make requests to go to the previous file
    -   update_queue: Message queue to inform main thread of changes in played
    music
    -   volume: A shared memory value of a value from 0-2.0 of modifiers to
    the base volume
    -   muted: A shared memory value determining if music should be muted
    -   prev_volume: Volume set prior to muting a track
    -   curr_frame: A shared memory value of the frame currently
    played by the worker
    -   curr_frame_total: A shared memory value of the total number of frames
    in the current music
    -   loop_flag: Determines if the currently played music should be looped
    -   shuffle_flag: Determines if the next selected track should be random
    -   music_lookup: Lookup table of music ids to file paths
    -   root: The window of the application
    -   notifier: A MusicNotifier used to make updates to the frontend
    -   model: The model used to mix music
    -   rain_thread: The process managing rain SFX
"""


class MusicPlayer:
    def __init__(self, root: CTk):
        self.music_process = None
        self.file_queue = Queue()

        self.pause_event = Event()
        self.pause_event.set()
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

        multiprocessing.set_start_method("spawn", force=True)

        self.model = ChunkMixingNN()
        self.model.share_memory()
        load_model(self.model, MODEL_NUM)

        rain_queue = Queue()
        rain_queue.put({RAIN_FILE: ""})

        # Most of the values we dont actually care about, but rain in the bg
        # should share volume with and pausing with the main track
        self.rain_thread = Process(
            target=playback_worker,
            args=(
                rain_queue,
                None,
                Queue(),
                self.pause_event,
                Event(),
                Queue(),
                Queue(),
                Value('i', 0),
                Value('i', 0),
                self.volume,
                Value('i', 1),
                Value('i', 0),
            )
        )
        self.rain_thread.start()

        self.music_process = Process(
            target=playback_worker,
            args=(
                self.file_queue,
                self.model,
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

    """
    Spawns a process to play a tracks selected by the user

    :param
        -   file: The file selected for playing
    """

    def play_tracks(self, files: list[MusicFile]) -> None:
        self.curr_frame.value = 0
        self.pause_event.set()

        worker_dict = self.build_lookup(files)
        self.file_queue.put(worker_dict)

        self.check_updates()

    """
    Periodically checks if there are any changes in the currently played music
    """

    def check_updates(self) -> None:
        try:
            if not self.updates_queue.empty():
                # clear the pause once the message comes through since that
                # signifies the track is ready to play
                self.pause_event.clear()
                new_file_id = self.updates_queue.get_nowait()
                new_file = self.music_lookup[new_file_id]

                self.notifier.notify_observers(new_file)
        except queue.Empty:
            pass
        finally:
            if self.music_process and self.music_process.is_alive():
                self.root.after(100, self.check_updates)

    """
    Uses a list of music files to build a lookup table of file ids to paths
    and vice versa

    :param
        -   files: The list of files to make a lookup table for

    :return
        -   worker_dict: A lookup table of paths to ids for worker thread
        use
    """

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

    """
    Toggles whether or not the music player is set to loop the current track
    """

    def toggle_loop(self) -> None:
        self.loop_flag.value = 1 - self.loop_flag.value

    """
    Toggles whether or not the music player is set to shuffle track order
    """

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

    """
    Makes a request to move to the next track in the current playlist
    """

    def fire_next(self) -> None:
        self.next_queue.put(1)

    """
    Makes a request to move to the previous track in the current playlist
    """

    def fire_prev(self) -> None:
        self.prev_queue.put(1)

    """
    Safely kills the currently active music thread
    """

    def kill_music_thread(self) -> None:
        if self.music_process and self.music_process.is_alive():
            self.stop_event.set()
            self.pause_event.set()

            self.music_process.join(timeout=2.0)

            if self.music_process.is_alive():
                self.music_process.terminate()
                self.music_process.join()

    """
    Kills all threads managed by the music player, for usage when the user
    closes the app
    """

    def kill_threads(self) -> None:
        self.kill_music_thread()

        if self.rain_thread and self.rain_thread.is_alive():
            self.rain_thread.terminate()
            self.rain_thread.join(0.1)
