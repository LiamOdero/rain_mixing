from typing import Any

import torch.nn as nn
from pydub import AudioSegment

"""
Interface for different models that can automatically mix rain into a track
"""


class MixingNN(nn.Module):

    def __init__(self):  # pragma: no cover
        super().__init__()

    def forward(self, x):  # pragma: no cover
        pass

    def mix_track(self,
                  track: AudioSegment) -> AudioSegment:  # pragma: no cover
        pass

    @staticmethod
    def get_accuracy(pred: Any, y: Any):  # pragma: no cover
        pass
