import os

import pytest

from constants.file_constants import ROOT
from rain_mixing.backend.Directory import Directory

TEST_DIR = os.path.join(ROOT, "tests", "assets")


def pytest_namespace():
    return {
        'root': None,
        'file_dir': None,
        'empty_dir': None,
        'sub_dir': None
    }


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    pytest.root = Directory()

    empty_dir = os.path.join(TEST_DIR, "empty_dir")
    file_dir = os.path.join(TEST_DIR, "file_dir")
    sub_dir = os.path.join(TEST_DIR, "sub_dir")

    pytest.empty_dir = Directory(empty_dir)
    pytest.file_dir = Directory(file_dir)
    pytest.sub_dir = Directory(sub_dir)


"""
Test that initializing a directory without any path makes a "root"
directory
"""


def test_init_root_dir() -> None:
    root = pytest.root

    assert root.path == "root"
    assert root.get_name() == "root"
    assert root.num_files == 0
    assert root.sub_directories == []
    assert root.files == []


"""
Test that the empty directory initializes as expected
"""


def test_init_empty_dir() -> None:
    empty_path = os.path.join(TEST_DIR, "empty_dir")
    assert pytest.empty_dir.path == empty_path

    assert pytest.empty_dir.get_name() == "empty_dir"
    assert pytest.empty_dir.num_files == 0
    assert pytest.empty_dir.sub_directories == []
    assert pytest.empty_dir.files == []


"""
Test that the empty directory initializes as expected
"""


def test_init_file_dir() -> None:
    file_path = os.path.join(TEST_DIR, "file_dir")
    assert pytest.file_dir.path == file_path

    assert pytest.file_dir.get_name() == "file_dir"
    assert pytest.file_dir.num_files == 2
    assert pytest.file_dir.sub_directories == []

    assert pytest.file_dir.files[0].name == "output_0"
    assert pytest.file_dir.files[1].name == "output_1"


"""
Test that the empty directory initializes as expected
"""


def test_init_sub_dir() -> None:
    sub_path = os.path.join(TEST_DIR, "sub_dir")
    assert pytest.sub_dir.path == sub_path

    assert pytest.sub_dir.get_name() == "sub_dir"
    assert pytest.sub_dir.num_files == 3

    assert pytest.sub_dir.files[0].name == "output_0"

    assert len(pytest.sub_dir.sub_directories) == 1

    sub_sub_path = os.path.join(sub_path, "file_sub")
    sub_sub_dir = pytest.sub_dir.sub_directories[0]
    assert sub_sub_dir.num_files == 1
    assert sub_sub_dir.files[0].name == "output_1"
    assert sub_sub_dir.path == sub_sub_path
    assert sub_sub_dir.get_name() == "file_sub"


"""
Tests that searching with no matches return None
"""


def test_search_negative() -> None:
    result = pytest.file_dir.search("whbwjidanbw")
    assert result is None


"""
Tests that searching with a match on a directory name returns the whole
directory
"""


def test_search_match_dir() -> None:
    result = pytest.file_dir.search("file_dir")
    assert result.num_files == 2


"""
Tests that searching with a match on a one file returns only that file
"""


def test_search_one_file() -> None:
    result = pytest.file_dir.search("output_0")
    assert result.num_files == 1


"""
Tests searching with a deep recursive result
"""


def test_search_recursive() -> None:
    result = pytest.sub_dir.search("output_1")
    assert result.num_files == 2
    assert len(result.files) == 0


"""
Tests that sub directories with no matches are not included in the final result
"""


def test_search_discard() -> None:
    result = pytest.sub_dir.search("output_0")
    assert result.num_files == 1
    assert len(result.sub_directories) == 0


"""
Tests that the empty directory has an expected dict output
"""


def test_empty_dict() -> None:
    result = pytest.empty_dir.get_dict()
    assert result == [{"name": "empty_dir", "children": []}]


"""
Tests that the file directory has an expected dict output
"""


def test_file_dict() -> None:
    result = pytest.file_dir.get_dict()
    assert result == [{"name": "file_dir",
                       "children": ["output_0", "output_1"]}]


"""
Tests that the sub directory has an expected dict output
"""


def test_sub_dict() -> None:
    result = pytest.sub_dir.get_dict()
    assert result == [{"name": "sub_dir",
                       "children": ["output_0",
                                    {"name": "file_sub",
                                     "children": ["output_1"]}]}]


"""
Tests that the empty directory returns no files
"""


def test_get_files_empty() -> None:
    result = pytest.empty_dir.get_files()
    assert result == []


"""
Tests that the files directory returns 2 files
"""


def test_get_files_flat() -> None:
    result = pytest.file_dir.get_files()
    assert len(result) == 2

    assert result[0].name == "output_0"
    assert result[1].name == "output_1"


"""
Tests that the sub directory returns 2 files
"""


def test_get_files_sub() -> None:
    result = pytest.sub_dir.get_files()
    assert len(result) == 2

    assert result[0].name == "output_0"
    assert result[1].name == "output_1"


"""
Tests adding files to a directory
"""


def test_add_files() -> None:
    test_file_1 = pytest.file_dir.files[0]
    test_file_2 = pytest.file_dir.files[1]

    new_dir = Directory()

    new_dir.add_file(test_file_1)

    assert new_dir.num_files == 1
    assert new_dir.files[0] == test_file_1

    new_dir.add_file(test_file_2)

    assert new_dir.num_files == 2
    assert new_dir.files[1] == test_file_2


"""
Tests adding a directory to a directory
"""


def test_add_dir() -> None:
    new_sub_dir = pytest.file_dir
    new_dir = Directory()

    new_dir.add_folder(new_sub_dir)
    assert new_dir.num_files == 3
    assert len(new_dir.files) == 0
    assert len(new_dir.sub_directories) == 1
    assert new_dir.sub_directories[0] == new_sub_dir
