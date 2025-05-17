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

        num_filters = 16
        kernel_size = 3
        padding = kernel_size // 2

        self.activation = nn.ReLU

        self.linear_block_1 = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            self.activation(),
        )

        self.conv_block_1 = nn.Sequential(
            nn.Conv1d(1, num_filters, kernel_size=kernel_size,
                      stride=1, padding=padding),
            nn.MaxPool1d(kernel_size=2),
            nn.BatchNorm1d(num_filters),
            self.activation()
        )

        self.conv_block_2 = nn.Sequential(
            nn.Conv1d(num_filters, num_filters * 2, kernel_size=kernel_size,
                      stride=1, padding=padding),
            nn.MaxPool1d(kernel_size=2),
            nn.BatchNorm1d(num_filters * 2),
            self.activation()
        )

        self.conv_block_3 = nn.Sequential(
            nn.Conv1d(num_filters * 2, num_filters * 4,
                      kernel_size=kernel_size, stride=1, padding=padding),
            nn.MaxPool1d(kernel_size=2),
            nn.BatchNorm1d(num_filters * 4),
            self.activation()
        )

        self.conv_block_4 = nn.Sequential(
            nn.Conv1d(num_filters * 4, num_filters * 4,
                      kernel_size=kernel_size, stride=1, padding=padding),
            nn.MaxPool1d(kernel_size=2),
            nn.BatchNorm1d(num_filters * 4),
            self.activation()
        )

        self.conv_block_5 = nn.Sequential(
            nn.Conv1d(num_filters * 4, 1, kernel_size=kernel_size,
                      stride=1, padding=padding),
            nn.MaxPool1d(kernel_size=2),
            nn.BatchNorm1d(1),
            self.activation()
        )

        self.linear_block_2 = nn.Sequential(
            nn.Linear(16, 256),
            nn.BatchNorm1d(256),
            self.activation(),
        )

        self.dropout = nn.Dropout(p=0.5)
        self.output_fc = nn.Linear(256, output_dim)

    def forward(self, x):
        # x = [batch_size, CHUNKS]

        h_1 = self.linear_block_1(x)
        h_1 = torch.unsqueeze(h_1, 1)

        h_2 = self.conv_block_1(h_1)

        h_3 = self.conv_block_2(h_2)

        h_4 = self.conv_block_3(h_3)

        h_5 = self.conv_block_4(h_4)

        h_6 = self.conv_block_5(h_5)
        h_6 = torch.reshape(h_6, (h_6.size(0), h_6.size(1) * h_6.size(2)))

        h_7 = self.linear_block_2(h_6)
        h_7 = self.dropout(h_7)

        return self.output_fc(h_7)

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
        accs = torch.isclose(pred,
                             y, atol=0.01)
        accs = accs.float()
        accs = torch.mean(accs)
        return accs
