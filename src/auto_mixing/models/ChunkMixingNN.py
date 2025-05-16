import copy
import numpy as np
import torch
from pydub import AudioSegment
from torch import nn
from auto_mixing.models.MixingNN import MixingNN
from constants.audio_constants import S_TO_MS
from constants.file_constants import CHUNKS
from ..data.logging import sample_dBFS

"""
Class for models which used chunked dBFS data in order to mix tracks
"""


class ChunkMixingNN(MixingNN):
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()

        self.hidden_layers = nn.Sequential(
            nn.BatchNorm1d(input_dim),

            nn.Linear(input_dim, 512),
            nn.ReLU(),

            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(p=0.5)
        )

        self.output_fc = nn.Linear(256, output_dim)

    def forward(self, x):
        # x = [batch_size, CHUNKS]

        h = self.hidden_layers(x)

        return self.output_fc(h)

    def mix_track(self, track: AudioSegment) -> AudioSegment:
        dBFS_samples = sample_dBFS(track)
        dBFS_samples = torch.tensor(dBFS_samples)

        target_dBFS = self.forward(dBFS_samples)
        target_diff = target_dBFS - dBFS_samples

        length = track.duration_seconds * S_TO_MS
        chunk_length = np.floor(length / CHUNKS)

        new_track = copy.copy(track)
        for i in range(new_track.frame_count()):
            target_dBFS = target_diff[i % chunk_length]
            new_track[i] += target_dBFS

        return new_track

    @staticmethod
    def get_accuracy(pred, y):
        accs = torch.isclose(pred, y, atol=0.1)
        accs = accs.float()
        return torch.mean(accs)
