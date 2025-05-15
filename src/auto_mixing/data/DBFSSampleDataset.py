import torch
from torch.utils.data import Dataset


class DBFSSampleDataset(Dataset):
    def __init__(self, input_samples, output_samples):
        self.input_samples = torch.Tensor(input_samples)
        self.output_samples = torch.Tensor(output_samples)

    def __len__(self):
        return len(self.input_samples)

    def __getitem__(self, idx):
        orig = self.input_samples[idx]
        target = self.output_samples[idx]

        return orig, target
