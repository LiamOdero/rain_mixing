import os

import numpy as np
import pytest
from auto_mixing.data.logging import (log_edit, read_logging_data, sample_dBFS,
                                      sample_logs)
from constants.file_constants import (LOGGING_EXTENSION, ROOT,
                                      INPUT_DATA_DIR, OUTPUT_DATA_DIR)
from constants.model_constants import CHUNKS
from rain_mixing.utils.utils import verify_logging_setup
from pydub import AudioSegment


def pytest_namespace():
    return {'curr_input_len ': 0,
            'curr_output_len ': 0,
            'new_input_len ': 0,
            'new_output_len ': 0,
            'input_array': None,
            'output_array': None
            }


"""
Performs pre-test setup and post-test cleanup
Note: This test suite effectively does most of the work in this function,
and the tests are just comparing values. The reason for this is that the
logging module mostly does file reads/writes, so doing repeated calls will be
slow
"""


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    # Setting up logs
    verify_logging_setup()
    pytest.curr_input_len = len(os.listdir(INPUT_DATA_DIR))
    pytest.curr_output_len = len(os.listdir(OUTPUT_DATA_DIR))

    test_file_path = os.path.join(ROOT, "src", "assets", "rain_sfx.mp3")
    test_input = AudioSegment.from_file(
        file=test_file_path, format="mp3")
    test_output = test_input + 5
    log_edit(test_input, test_output)

    pytest.new_input_len = len(os.listdir(INPUT_DATA_DIR))
    pytest.new_output_len = len(os.listdir(OUTPUT_DATA_DIR))

    # Setting up re-read audio segments
    pytest.input_array, pytest.output_array = read_logging_data()

    # run the tests
    yield

    new_input_file = os.listdir(INPUT_DATA_DIR)[-1]
    os.remove(os.path.join(INPUT_DATA_DIR, new_input_file))

    new_output_file = os.listdir(OUTPUT_DATA_DIR)[-1]
    os.remove(os.path.join(OUTPUT_DATA_DIR, new_output_file))


"""
Tests that log_edit() successfully outputs two mp3 files to input_data
and output_data folders under /src/logging
"""


def test_log_edit_file_output() -> None:
    # Getting the new number of files in the input and output folder
    assert pytest.new_input_len == pytest.curr_input_len + 1
    assert pytest.new_output_len == pytest.curr_output_len + 1


"""
Tests that the output mp3s by log_edit have the desired naming convention
"""


def test_log_edit_file_names() -> None:
    assert (f"input_{pytest.new_input_len - 1}.{LOGGING_EXTENSION}" in
            os.listdir(INPUT_DATA_DIR))

    assert (f"output_{pytest.new_output_len - 1}.{LOGGING_EXTENSION}" in
            os.listdir(OUTPUT_DATA_DIR))


"""
Tests that log_edit() outputted two separate files to the corresponding folders
"""


def test_log_edit_file_different() -> None:
    input_array, output_array = read_logging_data()

    # there is some loss in audio data when writing to wav, so an error of
    # <=+- 0. 1 is expected
    assert input_array[-1].dBFS == pytest.approx(
        output_array[-1].dBFS - 5, 0.1)


"""
Tests that read_logs correctly returns two separate arrays
"""


def test_read_logs_array_check() -> None:
    assert len(pytest.input_array) == pytest.new_input_len
    assert len(pytest.output_array) == pytest.new_output_len
    assert pytest.input_array[-1] != pytest.output_array[-1]


"""
Tests that sample_dBFS returns an ndarray with the correct chunk count
"""


def test_sample_dBFS_chunks() -> None:
    input_chunks = sample_dBFS(pytest.input_array[0])
    assert input_chunks.shape[-1] == CHUNKS


"""
Tests that sample_logs returns chunked the correct number of tracks
"""


def test_sample_logs_tracks() -> None:
    input_chunks, output_chunks = sample_logs(pytest.input_array,
                                              pytest.output_array)
    assert input_chunks.shape[0] == pytest.new_input_len
    assert output_chunks.shape[0] == pytest.new_output_len


"""
Tests that sample_logs returns two different arrays
"""


def test_sample_logs_different() -> None:
    input_chunks, output_chunks = sample_logs(pytest.input_array,
                                              pytest.output_array)

    assert not np.array_equal(input_chunks, output_chunks)
