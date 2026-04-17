import torch
import torch.nn as nn

class MethaneFluxCNNLSTM(nn.Module):
    """
    PyTorch Model Architecture for analyzing spatiotemporal Sentinel-1 SAR data.
    - 1D CNN: Extracts spatial scattering features (VV/VH bands).
    - LSTM: Decodes the temporal dynamics of AWD (Wet/Dry sequences over a month).
    - Fully Connected (FC): Calculates the correlated Methane (CH4) flux reduction score.
    """
    def __init__(self, input_channels=2, hidden_size=64, num_layers=2, output_size=1):
        super(MethaneFluxCNNLSTM, self).__init__()
        
        # CNN to extract spatial and band-level features
        # Input shape: (batch_size, input_channels, seq_len)
        self.conv1 = nn.Conv1d(in_channels=input_channels, out_channels=16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool1d(kernel_size=2)
        
        # LSTM layer to trace the AWD temporal pattern
        self.lstm = nn.LSTM(input_size=32, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        
        # Regressor block for carbon flux reduction
        self.fc1 = nn.Linear(hidden_size, 32)
        self.fc2 = nn.Linear(32, output_size)
        
    def forward(self, x):
        """
        Forward pass for the model.
        Expects x layout: (batch_size, input_channels=2, seq_len=30)
        """
        # Block 1: Feature Extraction
        c = self.conv1(x)
        c = self.relu(c)
        c = self.maxpool(c)  # Shape becomes (B, 16, seq_len/2)
        
        c = self.conv2(c)
        c = self.relu(c)
        c = self.maxpool(c)  # Shape becomes (B, 32, seq_len/4)
        
        # Permute for LSTM sequence consumption -> (Batch, Sequence, Features)
        c = c.permute(0, 2, 1)
        
        # Block 2: Temporal Analysis
        lstm_out, _ = self.lstm(c) # lstm_out shape: (B, seq_len/4, hidden_size)
        
        # We only need the context of the final sequence state for flux prediction
        last_hidden = lstm_out[:, -1, :] 
        
        # Block 3: Regression head
        out = self.fc1(last_hidden)
        out = self.relu(out)
        out = self.fc2(out)
        
        return out

def inference(sar_tensor: torch.Tensor) -> float:
    """
    Inference endpoint wrapper for the model.
    Passes a synthesized 30-day SAR block into the untrained model to output a CH4 Reduction baseline.
    """
    model = MethaneFluxCNNLSTM()
    model.eval()
    
    with torch.no_grad():
        flux_reduction = model(sar_tensor)
        
    return flux_reduction.item()

if __name__ == "__main__":
    # Test tensor representing 1 farmer, 2 SAR bands (VV/VH), over 30 days
    dummy_payload = torch.randn(1, 2, 30)
    score = inference(dummy_payload)
    print(f"Generated Methane Flux Reduction Score (Baseline initialized): {score:.4f} kg CO2e")
