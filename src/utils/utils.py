import os

# TODO: consider splitting some constants into directory specific util files
S_TO_MS = 1000
CHUNK_DIR = "chunk_data"

# TODO: file paths
INPUT_CHUNK_FILE = os.getcwd() + "/chunk_data/input.npy"
OUTPUT_CHUNK_FILE = os.getcwd() + "/chunk_data/output.npy"

SONG_DIR = os.getcwd() + "/tracks"
EXPORT_DIR = os.getcwd() + "/output"
IMAGE_DIR = os.getcwd() + "/cover"

"""
Confirms that the directory <dir> exists, and if it does not, attempts the create it

:param
    -   directory: The absolute directory to check the existence of
:exception
    - OSError: Directory does not exist and was failed to be created
"""
def verify_dir(directory: str):
    abs_dir = os.getcwd() + directory
    if not os.path.isdir(abs_dir):
        try:
            os.makedirs(abs_dir)
            return True
        except OSError:
            raise Exception(f"{abs_dir} Directory verification failed")


"""
Verifies that all required directories exist
"""
def verify_setup():
    verify_dir(SONG_DIR)
    verify_dir(EXPORT_DIR)
    verify_dir(IMAGE_DIR)
