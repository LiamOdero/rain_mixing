import numpy as np
import torch
from pydub import AudioSegment
from torch import nn
import torch.nn.functional as F
from auto_mixing.models.MixingNN import MixingNN
from rain_mixing.data.logging import sample_dBFS

EPSILON = 1e-09

"""
Class for models which used chunked dBFS data in order to mix tracks
"""


class ChunkMixingNN(MixingNN):
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()

        self.input_BN = nn.BatchNorm1d(input_dim)
        self.input_fc = nn.Linear(input_dim, 128)

        self.hidden_fc = nn.Linear(128, 100)
        self.output_fc = nn.Linear(100, output_dim)

    def forward(self, x):
        # x = [batch_size, CHUNKS]

        b = self.input_BN(x)

        h_1 = F.relu(self.input_fc(b))
        # h_1 = [batch_size, 128]

        h_2 = F.relu(self.hidden_fc(h_1))
        # h_2 = [128, 128]

        return self.output_fc(h_2)

    @classmethod
    def mix_track(cls, track: AudioSegment) -> AudioSegment:
        track_dBFS_samples = sample_dBFS(track)

        # Reshaping for use in the forward pass
        track_dBFS_samples = torch.tensor(track_dBFS_samples)
        track_dBFS_samples = torch.unsqueeze(track_dBFS_samples, 0)

        new_dBFS = None  # to be used in forward pass

        # TODO: Expand new_dbfs and add to track

        return track

    @staticmethod
    def get_accuracy(pred, y):
        accs = torch.isclose(pred, y, atol=0.1)
        accs = accs.float()
        return torch.mean(accs)
