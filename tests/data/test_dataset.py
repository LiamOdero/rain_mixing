import os

import numpy as np
import pytest
from pydub import AudioSegment

from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset, AUGMENT_TYPES
from auto_mixing.data.logging import sample_dBFS
from constants.file_constants import ROOT
from constants.model_constants import AUGMENT_VARIATIONS


def pytest_namespace():
    return {
        'test_input': None
    }


"""
Read audiosegment to be used in creating test datasets
"""


@pytest.fixture(scope="session", autouse=True)
def setup_tests() -> None:
    test_file_path = os.path.join(ROOT, "src", "assets", "rain_sfx.mp3")
    pytest.test_input = AudioSegment.from_file(
        file=test_file_path, format="mp3")

    # run the tests
    yield


"""
Tests that the DBFSSampleDataset initializes all parameters to the expected
size
"""


def test_dBFS_initialization() -> None:
    dBFS_dataset = DBFSSampleDataset([pytest.test_input],
                                     [pytest.test_input])

    assert dBFS_dataset.input_tracks == [pytest.test_input]
    assert len(dBFS_dataset) == 1
    assert dBFS_dataset.output_samples.size(0) == 1

    get_input, get_output = dBFS_dataset[0]

    input_ndarray = get_input.numpy()
    test_samples = sample_dBFS(pytest.test_input)

    assert get_output == pytest.test_input.dBFS

    # some difference in decimals stored
    assert np.allclose(input_ndarray, test_samples)


"""
Tests that the DBFSSampleDataset creates the correct number of augmentations
"""


def test_dBFS_augmentation_count() -> None:
    dBFS_dataset = DBFSSampleDataset([pytest.test_input],
                                     [pytest.test_input])
    dBFS_dataset.augment_data([0])

    # input tracks should be unchanged
    assert dBFS_dataset.input_tracks == [pytest.test_input]

    assert len(dBFS_dataset) == 1 + AUGMENT_VARIATIONS * AUGMENT_TYPES
    assert (dBFS_dataset.output_samples.size(0) == 1 +
            AUGMENT_VARIATIONS * AUGMENT_TYPES)


"""
Tests that the DBFSSampleDataset does nothing when given no indices to augment
"""


def test_dBFS_augmentation_empty() -> None:
    dBFS_dataset = DBFSSampleDataset([pytest.test_input],
                                     [pytest.test_input])
    dBFS_dataset.augment_data([])

    assert len(dBFS_dataset) == 1
    assert dBFS_dataset.output_samples.size(0) == 1


"""
Tests that the DBFSSampleDataset augments volume as expected
"""


def test_dBFS_augmentation_volume() -> None:
    dBFS_dataset = DBFSSampleDataset([pytest.test_input],
                                     [pytest.test_input])
    dBFS_dataset.augment_data([0])

    test_samples = sample_dBFS(pytest.test_input)

    input_volume, output_volume = dBFS_dataset[1]

    difference = (input_volume - test_samples)
    # due to minute differences i cant quite test that all samples are adjusted
    # by an equivalent amount, best i can do is check that they were adjusted
    # at all
    assert not np.allclose(difference, 0)

    # output target should be unchanged
    assert output_volume == pytest.test_input.dBFS


"""
Tests that the DBFSSampleDataset augments silence as expected
"""


def test_dBFS_augmentation_silence() -> None:
    dBFS_dataset = DBFSSampleDataset([pytest.test_input],
                                     [pytest.test_input])
    dBFS_dataset.augment_data([0])

    test_samples = sample_dBFS(pytest.test_input)

    input_volume, output_volume = dBFS_dataset[2]

    # unfortunately the sampled volume != 0, so best i can do is check that
    # its strictly smaller, also no guarantee that itll be -100
    assert input_volume[0] < test_samples[0]

    # output target should be unchanged
    assert output_volume == pytest.test_input.dBFS
