from typing import Any, Type
import torch
import torch.utils.data as data
from auto_mixing.data.MixingDataset import MixingDataset
from auto_mixing.data.logging import read_logging_data
from constants.model_constants import TRAIN_RATIO, VALID_RATIO, TEST_RATIO

"""
Creates a training, validation, and testing dataset using dBFS samples
from logged data

:param
    - data_class: The type of MixingDataset to create
:return
    - train_data: Dataloader for training samples
    - valid_data: Dataloader for validation samples
    - test_data: Dataloader for testing samples
:raise
    - FileNotFoundError: When any mismatch between input and output logs are
    found
"""


def create_sample_dataloaders(data_class: Type[MixingDataset]) \
        -> tuple[Any, Any, Any]:
    input_tracks, output_tracks = read_logging_data()

    # Initializing the dataloaders to use in the training loop
    if (input_tracks and output_tracks and
            len(input_tracks) == len(output_tracks)):
        dataset = data_class(input_tracks, output_tracks)

        generator = torch.Generator()
        generator.manual_seed(0)

        (train_data,
         valid_data,
         test_data) = data.random_split(dataset=dataset,
                                        lengths=[TRAIN_RATIO,
                                                 VALID_RATIO,
                                                 TEST_RATIO],
                                        generator=generator)

        # Creating augmented training samples to help with generalization
        train_data.dataset.augment_data(train_data.indices)
        return train_data, valid_data, test_data
    else:
        raise FileNotFoundError
