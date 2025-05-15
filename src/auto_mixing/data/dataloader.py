import torch.utils.data as data
from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset
from rain_mixing.data.logging import read_logging_data, sample_logs
from constants.model_constants import TRAIN_RATIO, VALID_RATIO, TEST_RATIO

"""
Creates a training, validation, and testing dataset using dBFS samples
from logged data
"""


def create_sample_dbfs_dataloaders():
    input_tracks, output_tracks = read_logging_data()
    input_samples, output_samples = sample_logs(input_tracks, output_tracks)

    dataset = DBFSSampleDataset(input_samples, output_samples)

    train_data, valid_data, test_data = data.random_split(dataset,
                                                          [TRAIN_RATIO,
                                                           VALID_RATIO,
                                                           TEST_RATIO])
    return train_data, valid_data, test_data
