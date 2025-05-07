import os

import pytest
from rain_mixing.data.logging import (log_edit, read_logging_data,
                                      chunk_dbfs, CHUNKS)
from rain_mixing.utils.utils import verify_logging_setup
from pydub import AudioSegment

SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        '..', '..', "src"))
INPUT_DIR = os.path.join(SRC_ROOT, "logging", "input_data")
OUTPUT_DIR = os.path.join(SRC_ROOT, "logging", "output_data")


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
    pytest.curr_input_len = len(os.listdir(INPUT_DIR))
    pytest.curr_output_len = len(os.listdir(OUTPUT_DIR))

    test_file_path = os.path.join(os.path.dirname(__file__), "rain_sfx.mp3")
    test_input = AudioSegment.from_file(
        file=test_file_path, format="mp3")
    test_output = test_input + 5
    log_edit(test_input, test_output)

    pytest.new_input_len = len(os.listdir(INPUT_DIR))
    pytest.new_output_len = len(os.listdir(OUTPUT_DIR))

    # Setting up re-read audio segments
    pytest.input_array, pytest.output_array = read_logging_data()

    # run the tests
    yield

    new_input_file = os.listdir(INPUT_DIR)[-1]
    os.remove(os.path.join(INPUT_DIR, new_input_file))

    new_output_file = os.listdir(OUTPUT_DIR)[-1]
    os.remove(os.path.join(OUTPUT_DIR, new_output_file))


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

    assert (os.listdir(INPUT_DIR)[-1] ==
            f"input_{pytest.new_input_len - 1}.mp3")

    assert (os.listdir(OUTPUT_DIR)[-1] ==
            f"output_{pytest.new_output_len - 1}.mp3")


"""
Tests that log_edit() outputted two separate files to the corresponding folders
"""


def test_log_edit_file_different() -> None:
    input_array, output_array = read_logging_data()

    # there is some loss in audio data when writing to mp3, so an error of
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
Tests that chunk_dbfs returns chunked the correct number of tracks
"""


def test_chunk_dbfs_tracks() -> None:
    input_chunks, output_chunks = chunk_dbfs(pytest.input_array,
                                             pytest.output_array)
    assert input_chunks.shape[0] == pytest.new_input_len
    assert output_chunks.shape[0] == pytest.new_output_len


"""
Tests that chunk_dbfs returns two arrays with the correct chunk count
"""


def test_chunk_dbfs_chunks() -> None:
    input_chunks, output_chunks = chunk_dbfs(pytest.input_array,
                                             pytest.output_array)
    assert input_chunks.shape[-1] == CHUNKS
    assert output_chunks.shape[-1] == CHUNKS


"""
Tests that chunk_dbfs returns two different arrays
"""


def test_chunk_dbfs_different() -> None:
    input_chunks, output_chunks = chunk_dbfs(pytest.input_array,
                                             pytest.output_array)

    assert (input_chunks != output_chunks).all()
