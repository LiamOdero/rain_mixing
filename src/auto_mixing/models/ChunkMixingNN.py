import torch
from pydub import AudioSegment
from torch import nn
import torch.nn.functional as F
from auto_mixing.models.MixingNN import MixingNN

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
        # b = [batch_size, CHUNKS]

        h_1 = F.relu(self.input_fc(b))
        # h_1 = [batch_size, 128]

        h_2 = F.relu(self.hidden_fc(h_1))
        # h_2 = [128, 128]

        return self.output_fc(h_2)

    @classmethod
    def mix_track(cls, track: AudioSegment) -> AudioSegment:
        pass

    @staticmethod
    def get_accuracy(pred, y):
        accs = torch.isclose(pred, y, atol=0.1)
        accs = accs.float()
        return torch.mean(accs)
