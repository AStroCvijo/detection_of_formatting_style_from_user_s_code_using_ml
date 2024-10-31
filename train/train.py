import torch
import torch.nn as nn
from model.LSTM import LSTM
from torch.utils.data import DataLoader, Dataset, TensorDataset
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence

# Import the model
from train.eval import eval

# Function for training the model
def train(num_epochs, train_loader, test_loader, model, device, optimizer, criterion):
    for epoch in range(num_epochs):
        total_loss = 0
        for batch_idx, (batch_sequences, batch_labels) in enumerate(train_loader):
            # Move data to the device
            batch_sequences, batch_labels = batch_sequences.to(device), batch_labels.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            output = model(batch_sequences)
            
            # Compute loss and backpropagate
            loss = criterion(output, batch_labels)
            loss.backward()
            optimizer.step()
            
            # Accumulate and print loss every 200 batches
            total_loss += loss.item()
            if (batch_idx + 1) % 200 == 0:
                print(f"Epoch {epoch+1}, Batch {batch_idx+1}, Loss: {loss.item():.4f}")
                
        # Calculate training accuracy
        train_accuracy = eval(train_loader, model, device)
        # Calculate test accuracy
        test_accuracy = eval(test_loader, model, device)
        
        print(f"Epoch {epoch+1}/{num_epochs}, Average Loss: {total_loss / len(train_loader):.4f}, Training Accuracy: {train_accuracy:.4f}, Test Accuracy: {test_accuracy:.4f}")
    
    # Model save path
    model_save_path = "pretrained_models/model.pth"

    # Save the model
    torch.save(model.state_dict(), model_save_path)
    print(f"Model saved to {model_save_path}")