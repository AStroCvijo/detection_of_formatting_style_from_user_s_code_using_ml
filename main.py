import os
import re
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, TensorDataset
from sklearn.preprocessing import LabelEncoder

# Import the argument parser
from utils.argparser import arg_parse

# Import the seed setter
from utils.seed import set_seed

# Import the function for filtering coq files
from data.data_functions import filter_coq_files

# Import the functions for preprocessing the data
from data.data_functions import tokenize_coq_files_in_directory
from data.data_functions import create_sequences_and_labels
from data.data_functions import build_vocab
from data.data_functions import tokens_to_indices
from data.data_functions import split_data
from data.data_functions import CoqTokenDataset

# Import the function for training and evaluating the model
from train.train import train
from train.eval import eval

# Import the model
from model.LSTM import LSTM

if __name__ == "__main__":
    
    # Set the seed
    seed = 42
    set_seed(seed)

    # Parse the arguments
    args = arg_parse()

    # Extract coq files
    input_folder = "data/math-comp"
    output_folder = "data/coq_files"
    if (not os.path.isdir(output_folder)):
        filter_coq_files(input_folder, output_folder)

    # Directory containing coq files
    directory = 'data/coq_files'

    # --------------------------------------------------------------------------------------------------------------------------------------------
    # Preprocess the dataset
    # --------------------------------------------------------------------------------------------------------------------------------------------

    # Tokenize the coq code
    tokens, token_info = tokenize_coq_files_in_directory(directory)

    # Create sequences of tokens and their labels
    seq_length = args.sequence_length
    sequences, labels = create_sequences_and_labels(tokens, token_info, seq_length)

    # Build the vocabulary and convert to indexed sequences
    token_to_index = build_vocab(tokens)
    indexed_sequences = tokens_to_indices(sequences, token_to_index)

    # Split into train, validation, and test sets
    train_seqs, train_labels, val_seqs, val_labels, test_seqs, test_labels = split_data(indexed_sequences, labels)

    # Create Dataset and DataLoader for each split
    train_dataset = CoqTokenDataset(train_seqs, train_labels)
    val_dataset = CoqTokenDataset(val_seqs, val_labels)
    test_dataset = CoqTokenDataset(test_seqs, test_labels)

    # Create the dataloaders
    batch_size = args.batch_size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False, generator=torch.Generator().manual_seed(seed))
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)

    print("Data loaders initialized")

    # --------------------------------------------------------------------------------------------------------------------------------------------
    # Initialize and train the model
    # --------------------------------------------------------------------------------------------------------------------------------------------

    # Get the device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    # Model Constants
    embedding_dim = args.embedding_dim
    hidden_dim = args.hidden_dim
    num_layers = args.num_layers
    bidirectional = args.bidirectional
    output_dim = 3  # Three classes: <SPACE>, <NEWLINE>, other

    # Initialize the model and move it to the device
    vocab_size = len(token_to_index)
    model = LSTM(vocab_size, embedding_dim, hidden_dim, output_dim, num_layers, bidirectional).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)

    # Train the model
    num_epochs = args.epochs
    print("Starting training...")
    train(num_epochs, train_loader, test_loader, model, device, optimizer, criterion)

    # Calculate and print the overall accuracy
    train_accuracy = eval(train_loader, model, device)
    val_accuracy = eval(val_loader, model, device)
    test_accuracy = eval(test_loader, model, device)
    print(f"Training Accuracy: {train_accuracy:.4f}, Validation Accuracy: {val_accuracy:.4f}, Test Accuracy: {test_accuracy:.4f}")