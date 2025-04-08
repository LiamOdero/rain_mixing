from pydub import AudioSegment
from pydub.utils import make_chunks
import numpy as np
from rain_mixing.src.utils.utils import *

CHUNKS = 100

def log_dbfs(input_track: AudioSegment, output_track: AudioSegment):
    verify_dir(CHUNK_DIR)
    length = input_track.duration_seconds * S_TO_MS
    chunk_length = length // CHUNKS

    input_chunks = make_chunks(input_track, chunk_length)
    input_dbfs = np.array([[chunk.dBFS for chunk in input_chunks]])

    output_chunks = make_chunks(output_track, chunk_length)
    output_dbfs = np.array([[chunk.dBFS for chunk in output_chunks]])

    chunk_verification = verify_dir(CHUNK_DIR)
    if not chunk_verification:
        raise Exception("Chunk Directory verification failed")

    merge_npy_data(input_dbfs, INPUT_CHUNK_FILE)
    merge_npy_data(output_dbfs, OUTPUT_CHUNK_FILE)

    with open(OUTPUT_CHUNK_FILE, "rb") as f:
        test = np.load(f)
        pass


def merge_npy_data(new_data: np.array, filename: str):

    if os.path.isfile(filename):
        with open(filename, "rb") as f:
            existing_data = np.load(f)
            merged_data = np.concatenate((existing_data, new_data), axis=0)
    else:
        merged_data = new_data

    with open(filename, "wb") as f:
        np.save(f, merged_data)