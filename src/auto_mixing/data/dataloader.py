from typing import Any

import numpy as np
import torch.utils.data as data

from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset
from auto_mixing.data.logging import read_logging_data, sample_dBFS
from constants.model_constants import TRAIN_RATIO, VALID_RATIO, TEST_RATIO

"""
Creates a training, validation, and testing dataset using dBFS samples
from logged data

:return
    - train_data: Dataloader for training samples
    - valid_data: Dataloader for validation samples
    - test_data: Dataloader for testing samples
"""


def create_sample_dBFS_dataloaders() -> tuple[Any, Any, Any]:
    input_tracks, output_tracks = read_logging_data()

    # Taking dBFS samples from chunks for the input
    input_samples = np.array([sample_dBFS(input_track) for input_track in
                              input_tracks])

    # For the basic model, the targets are the dBFS of the finalized track
    output_samples = np.array([output_track.dBFS for output_track in
                               output_tracks])
    output_samples = np.reshape(output_samples,
                                (output_samples.shape[0], 1))

    # Initializing the dataloaders to use in the training loop
    dataset = DBFSSampleDataset(input_samples, output_samples)
    train_data, valid_data, test_data = data.random_split(dataset,
                                                          [TRAIN_RATIO,
                                                           VALID_RATIO,
                                                           TEST_RATIO])

    # Creating augmented training samples to help with generalization
    train_data.dataset.augment_data(train_data.indices)
    return train_data, valid_data, test_data
