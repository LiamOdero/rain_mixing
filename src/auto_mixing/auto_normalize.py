import os
import pyloudnorm as pyln
import soundfile as sf
from pydub import AudioSegment
from tqdm import tqdm

from constants.file_constants import SONG_DIR, INPUT_DATA_DIR, \
    LOGGING_EXTENSION, OUTPUT_DATA_DIR
from rain_mixing.utils.utils import wrapped_is_file

tracks = []
for filename in tqdm(os.listdir(SONG_DIR)):
    f = os.path.join(SONG_DIR, filename)

    loc = os.path.abspath(f)
    extension = f[-3:]
    track_name = filename[:-4]

    input_track = AudioSegment.from_file(file=loc, format=extension)

    # via https://github.com/csteinmetz1/pyloudnorm
    data, rate = sf.read(loc)

    # measure the loudness first
    meter = pyln.Meter(rate)  # create BS.1770 meter
    loudness = meter.integrated_loudness(data)

    # loudness normalize audio to -27.5 dB LUFS
    loudness_normalized_audio = pyln.normalize.loudness(data, loudness, -27.5)

    if loudness_normalized_audio.ndim > 1:
        channel1 = loudness_normalized_audio[:, 0]
    else:
        channel1 = loudness_normalized_audio

    output_track = AudioSegment(
        data=channel1.tobytes(),
        frame_rate=rate,
        sample_width=channel1.dtype.itemsize,
        channels=1
    )

    curr_length = len([name for name in os.listdir(INPUT_DATA_DIR) if
                       wrapped_is_file(INPUT_DATA_DIR, name)])

    input_filename = os.path.join(INPUT_DATA_DIR,
                                  f"input_{curr_length}.{LOGGING_EXTENSION}")
    input_track.export(input_filename)

    output_filename = os.path.join(OUTPUT_DATA_DIR,
                                   f"output_{curr_length}.{LOGGING_EXTENSION}")
    sf.write(output_filename, loudness_normalized_audio, rate, format='WAV')
