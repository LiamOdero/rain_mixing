import os

import pytest
from pydub import AudioSegment

from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset
from auto_mixing.models.ChunkMixingNN import ChunkMixingNN
from constants.file_constants import ROOT
from constants.model_constants import RANGE_REDUCTION
from rain_mixing.utils.utils import verify_logging_setup
from torch import Tensor


def pytest_namespace():
    return {
        'test_audio': None,
        'dataloader': None
    }


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    # Setting up logs
    verify_logging_setup()

    test_file_path = os.path.join(ROOT, "src", "assets", "rain_sfx.mp3")
    pytest.test_audio = AudioSegment.from_file(
        file=test_file_path, format="mp3")
    pytest.dataloader = DBFSSampleDataset([pytest.test_audio],
                                          [pytest.test_audio])


"""
Tests the initialization of a ChunkMixingNN
"""


def test_init_chunkNN() -> None:
    ChunkMixingNN(1)
    assert True


"""
Tests the forward pass of a ChunkMixingNN
"""


def test_forward_chunkNN() -> None:
    model = ChunkMixingNN(1)
    model.eval()

    for x, y in pytest.dataloader:
        x = x.unsqueeze(0)
        model.forward(x)
    assert True


"""
Tests the mixing of a ChunkNN
"""


def test_mix_chunkNN() -> None:
    model = ChunkMixingNN(1)
    model.eval()
    new_track = model.mix_track(pytest.test_audio)
    assert new_track.dBFS != pytest.test_audio.dBFS


"""
Tests for calculating accuracy under ChunkMixingNN
"""


def test_accuracy_match_chunkNN() -> None:
    model = ChunkMixingNN(1)
    acc = model.get_accuracy(Tensor([1]), Tensor([1]))
    assert acc.item() == 1


def test_accuracy_fail_chunkNN() -> None:
    model = ChunkMixingNN(1)
    acc = model.get_accuracy(Tensor([0]), Tensor([1]))
    assert acc.item() == 0


def test_accuracy_tolerance_chunkNN() -> None:
    model = ChunkMixingNN(1)
    acc = model.get_accuracy(Tensor([1 - (1 / RANGE_REDUCTION)]), Tensor([1]))
    assert acc.item() == 1


def test_accuracy_multiple_chunkNN() -> None:
    model = ChunkMixingNN(1)
    acc = model.get_accuracy(Tensor([0, 1]), Tensor([1, 1]))
    assert acc.item() == 0.5
