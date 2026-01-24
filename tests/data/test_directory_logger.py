import os

import pytest

from rain_mixing.backend.Directory import Directory
from rain_mixing.data.DirectoryLogger import DirectoryLogger
from tests.utils import TEST_DIRECTORY_DIR, TEST_DIR


def pytest_namespace():
    return {'directory_logger': None,
            'loaded_dir': None
            }


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    pytest.directory_logger = DirectoryLogger(TEST_DIRECTORY_DIR)

    empty_dir = os.path.join(TEST_DIR, "empty_dir")
    file_dir = os.path.join(TEST_DIR, "file_dir")
    sub_dir = os.path.join(TEST_DIR, "sub_dir")

    root = Directory()
    root.add_folder(empty_dir)
    root.add_folder(file_dir)
    root.add_folder(sub_dir)

    pytest.directory_logger.log_dirs(root)
    pytest.loaded_dir = pytest.directory_logger.load_dirs()

    yield

    os.remove(os.path.join(TEST_DIRECTORY_DIR, "data.txt"))


"""
Tests that saving and loading an empty directory works
"""


def test_load_empty() -> None:
    empty_path = os.path.join(TEST_DIR, "empty_dir")

    empty_dir = pytest.loaded_dir.sub_directories[0]
    assert empty_dir.path == empty_path

    assert empty_dir.get_name() == "empty_dir"
    assert empty_dir.num_files == 0
    assert empty_dir.sub_directories == []
    assert empty_dir.files == []


"""
Tests that saving and loading a flat directory with files works
"""


def test_load_files() -> None:
    file_path = os.path.join(TEST_DIR, "file_dir")

    file_dir = pytest.loaded_dir.sub_directories[1]
    assert file_dir.path == file_path

    assert file_dir.get_name() == "file_dir"
    assert file_dir.num_files == 2
    assert file_dir.sub_directories == []

    assert file_dir.files[0].name == "output_0"
    assert file_dir.files[1].name == "output_1"


"""
Tests that saving and loading a directory with sub directories and files works
"""


def test_init_sub_dir() -> None:
    sub_path = os.path.join(TEST_DIR, "sub_dir")
    sub_dir = pytest.loaded_dir.sub_directories[2]

    assert sub_dir.path == sub_path

    assert sub_dir.get_name() == "sub_dir"
    assert sub_dir.num_files == 3

    assert sub_dir.files[0].name == "output_0"

    assert len(sub_dir.sub_directories) == 1

    sub_sub_path = os.path.join(sub_path, "file_sub")
    sub_sub_dir = sub_dir.sub_directories[0]
    assert sub_sub_dir.num_files == 1
    assert sub_sub_dir.files[0].name == "output_1"
    assert sub_sub_dir.path == sub_sub_path
    assert sub_sub_dir.get_name() == "file_sub"
