import torch.nn as nn
from pydub import AudioSegment


"""
Interface for different models that can automatically mix rain into a track
"""


class MixingNN(nn.Module):
    def __init__(self):
        super().__init__()

    @classmethod
    def forward(cls, x):
        pass

    @classmethod
    def mix_track(cls, track: AudioSegment) -> AudioSegment:
        pass

    @staticmethod
    def get_accuracy(pred, y):
        pass
