import os
import string
from typing import Any
from numpy import ndarray, dtype, float64
from pydub import AudioSegment
from pydub.utils import make_chunks
import numpy as np
import torch
from tqdm import tqdm
from torch import save, load
from auto_mixing.models.MixingNN import MixingNN
from rain_mixing.utils.utils import wrapped_is_file
from constants.file_constants import (INPUT_DATA_DIR, OUTPUT_DATA_DIR,
                                      LOGGING_EXTENSION, MODEL_DIR)
from constants.model_constants import CHUNKS
from constants.audio_constants import S_TO_MS

"""
Takes in an unmodified track and it's edit and saves it to the corresponding
logging folder

:param
    -   input_track: An unmodified track that the user has edited
    -   output_track: The edited version of <input_track>
    -   input_dir: The directory to write input data to
    -   output_dir: The directory to write output data to
"""


def log_edit(input_track: AudioSegment,
             output_track: AudioSegment,
             input_dir: string = INPUT_DATA_DIR,
             output_dir: string = OUTPUT_DATA_DIR) -> None:

    curr_length = len([name for name in os.listdir(input_dir) if
                       wrapped_is_file(input_dir, name)])

    input_filename = os.path.join(input_dir,
                                  f"input_{curr_length}.{LOGGING_EXTENSION}")
    input_track.export(input_filename)

    output_filename = os.path.join(output_dir,
                                   f"output_{curr_length}.{LOGGING_EXTENSION}")
    output_track.export(output_filename)


"""
Saves <model>'s state dict to< MODEL_DIR>

:param
    -   model: The MixingNN chosen to save
"""


def save_model(model: MixingNN) -> None:
    curr_length = len([name for name in os.listdir(MODEL_DIR) if
                       wrapped_is_file(MODEL_DIR, name)])
    model_filename = os.path.join(MODEL_DIR,
                                  f"model_{curr_length}.pth")
    save(model.state_dict(), model_filename)


"""
Loads the model saved with <model_num> to the input <model>
PRECONDITION: <model_num> is compatible with the input model

:param
    -   model: The MixingNN to load data into
    -   model_num: The file no. associated with the requested model
"""


def load_model(model: MixingNN, model_num: int) -> None:
    model_filename = os.path.join(MODEL_DIR,
                                  f"model_{model_num}.pth")

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.load_state_dict(load(model_filename,
                               map_location=torch.device(device),
                               weights_only=True))
    model.to(device)
    model.eval()


"""
Returns a list of <CHUNKS> dBFS samples from <track>

:param
    -   track: The track to extrack dBFS samples from
:return
    -   chunk_dBFS: A list of chunked dBFS data from <track>
        length = CHUNKS
"""


def sample_dBFS(track: AudioSegment) -> ndarray[tuple[int, ...], dtype[Any]]:
    # Ensure that there will be <CHUNKS> many audio chunks
    length = track.duration_seconds * S_TO_MS
    chunk_length = length // CHUNKS

    chunks = make_chunks(track, chunk_length)

    chunk_dBFS = np.array([chunk.dBFS for chunk in chunks])
    # TODO: see if -1e2 is sufficient
    chunk_dBFS = np.nan_to_num(chunk_dBFS, nan=0.0, neginf=-1e2)

    if chunk_dBFS.shape[0] > CHUNKS:
        average = np.average(chunk_dBFS[CHUNKS - 1:])
        chunk_dBFS[CHUNKS - 1] = average
        chunk_dBFS = chunk_dBFS[:CHUNKS]

    return chunk_dBFS


"""
Takes in the completed edits and saves <CHUNKS> dBFS samples from each
corresponding input and output track This is mainly intended to be used as
input for non-transformers models

:param
    -   input_tracks: An ordered list of all original tracks that were edited
    -   output_tracks: An ordered list of all edited tracks. Each index
    corresponds to the same track in <input_tracks>

:return
    -   input_dBFS: A 2D npy list of dBFS data that is dimension
    len(input_tracks) x <CHUNKS>
    -   output_dBFS: A 2D npy list of dBFS data that is dimension
    len(input_tracks) x <CHUNKS>
"""


def sample_logs(input_tracks: list[AudioSegment],
                output_tracks: list[AudioSegment]) -> (
        tuple)[ndarray[dtype[float64]], ndarray[dtype[float64]]]:
    input_dBFS = np.empty((len(input_tracks), CHUNKS))
    output_dBFS = np.empty((len(output_tracks), CHUNKS))

    # Getting chunked dBFS per each track
    for i in range(len(input_tracks)):
        input_track = input_tracks[i]
        input_dBFS[i] = sample_dBFS(input_track)

        output_track = output_tracks[i]
        output_dBFS[i] = sample_dBFS(output_track)

    return input_dBFS, output_dBFS


"""
Reads data from the logging directory and creates an array of input and
output tracks

:return
    -   input_data: Unmodified tracks that have been selected by users
    -   output_data: Tracks that have had they volumes modified by users
"""


def read_logging_data(input_dir: string = INPUT_DATA_DIR,
                      output_dir: string = OUTPUT_DATA_DIR) \
        -> tuple[list[AudioSegment], list[AudioSegment]]:

    input_data = []
    print("importing input data...")
    for name in tqdm(os.listdir(input_dir)):
        if wrapped_is_file(input_dir, name):
            abs_file = os.path.join(input_dir, name)
            track = AudioSegment.from_file(file=abs_file,
                                           extension=f"{LOGGING_EXTENSION}")
            input_data.append(track)

    output_data = []
    print("importing output data...")
    for name in tqdm(os.listdir(output_dir)):
        if wrapped_is_file(output_dir, name):
            abs_file = os.path.join(output_dir, name)
            track = AudioSegment.from_file(file=abs_file,
                                           extension=f"{LOGGING_EXTENSION}")
            output_data.append(track)

    return input_data, output_data
