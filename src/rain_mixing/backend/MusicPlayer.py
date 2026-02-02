import numpy as np
import sounddevice as sd
from multiprocessing import Process, Event, Value

from rain_mixing.backend.MusicFile import MusicFile
from rain_mixing.backend.MusicNotifier import MusicNotifier


def playback_worker(audio_bytes, sample_rate, channels, sample_width,
                    pause_event, stop_event, volume_val):
    dtype = np.int16 if sample_width == 2 else np.int32
    audio_array = np.frombuffer(audio_bytes, dtype=dtype).reshape(-1, channels)

    current_frame = 0

    def callback(outdata, frames, _time, _status):
        nonlocal current_frame
        if stop_event.is_set():
            raise sd.CallbackStop()

        if pause_event.is_set():
            outdata.fill(0)
            return

        chunk = audio_array[current_frame: current_frame + frames]
        if len(chunk) < frames:
            res = (chunk * volume_val.value).astype(dtype)
            outdata[:len(chunk)] = res
            outdata[len(chunk):] = 0
            raise sd.CallbackStop()
        else:
            boosted_chunk = chunk.astype(np.float32) * volume_val.value

            if dtype == np.int16:
                boosted_chunk = np.clip(boosted_chunk,
                                        -32768, 32767)
            elif dtype == np.int32:
                boosted_chunk = np.clip(boosted_chunk,
                                        -2147483648, 2147483647)

            outdata[:] = boosted_chunk.astype(dtype)
            current_frame += frames

    with sd.OutputStream(samplerate=sample_rate,
                         channels=channels,
                         callback=callback,
                         dtype=dtype,
                         blocksize=1024):
        while not stop_event.is_set() and current_frame < len(audio_array):
            sd.sleep(100)


"""
Manages playing and controlling a MusicFile selected by the user
"""


class MusicPlayer:
    def __init__(self):
        self.music_process = None

        self.pause_event = Event()
        self.stop_event = Event()

        self.volume = Value('d', 1.0)
        self.muted = False
        self.prev_volume = 0

        self.notifier = MusicNotifier()

    def play_track(self, file: MusicFile) -> None:
        self.kill_threads()

        file.load_audio()
        audio = file.audio

        # Reset flags
        self.stop_event.clear()
        self.pause_event.clear()

        self.music_process = Process(
            target=playback_worker,
            args=(
                audio.raw_data,
                audio.frame_rate,
                audio.channels,
                audio.sample_width,
                self.pause_event,
                self.stop_event,
                self.volume
            )
        )
        self.music_process.start()
        self.notifier.notify_observers(file)

    """
    Toggle pause event used by music thread
    """

    def toggle_pause(self) -> None:
        if self.pause_event.is_set():
            self.pause_event.clear()
        else:
            self.pause_event.set()

    """
    Sets volume from 0.0 to 2.0 (2.0 is 200% volume)
    """

    def set_volume(self, value: float) -> None:
        if not self.muted:
            # Clamping between 0.0 and 2.0
            self.volume.value = max(0.0, min(2.0, value))
        else:
            self.prev_volume = max(0.0, min(2.0, value))

    def toggle_mute(self) -> None:
        if self.muted:
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
