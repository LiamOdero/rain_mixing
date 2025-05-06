import os

S_TO_MS = 1000

SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DATA_DIR = os.path.join(SRC_ROOT, "logging", "input_data")
OUTPUT_DATA_DIR = os.path.join(SRC_ROOT, "logging", "output_data")

SONG_DIR = os.path.join(SRC_ROOT, "tracks")
EXPORT_DIR = os.path.join(SRC_ROOT, "output")
IMAGE_DIR = os.path.join(SRC_ROOT, "cover")

"""
Confirms that the directory <dir> exists, and if it does not,
attempts to create it

:param
    -   directory: The absolute directory to check the existence of
:exception
    - OSError: Directory does not exist and was failed to be created
"""


def verify_dir(directory: str):
    abs_dir = directory
    if not os.path.isdir(abs_dir):
        try:
            os.makedirs(abs_dir)
            return True
        except OSError:
            raise Exception(f"{abs_dir} Directory verification failed")


"""
A wrapper for os.path.isfile that accounts for directory

:param
    -   dir: The directory of the file to verify
    -   filename: The name of the file to verify

:return
    Whether or not the desired file exists in the specified directory
"""


def wrapped_is_file(directory, filename):
    abs_file = os.path.join(directory, filename)
    return os.path.isfile(abs_file)


"""
Verifies that all required directories exist
"""


def verify_setup():
    verify_dir(SONG_DIR)
    verify_dir(EXPORT_DIR)
    verify_dir(IMAGE_DIR)


"""
Verifies that all required directories for logging exist
"""


def verify_logging_setup():
    verify_dir(INPUT_DATA_DIR)
    verify_dir(OUTPUT_DATA_DIR)
