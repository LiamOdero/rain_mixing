from random import randint
import torch
from torch import Tensor
from torch.utils.data import Dataset
from constants.model_constants import AUGMENT_VARIATIONS


"""
Dataset class wrapper for use with dBFS sample-based models

:attributes
    - input_samples: The inputs to the network. Shape [samples, CHUNKS]
    - output_sample: The target outputs of the network. Shape [samples, 1]
"""


class DBFSSampleDataset(Dataset):
    def __init__(self, input_samples, output_samples) -> None:
        self.input_samples = torch.Tensor(input_samples)
        self.output_samples = torch.Tensor(output_samples)

    def __len__(self) -> int:
        return len(self.input_samples)

    """
    Retrieves an input-output pair from the dataloader
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
        new_input_samples = torch.empty((AUGMENT_VARIATIONS * len(indices),
                                         self.input_samples.size(1)))
        new_output_samples = torch.empty((AUGMENT_VARIATIONS * len(indices),
                                         self.output_samples.size(1)))

        # iterating through each input output pair
        print("Augmenting Data:")
        for i in range(len(indices)):
            in_track = self.input_samples[indices[i]]
            out_track = self.output_samples[indices[i]]

            # Creating AUGMENT_VARIATIONS versions of the input output pair
            for j in range(AUGMENT_VARIATIONS):
                augment_count = i * AUGMENT_VARIATIONS + j
                new_track = in_track.clone().detach()
                new_track += randint(-5, 5)

                new_input_samples[augment_count] = new_track

                # output target should still be the same
                new_output_samples[augment_count] = out_track

                indices.append(self.input_samples.size(0) + augment_count)

        self.input_samples = torch.cat((self.input_samples,
                                        new_input_samples), dim=0)
        self.output_samples = torch.cat((self.output_samples,
                                        new_output_samples), dim=0)
