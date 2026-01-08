import torch
from torch import nn, optim
from torch.nn import MSELoss
from torch.optim import Optimizer
from torch.utils import data
from torch.utils.data import DataLoader

from auto_mixing.data.DBFSSampleDataset import DBFSSampleDataset
from auto_mixing.data.dataloader import create_sample_dataloaders
from auto_mixing.models.ChunkMixingNN import ChunkMixingNN
from auto_mixing.models.MixingNN import MixingNN
from constants.model_constants import (BATCH_SIZE, LR, RANGE_REDUCTION,
                                       EPOCHS, WEIGHT_DECAY)
import matplotlib.pyplot as plt

"""
Passes inputs through the model for a single training loop step

:param
    -   model: The model currently being trained
    -   dataloader: Contains the batched training samples and labels
    -   optimizer: The optimizer type to use in each step
    -   criterion: The loss function to use in each step
    -   device: The device (cpu or cuda) to use in training
:return
    -   final_loss: Average loss over all batches for this step
    -   final_acc: Average accuracy over all batches for this step
"""


def train_loop(model: MixingNN, dataloader: DataLoader, optimizer: Optimizer,
               criterion: MSELoss, device: str) -> tuple[float, float]:
    epoch_loss = 0
    epoch_acc = 0

    model.train()

    for (x, y) in dataloader:
        x = x.to(device)
        y = y.to(device)

        # scale samples so that model weights are not large
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

        epoch_loss += loss.item()
        epoch_acc += acc.item()

    final_loss = epoch_loss / len(dataloader)
    final_acc = epoch_acc / len(dataloader)
    return final_loss, final_acc


"""
Passes inputs through a model to test its performance

:param
    -   model: The model being evaluated
    -   dataloader: Contains the batched testing samples and labels
    -   criterion: The loss function to use
    -   device: The device (cpu or cuda) to evaluate on
:return
    -   final_loss: Average loss over all batches
    -   final_acc: Average accuracy over all batches
"""


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

        epoch_loss += loss.item()
        epoch_acc += acc.item()

    return epoch_loss / len(dataloader), epoch_acc / len(dataloader)


"""
Plots the total training and validation loss for each step

:param
    -   epochs: a list of epoch numbers
    -   train_losses: a list of training losses corresponding to <epochs>
    -   valid_losses: a list of validation losses corresponding to <epochs>
"""


def plot_training(epochs: list[int],
                  train_losses: list[float],
                  valid_losses: list[float]) -> None:
    plt.figure(figsize=(10, 6))

    # Plot training and validation losses
    plt.plot(epochs, train_losses, label='Training Loss')
    plt.plot(epochs, valid_losses, label='Validation Loss')

    # Add labels and title
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss over Epochs')
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.tight_layout()
    plt.show()


"""
Plots the total training and validation accuracy for each step

:param
    -   epochs: a list of epoch numbers
    -   train_losses: a list of training accuracies corresponding to <epochs>
    -   valid_losses: a list of validation accuracies corresponding to <epochs>
"""


def plot_acc(epochs, train_acc, valid_acc):
    plt.figure(figsize=(10, 6))

    # Plot training and validation losses
    plt.plot(epochs, train_acc, label='Training Accuracy')
    plt.plot(epochs, valid_acc, label='Validation Accuracy')

    # Add labels and title
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training and Validation Accuracy over Epochs')
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.tight_layout()
    plt.show()


"""
Trains a model to use for mixing

:return
    -   model: A fully trained MixingNN to use in mixing tracks
"""


def train_model() -> MixingNN:
    torch.seed()

    # initialize data
    train_data, valid_data, test_data = (
        create_sample_dataloaders(DBFSSampleDataset))

    train_dataloader = data.DataLoader(train_data, shuffle=True,
                                       batch_size=BATCH_SIZE)
    valid_dataloader = data.DataLoader(valid_data, shuffle=True,
                                       batch_size=BATCH_SIZE)
    test_dataloader = data.DataLoader(test_data, shuffle=True,
                                      batch_size=BATCH_SIZE)

    model = ChunkMixingNN(1)

    # initialize training params
    optimizer = optim.Adam(model.parameters(), lr=LR,
                           weight_decay=WEIGHT_DECAY)
    criterion = nn.MSELoss()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = model.to(device)
    criterion = criterion.to(device)

    train_losses = []
    train_accs = []
    valid_losses = []
    valid_accs = []
    epochs = []

    # training loop
    for epoch in range(EPOCHS):
        # perform one step of the training process
        train_loss, train_acc = train_loop(model, train_dataloader, optimizer,
                                           criterion, device)

        print(f'Epoch: {epoch + 1:02} ')
        print(
            f'\tTrain Loss: {train_loss:.3f} | '
            f'Train Acc: {train_acc * 100:.2f}%')
        train_losses.append(train_loss)
        train_accs.append(train_acc)

        # perform evaluation on validation set
        valid_loss, valid_acc = evaluate(model, valid_dataloader, criterion,
                                         device)
        print(
            f'\tValid Loss: {valid_loss:.3f} | '
            f'Valid Acc: {valid_acc * 100:.2f}%')
        valid_losses.append(valid_loss)
        valid_accs.append(valid_acc)
        epochs.append(epoch)

    # final evaluation on test set
    test_loss, test_acc = evaluate(model, test_dataloader, criterion,
                                   device)
    print(
        f'Test Loss: {test_loss:.3f} | '
        f'Test Acc: {test_acc * 100:.2f}%')
    plot_training(epochs, train_losses, valid_losses)
    plot_acc(epochs, train_accs, valid_accs)
    return model


if __name__ == "__main__":
    train_model()
    pass
