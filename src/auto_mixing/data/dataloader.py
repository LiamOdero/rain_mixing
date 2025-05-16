import copy
from random import randint
import torch.utils.data as data
from pydub import AudioSegment
from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset
from auto_mixing.data.logging import read_logging_data, sample_logs
from constants.model_constants import TRAIN_RATIO, VALID_RATIO, TEST_RATIO, \
    AUGMENT_VARIATIONS

"""
Creates versions of tracks in <input_tracks> with minor adjustments
but with the same output target to increase the number of data samples
the model can be trained on
"""


def augment_data(input_tracks: list[AudioSegment],
                 output_tracks: list[AudioSegment]):
    new_input_tracks = []
    new_output_tracks = []

    # iterating through each input output pair
    for in_track, out_track in zip(input_tracks, output_tracks):
        new_input_tracks.append(in_track)
        new_output_tracks.append(out_track)

        # Creating AUGMENT_VARIATIONS versions of the input output pair
        for i in range(AUGMENT_VARIATIONS):
            new_track = copy.copy(in_track)
            new_track += randint(1, 20)

            new_input_tracks.append(new_track)
            new_output_tracks.append(out_track)

    return new_input_tracks, new_output_tracks


"""
Creates a training, validation, and testing dataset using dBFS samples
from logged data
"""


def create_sample_dbfs_dataloaders():
    input_tracks, output_tracks = read_logging_data()
    input_tracks, output_tracks = augment_data(input_tracks, output_tracks)
    input_samples, output_samples = sample_logs(input_tracks, output_tracks)

    dataset = DBFSSampleDataset(input_samples, output_samples)

    train_data, valid_data, test_data = data.random_split(dataset,
                                                          [TRAIN_RATIO,
                                                           VALID_RATIO,
                                                           TEST_RATIO])
    return train_data, valid_data, test_data
