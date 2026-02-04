import numpy as np
import sounddevice as sd
from multiprocessing import Process, Event, Value

from rain_mixing.backend.MusicFile import MusicFile
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


def playback_worker(audio_bytes, sample_rate, channels, sample_width,
                    pause_event: Event, stop_event: Event,
                    current_frame: Value, frame_total: Value,
                    volume_val: Value):
    dtype = np.int16 if sample_width == 2 else np.int32
    audio_array = np.frombuffer(audio_bytes, dtype=dtype).reshape(-1, channels)
    frame_total.value = len(audio_array)

    while not stop_event.is_set():

        def callback(outdata, frames, _time, _status):
            if stop_event.is_set():
                raise sd.CallbackStop()

            if pause_event.is_set():
                outdata.fill(0)
                return

            idx = current_frame.value
            chunk = audio_array[idx: idx + frames]

            if len(chunk) == 0:
                outdata.fill(0)
                raise sd.CallbackStop()  # Ends the stream, but not the process

            if len(chunk) < frames:
                res = (chunk * volume_val.value).astype(dtype)
                outdata[:len(chunk)] = res
                outdata[len(chunk):].fill(0)
                current_frame.value += len(chunk)
                raise sd.CallbackStop()
            else:
                boosted_chunk = chunk.astype(np.float32) * volume_val.value
                # Clipping
                if dtype == np.int16:
                    boosted_chunk = np.clip(boosted_chunk, -32768, 32767)
                elif dtype == np.int32:
                    boosted_chunk = np.clip(boosted_chunk, -2147483648,
                                            2147483647)

                outdata[:] = boosted_chunk.astype(dtype)
                current_frame.value += frames

        if pause_event.is_set() or current_frame.value >= len(audio_array):
            sd.sleep(100)
            continue

        # Inner block: Active Audio Stream
        with sd.OutputStream(samplerate=sample_rate, channels=channels,
                             callback=callback, dtype=dtype, blocksize=1024):
            while not stop_event.is_set() and not pause_event.is_set() \
                    and current_frame.value < len(audio_array):
                sd.sleep(100)


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
    def __init__(self):
        self.music_process = None

        self.pause_event = Event()
        self.stop_event = Event()

        self.volume = Value('d', 1.0)
        self.muted = False
        self.prev_volume = 0

        self.curr_frame = Value('i', 0)
        self.curr_frame_total = Value('i', 0)

        self.notifier = MusicNotifier()

    """
    Spawns a process to play a track selected by the user

    :param
        -   file: The file selected for playing
    """

    def play_track(self, file: MusicFile) -> None:
        self.kill_threads()

        file.load_audio()
        audio = file.audio

        # Reset flags
        self.stop_event.clear()
        self.pause_event.clear()
        self.curr_frame.value = 0

        self.music_process = Process(
            target=playback_worker,
            args=(
                audio.raw_data,
                audio.frame_rate,
                audio.channels,
                audio.sample_width,
                self.pause_event,
                self.stop_event,
                self.curr_frame,
                self.curr_frame_total,
                self.volume,
            )
        )
        self.music_process.start()
        self.notifier.notify_observers(file)

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
    Kills all threads managed by the music player, for usage when the user
    closes the app
    """

    def kill_threads(self) -> None:
        if self.music_process and self.music_process.is_alive():
            self.stop_event.set()
            self.music_process.join(0.1)
            self.music_process.terminate()
