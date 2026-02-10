import os.path
from constants.file_constants import ROOT, MODEL_DIR
from rain_mixing.utils.utils import verify_dir

TEST_INPUT_DIR = os.path.join(ROOT, "tests", "logging", "input_data")
TEST_OUTPUT_DIR = os.path.join(ROOT, "tests", "logging", "output_data")
TEST_DIR = os.path.join(ROOT, "tests", "assets")
TEST_DIRECTORY_DIR = os.path.join(ROOT, "tests", "logging", "directories")

"""
Verifies that all required directories for testing exist
"""


def verify_testing_setup() -> None:
    verify_dir(TEST_INPUT_DIR)
    verify_dir(TEST_OUTPUT_DIR)

    # no more than 1 model is tested at a time, so it should be fine to leave
    # testing models in the main model directory as long as they are deleted
    verify_dir(MODEL_DIR)
