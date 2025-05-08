from torch.utils.data import Dataset


class DBFSSampleDataset(Dataset):
    def __init__(self, input_samples, output_samples,
                 transform=None, target_transform=None):
        self.input_samples = input_samples
        self.output_samples = output_samples
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.input_samples)

    def __getitem__(self, idx):
        orig = self.input_samples[self]
        target = self.output_samples[self]

        if self.transform:
            orig = self.transform(orig)
        if self.target_transform:
            target = self.target_transform(target)

        return orig, target
