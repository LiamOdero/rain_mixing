import numpy as np
import sounddevice as sd
from multiprocessing import Process, Event

from rain_mixing.backend.MusicFile import MusicFile
from rain_mixing.backend.MusicNotifier import MusicNotifier


def playback_worker(audio_bytes, sample_rate, channels, sample_width,
                    pause_event, stop_event):

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
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):] = 0
            raise sd.CallbackStop()
        else:
            outdata[:] = chunk
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
                self.stop_event
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
    Kills all threads managed by the music player, for usage when the user
    closes the app
    """
    def kill_threads(self) -> None:
        if self.music_process and self.music_process.is_alive():
            self.stop_event.set()
            self.music_process.join(0.1)
            self.music_process.terminate()
