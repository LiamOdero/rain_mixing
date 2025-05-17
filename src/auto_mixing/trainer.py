import torch
from torch import nn, optim
from torch.nn import MSELoss
from torch.optim import Optimizer
from torch.utils import data
from torch.utils.data import DataLoader
from auto_mixing.data.logging import CHUNKS
from auto_mixing.data.dataloader import create_sample_dBFS_dataloaders
from auto_mixing.models.ChunkMixingNN import ChunkMixingNN
from auto_mixing.models.MixingNN import MixingNN
from constants.model_constants import (BATCH_SIZE, LR, RANGE_REDUCTION,
                                       EPOCHS, WEIGHT_DECAY)
import matplotlib.pyplot as plt


def train_loop(model: MixingNN, dataloader: DataLoader, optimizer: Optimizer,
               criterion: MSELoss, device: str):
    epoch_loss = 0
    epoch_acc = 0

    model.train()

    for (x, y) in dataloader:
        x = x.to(device)
        y = y.to(device)

        x = x / -RANGE_REDUCTION
        y = y / -RANGE_REDUCTION

        optimizer.zero_grad()

        pred = model(x)
        # Scale predictions and targets since we are working with values
        # in the range ~(0, 1), so MSE appears very small when acc is bad
        loss = criterion(pred * -RANGE_REDUCTION, y * -RANGE_REDUCTION)

        acc = model.get_accuracy(pred, y)

        loss.backward()
        optimizer.step()

        epoch_loss += loss
        epoch_acc += acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


def evaluate(model: MixingNN, dataloader: DataLoader,
             criterion: MSELoss, device: str):
    epoch_loss = 0
    epoch_acc = 0

    model.eval()

    for (x, y) in dataloader:
        x = x.to(device)
        y = y.to(device)

        x = x / -RANGE_REDUCTION
        y = y / -RANGE_REDUCTION

        pred = model(x)
        loss = criterion(pred * -RANGE_REDUCTION, y * -RANGE_REDUCTION)

        acc = model.get_accuracy(pred, y)

        epoch_loss += loss
        epoch_acc += acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


def plot_training(epochs, train_losses, valid_losses):
    plt.figure(figsize=(10, 6))

    # Plot training and validation losses
    plt.plot(epochs, train_losses, label='Training Loss', marker='o')
    plt.plot(epochs, valid_losses, label='Validation Loss', marker='s')

    # Add labels and title
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss over Epochs')
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.tight_layout()
    plt.show()


def train_model():
    torch.seed()

    train_data, valid_data, test_data = create_sample_dBFS_dataloaders()
    train_dataloader = data.DataLoader(train_data, shuffle=True,
                                       batch_size=BATCH_SIZE)
    valid_dataloader = data.DataLoader(valid_data, shuffle=True,
                                       batch_size=BATCH_SIZE)
    test_dataloader = data.DataLoader(test_data, shuffle=True,
                                      batch_size=BATCH_SIZE)

    model = ChunkMixingNN(CHUNKS, 1)

    optimizer = optim.Adam(model.parameters(), lr=LR,
                           weight_decay=WEIGHT_DECAY)
    criterion = nn.MSELoss()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = model.to(device)
    criterion = criterion.to(device)

    train_losses = []
    valid_losses = []
    epochs = []

    for epoch in range(EPOCHS):
        train_loss, train_acc = train_loop(model, train_dataloader, optimizer,
                                           criterion, device)

        print(f'Epoch: {epoch + 1:02} ')
        print(
            f'\tTrain Loss: {train_loss:.3f} | '
            f'Train Acc: {train_acc * 100:.2f}%')
        train_losses.append(train_loss.item())

        valid_loss, valid_acc = evaluate(model, valid_dataloader, criterion,
                                         device)
        print(
            f'\tValid Loss: {valid_loss:.3f} | '
            f'Valid Acc: {valid_acc * 100:.2f}%')
        valid_losses.append(valid_loss.item())
        epochs.append(epoch)

    test_loss, test_acc = evaluate(model, test_dataloader, criterion,
                                   device)
    print(
        f'Test Loss: {test_loss:.3f} | '
        f'Test Acc: {test_acc * 100:.2f}%')
    plot_training(epochs, train_losses, valid_losses)
    return model


if __name__ == "__main__":
    model = train_model()
    pass
