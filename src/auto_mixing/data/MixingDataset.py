from pydub import AudioSegment
from torch.utils.data import Dataset

"""
Interface for different datasets to train mixing models
"""


class MixingDataset(Dataset):

    def __init__(self, _input_tracks: list[AudioSegment],
                 _output_tracks: list[AudioSegment]) -> None:
        super().__init__()

    def augment_data(self, indices: list[int]) -> None:
        pass
