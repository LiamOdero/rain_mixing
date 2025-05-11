import numpy as np
import torch
from torch import nn, optim
from torch.nn import MSELoss
from torch.optim import Optimizer
from torch.utils import data
from torch.utils.data import DataLoader
from tqdm import trange, tqdm
from rain_mixing.data.logging import CHUNKS
from auto_mixing.data.dataloader import create_sample_dbfs_dataloaders
from auto_mixing.models.ChunkMixingNN import ChunkMixingNN
from auto_mixing.models.MixingNN import MixingNN

LR = 0.01
EPOCHS = 10
BATCH_SIZE = 32
RANGE_REDUCTION = 100


def train_loop(model: MixingNN, dataloader: DataLoader, optimizer: Optimizer,
               criterion: MSELoss, device: str):
    epoch_loss = 0
    epoch_acc = 0

    model.train()

    for (x, y) in dataloader:
        x = x.to(device)
        y = y.to(device)

        y = y / RANGE_REDUCTION

        optimizer.zero_grad()

        pred = model(x)
        loss = criterion(pred, y)

        acc = model.get_accuracy(pred, y)

        loss.backward()
        optimizer.step()

        epoch_loss += loss
        epoch_acc = acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)

def evaluate(model: MixingNN, dataloader: DataLoader, optimizer: Optimizer,
               criterion: MSELoss, device: str):
    epoch_loss = 0
    epoch_acc = 0

    model.eval()

    for (x, y) in tqdm(dataloader, desc="Training", leave=False):
        x = x.to(device)
        y = y.to(device)

        optimizer.zero_grad()

        pred, _ = model(x)
        loss = criterion(pred, y)

        acc = model.get_accuracy(pred, y)

        epoch_loss += loss
        epoch_acc = acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


def train_model():
    train_data, valid_data, test_data = create_sample_dbfs_dataloaders()
    dataloader = data.DataLoader(train_data, shuffle=True,
                                 batch_size=BATCH_SIZE)

    model = ChunkMixingNN(CHUNKS, CHUNKS)

    optimizer = optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = model.to(device)
    criterion = criterion.to(device)

    for epoch in trange(EPOCHS):
        train_loss, train_acc = train_loop(model, dataloader, optimizer,
                                           criterion, device)

        print(f'Epoch: {epoch + 1:02} ')
        print(
            f'\tTrain Loss: {train_loss:.3f} | '
            f'Train Acc: {train_acc * 100:.2f}%')

    return model

if __name__ == "__main__":
    model = train_model()
    pass
