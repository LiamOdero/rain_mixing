import os

# TODO: consider splitting some constants into directory specific util files
S_TO_MS = 1000
CHUNK_DIR = "chunk_data"

# TODO: file paths
INPUT_CHUNK_FILE = os.getcwd() + "/chunk_data/input.npy"
OUTPUT_CHUNK_FILE = os.getcwd() + "/chunk_data/output.npy"

SONG_DIR = "tracks"
EXPORT_DIR = "output"
IMAGE_DIR = "cover"

# Confirms that the directory <dir> exists, and if it does not, attempts the create it. Returns true if the
# directory exists at function return time, and false otherwise.
def verify_dir(dir: str):
    if not os.path.isdir(dir):
        try:
            os.makedirs(dir)
            return True
        except OSError:
            return False
    return True
