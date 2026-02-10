import os

import pytest
from pydub import AudioSegment

from auto_mixing.data.dataloader import create_sample_dataloaders
from auto_mixing.data.logging import log_edit
from constants.file_constants import ROOT
from constants.model_constants import AUGMENT_VARIATIONS
from tests.utils import verify_testing_setup, TEST_OUTPUT_DIR, \
    TEST_INPUT_DIR
from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset, AUGMENT_TYPES


def pytest_namespace():
    return {
        'test_input': None
    }


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    # Setting up logs
    verify_testing_setup()
    pytest.curr_input_len = len(os.listdir(TEST_INPUT_DIR))
    pytest.curr_output_len = len(os.listdir(TEST_OUTPUT_DIR))

    test_file_path = os.path.join(ROOT, "src", "assets", "rain_sfx.mp3")
    pytest.test_input = AudioSegment.from_file(
        file=test_file_path, format="mp3")


def clear_logs() -> None:
    for file in os.listdir(TEST_INPUT_DIR):
        os.remove(os.path.join(TEST_INPUT_DIR, file))

    for file in os.listdir(TEST_OUTPUT_DIR):
        os.remove(os.path.join(TEST_OUTPUT_DIR, file))


"""
Tests that dataloader initializes as expected in a valid case with
DBFSSampleDataset
"""


def test_init_dataloader_dBFS() -> None:
    for i in range(10):
        log_edit(pytest.test_input, pytest.test_input,
                 TEST_INPUT_DIR, TEST_OUTPUT_DIR)

    train_data, valid_data, test_data = create_sample_dataloaders(
        DBFSSampleDataset, TEST_INPUT_DIR, TEST_OUTPUT_DIR)
    clear_logs()
    assert len(test_data) == 1
    assert len(valid_data) == 2
    assert len(train_data) == 7 + 7 * AUGMENT_VARIATIONS * AUGMENT_TYPES


"""
Tests that dataloader raises FileNotFoundError on empty logging
"""


def test_init_dataloader_empty() -> None:
    try:
        create_sample_dataloaders(DBFSSampleDataset,
                                  TEST_INPUT_DIR, TEST_OUTPUT_DIR)
        # if nothing happens, this is unexpected
        assert False
    except FileNotFoundError:
        assert True


"""
Tests that dataloader raises FileNotFoundError on mismatch file count
"""


def test_init_dataloader_mismatch() -> None:
    for i in range(10):
        log_edit(pytest.test_input, pytest.test_input,
                 TEST_INPUT_DIR, TEST_OUTPUT_DIR)

    new_input_file = os.listdir(TEST_INPUT_DIR)[-1]
    os.remove(os.path.join(TEST_INPUT_DIR, new_input_file))

    try:
        create_sample_dataloaders(DBFSSampleDataset,
                                  TEST_INPUT_DIR, TEST_OUTPUT_DIR)

        clear_logs()
        # if nothing happens, this is unexpected
        assert False
    except FileNotFoundError:
        clear_logs()
        assert True
