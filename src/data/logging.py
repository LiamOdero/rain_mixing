from pydub import AudioSegment
from pydub.utils import make_chunks
import numpy as np
from rain_mixing.src.utils.utils import *

CHUNKS = 100

"""
Takes in an unmodified track and it's edit and saves it to the corresponding logging folder

:param
    -   input_track: An unmodified track that the user has edited
    -   output_track: The edited version of <input_track>
"""
def log_edit(input_track: AudioSegment, output_track: AudioSegment):
    curr_length = len([name for name in os.listdir(INPUT_DATA_DIR) if os.path.isfile(name)])\

    input_filename = os.path.join(INPUT_DATA_DIR, f"input_{curr_length}.mp3")
    input_track.export(input_filename)

    output_filename = os.path.join(OUTPUT_DATA_DIR, f"output_{curr_length}.mp3")
    output_track.export(output_filename)


"""
Takes in the completed edits and saves <CHUNKS> dBFS samples from each corresponding input and output track
This is mainly intended to be used as input for non-transformers models

:param
    -   input_tracks: An ordered list of all original tracks that were edited 
    -   output_tracks: An ordered list of all edited tracks. Each index corresponds to the same track in <input_tracks>
    
:return
    -   input_dbfs: A 2D npy list of dBFS data that is dimension len(input_tracks) x <CHUNKS>
    -   output_dbfs: A 2D npy list of dBFS data that is dimension len(input_tracks) x <CHUNKS>
"""
def chunk_dbfs(input_tracks: list[AudioSegment], output_tracks: list[AudioSegment]):
    input_dbfs = np.empty((len(input_tracks), CHUNKS))
    output_dbfs = np.empty((len(output_tracks), CHUNKS))
    # Getting chunked dBFS per each track
    for i in range(len(input_tracks)):
        input_track = input_tracks[i]
        output_track = output_tracks[i]

        # Computing how long to make each chunk to ensure that there will be <CHUNKS> many
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
Merges potentially existing chunked dBFS data with <new_data> and saves it to disk

:param 
    -   new_data: the new chunked dBFS data to save
    -   filename: The absolute path to where chunked dBFS data should be merged from and saved
"""
def merge_npy_data(new_data: np.array, filename: str):
    # Creating the merged data
    if os.path.isfile(filename):
        # Only merge data if the required file already exists, as otherwise it will fail
        with open(filename, "rb") as f:
            existing_data = np.load(f)
            merged_data = np.concatenate((existing_data, new_data), axis=0)
    else:
        merged_data = new_data

    # Saving the merged data
    with open(filename, "wb") as f:
        np.save(f, merged_data)
