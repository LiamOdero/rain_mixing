import copy
import torch
from pydub import AudioSegment
from torch import nn, Tensor
from auto_mixing.models.MixingNN import MixingNN
from constants.model_constants import RANGE_REDUCTION
from ..data.logging import sample_dBFS

"""
Class for models which used chunked dBFS data in order to mix tracks
"""


class ChunkMixingNN(MixingNN):
    def __init__(self, output_dim: int):
        super().__init__()

        num_filters = 4
        kernel_size = 3
        padding = kernel_size // 2

        self.activation = nn.LeakyReLU

        self.conv_block = nn.Sequential(
            nn.Conv1d(1, num_filters, kernel_size=kernel_size,
                      stride=1, padding=padding, dilation=2),
            nn.BatchNorm1d(num_filters),
            nn.MaxPool1d(kernel_size=2),
            self.activation()
        )

        self.linear_block = nn.Sequential(
            nn.Linear(196, 16),
            nn.BatchNorm1d(16),
            self.activation(),
        )

        self.dropout = nn.Dropout(p=0.7)
        self.output_fc = nn.Linear(16, output_dim)

    """
    Forward pass for this model type

    :param
        -   x: The current set of samples to train on
             shape = [batch_size, CHUNKS]
    :return
        - A tensor containing a float representing a decibel adjustment to make
    """

    def forward(self, x: Tensor) -> Tensor:
        # passing input through layers sequentially
        h_1 = torch.unsqueeze(x, 1)

        h_2 = self.conv_block(h_1)
        h_3 = torch.reshape(h_2, (h_2.size(0), h_2.size(1) * h_2.size(2)))

        h_4 = self.linear_block(h_3)
        h_5 = self.dropout(h_4)

        return self.output_fc(h_5)

    """
    Takes in a track and passes it through the model to determine what decibel
    adjustment to apply to the entire track

    :param
        -   track: Audiosegment of the music to mix
    :return
        -   new_track: A shallow copy of the new mixed track
    """

    def mix_track(self, track: AudioSegment) -> AudioSegment:
        # sampling the dBFS so since that is what the model is trained on
        dBFS_samples = sample_dBFS(track)
        dBFS_samples = torch.tensor(dBFS_samples).float()
        dBFS_samples = dBFS_samples.unsqueeze(0)

        # getting the dB adjustment to apply
        # multiply by RANGE_REDUCTION since model outputs is in reduced space
        target_dBFS = self.forward(dBFS_samples) * RANGE_REDUCTION
        target_diff = (target_dBFS - track.dBFS).mean().item()

        new_track = copy.copy(track)
        new_track += target_diff

        return new_track

    """
    Determines accuracy of a prediction using a ground truth label

    Prediction considered accurate if within 1 decibel of the label

    :param
        -   pred: a list of predictions by the model
        -   y: a list of corresponding ground truths to each prediction
    :return
        -   accs: accuracy in the range [0, 1], contained in a singleton
            tensor
    """

    @staticmethod
    def get_accuracy(pred: Tensor, y: Tensor) -> Tensor:
        # Use RANGE_REDUCTION to determine 1 decibel tolerance value
        accs = torch.isclose(pred,
                             y, atol=(1 / RANGE_REDUCTION))
        accs = accs.float()
        accs = torch.mean(accs)
        return accs
