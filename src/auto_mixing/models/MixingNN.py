import torch.nn as nn
from pydub import AudioSegment


"""
Interface for different models that can automatically mix rain into a track
"""


class MixingNN(nn.Module):

    def __init__(self):
        super().__init__()

    def forward(self, x):
        pass

    def mix_track(self, track: AudioSegment) -> AudioSegment:
        pass

    @staticmethod
    def get_accuracy(pred, y):
        pass
