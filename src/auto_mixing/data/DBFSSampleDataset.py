import copy
from random import random
import numpy as np
import torch
from pydub import AudioSegment
from torch import Tensor
from tqdm import tqdm

from auto_mixing.data.MixingDataset import MixingDataset
from auto_mixing.data.logging import sample_dBFS
from constants.model_constants import AUGMENT_VARIATIONS

AUGMENT_TYPES = 2

"""
Dataset class wrapper for use with dBFS sample-based models

:attributes
    - input_samples: The inputs to the network. Shape [samples, CHUNKS]
    - output_sample: The target outputs of the network. Shape [samples, 1]
"""


class DBFSSampleDataset(MixingDataset):
    def __init__(self, input_tracks: list[AudioSegment],
                 output_tracks: list[AudioSegment]) -> None:
        # Taking dBFS samples from chunks for the input
        super().__init__(input_tracks, output_tracks)
        input_samples = np.array([sample_dBFS(input_track) for input_track in
                                  input_tracks])

        # Targets are the dBFS of the finalized track
        output_samples = np.array([output_track.dBFS for output_track in
                                   output_tracks])
        output_samples = np.reshape(output_samples,
                                    (output_samples.shape[0], 1))

        self.input_tracks = input_tracks
        self.input_samples = torch.Tensor(input_samples)
        self.output_samples = torch.Tensor(output_samples)

    def __len__(self) -> int:
        return len(self.input_samples)

    """
    Retrieves a specified input-output pair from the dataloader
    """

    def __getitem__(self, idx) -> tuple[Tensor, Tensor]:
        orig = self.input_samples[idx]
        target = self.output_samples[idx]

        return orig, target

    """
    Adds augmentations of samples in <self.input_samples> and
    <self.output_samples> with flat increases or decreases to volume according
    to the samples listed in <indices>

    :param
        - indices: Indicates which samples to augment
    """

    def augment_data(self, indices: list[int]) -> None:
        # Tensors to hold augmented samples
        new_input_samples = torch.empty(((AUGMENT_VARIATIONS * AUGMENT_TYPES)
                                         * len(indices),
                                         self.input_samples.size(1)))

        new_output_samples = torch.empty(((AUGMENT_VARIATIONS * AUGMENT_TYPES)
                                          * len(indices),
                                          self.output_samples.size(1)))

        # iterating through each input output pair
        print("Augmenting Data:")
        augment_count = 0
        for i in tqdm(range(len(indices))):
            in_track = self.input_tracks[indices[i]]
            out_track = self.output_samples[indices[i]]

            # Creating AUGMENT_VARIATIONS versions of the input output pair

            for j in range(AUGMENT_VARIATIONS):
                for a in range(AUGMENT_TYPES):
                    new_audio = copy.copy(in_track)
                    if a == 0:
                        # adjust dB in the range [-15, 15] for the entire track
                        new_audio += random() * 30 - 15
                    elif a == 1:
                        # add up to 10 seconds of silence at the start
                        silence_dur = random() * 10
                        silent_audio = AudioSegment.silent(silence_dur * 1000)
                        new_audio = silent_audio.append(new_audio, crossfade=0)

                    # sampling dBFS to add to dataset
                    new_track = sample_dBFS(new_audio)
                    new_input_samples[augment_count] = torch.Tensor(new_track)

                    # output target should still be the same
                    new_output_samples[augment_count] = out_track
                    indices.append(self.input_samples.size(0) + augment_count)
                    augment_count += 1

        # adding samples to the dataset
        self.input_samples = torch.cat((self.input_samples,
                                        new_input_samples), dim=0)
        self.output_samples = torch.cat((self.output_samples,
                                         new_output_samples), dim=0)
