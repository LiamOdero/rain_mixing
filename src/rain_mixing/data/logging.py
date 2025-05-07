import os
from numpy import ndarray, dtype, float64
from pydub import AudioSegment
from pydub.utils import make_chunks
import numpy as np
from ..utils.utils import wrapped_is_file
from ..utils.utils import (INPUT_DATA_DIR, OUTPUT_DATA_DIR,
                           S_TO_MS)

CHUNKS = 100

"""
Takes in an unmodified track and it's edit and saves it to the corresponding
logging folder

:param
    -   input_track: An unmodified track that the user has edited
    -   output_track: The edited version of <input_track>
"""


def log_edit(input_track: AudioSegment, output_track: AudioSegment) -> None:
    curr_length = len([name for name in os.listdir(INPUT_DATA_DIR) if
                       wrapped_is_file(INPUT_DATA_DIR, name)])

    input_filename = os.path.join(INPUT_DATA_DIR,
                                  f"input_{curr_length}.mp3")
    input_track.export(input_filename)

    output_filename = os.path.join(OUTPUT_DATA_DIR,
                                   f"output_{curr_length}.mp3")
    output_track.export(output_filename)


"""
Takes in the completed edits and saves <CHUNKS> dBFS samples from each
corresponding input and output track This is mainly intended to be used as
input for non-transformers models

:param
    -   input_tracks: An ordered list of all original tracks that were edited
    -   output_tracks: An ordered list of all edited tracks. Each index
    corresponds to the same track in <input_tracks>

:return
    -   input_dbfs: A 2D npy list of dBFS data that is dimension
    len(input_tracks) x <CHUNKS>
    -   output_dbfs: A 2D npy list of dBFS data that is dimension
    len(input_tracks) x <CHUNKS>
"""


def chunk_dbfs(input_tracks: list[AudioSegment],
               output_tracks: list[AudioSegment]) -> (
        tuple)[ndarray[dtype[float64]], ndarray[dtype[float64]]]:
    input_dbfs = np.empty((len(input_tracks), CHUNKS))
    output_dbfs = np.empty((len(output_tracks), CHUNKS))
    # Getting chunked dBFS per each track
    for i in range(len(input_tracks)):
        input_track = input_tracks[i]
        output_track = output_tracks[i]

        # Ensure that there will be <CHUNKS> many audio chunks
        length = input_track.duration_seconds * S_TO_MS
        chunk_length = np.ceil(length / CHUNKS)

        input_chunks = make_chunks(input_track, chunk_length)
        # TODO: remove eventually
        assert len(input_chunks) == CHUNKS
        input_dbfs[i] = np.array([[chunk.dBFS for chunk in input_chunks]])

        output_chunks = make_chunks(output_track, chunk_length)
        output_dbfs[i] = np.array([[chunk.dBFS for chunk in output_chunks]])

    return input_dbfs, output_dbfs


"""
Reads data from the logging directory and creates an array of input and
output tracks

:return
    -   input_data: Unmodified tracks that have been selected by users
    -   output_data: Tracks that have had they volumes modified by users
"""


def read_logging_data() -> tuple[list[AudioSegment], list[AudioSegment]]:
    input_data = []
    for name in os.listdir(INPUT_DATA_DIR):
        if wrapped_is_file(INPUT_DATA_DIR, name):
            abs_file = os.path.join(INPUT_DATA_DIR, name)
            track = AudioSegment.from_file(file=abs_file, extension="mp3")
            input_data.append(track)

    output_data = []
    for name in os.listdir(OUTPUT_DATA_DIR):
        if wrapped_is_file(OUTPUT_DATA_DIR, name):
            abs_file = os.path.join(OUTPUT_DATA_DIR, name)
            track = AudioSegment.from_file(file=abs_file, extension="mp3")
            output_data.append(track)

    return input_data, output_data
