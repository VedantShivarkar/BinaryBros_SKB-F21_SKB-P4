"""
=============================================================================
Amrit Vaayu dMRV — CNN-LSTM Model Architecture for Methane Flux Estimation
=============================================================================
Defines a hybrid CNN-LSTM deep learning model architecture designed to
process spatiotemporal SAR (Sentinel-1) time-series data and output a
methane (CH4) flux reduction score.

Architecture Overview:
  1. CNN Block:  Extracts local temporal features from raw SAR backscatter
                 using 1D convolutions over the time dimension.
  2. LSTM Block: Captures long-range temporal dependencies and cyclic
                 patterns in AWD wetting/drying sequences.
  3. FC Head:    Fully connected regression head that outputs a single
                 scalar — the predicted CH4 flux reduction in kg CO₂e.

Input shape:   (batch_size, sequence_length, num_features)
  - sequence_length: number of time steps (e.g., 30 days)
  - num_features:    SAR + auxiliary features per time step
    [vv_backscatter_db, vh_backscatter_db, soil_moisture_pct, methane_proxy]

Output shape:  (batch_size, 1)
  - Predicted methane flux reduction score (kg CO₂e)

Note: This module defines the architecture only. Training is not performed
      in this hackathon demo — the model is used with random weights for
      inference demonstration purposes.

Author: Binary Bros (Vedant Shivarkar & Akshad Kolawar)
=============================================================================
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple


class TemporalCNNBlock(nn.Module):
    """
    1D Convolutional block for extracting local temporal patterns
    from SAR time-series data.

    Architecture:
      Conv1D → BatchNorm → ReLU → Conv1D → BatchNorm → ReLU → MaxPool
      (with optional residual connection)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        use_residual: bool = True,
    ):
        super().__init__()
        self.use_residual = use_residual

        # Padding to maintain temporal dimension
        padding = kernel_size // 2

        self.conv_block = nn.Sequential(
            # First convolution layer
            nn.Conv1d(in_channels, out_channels, kernel_size=kernel_size, padding=padding),
            nn.BatchNorm1d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),

            # Second convolution layer (deeper feature extraction)
            nn.Conv1d(out_channels, out_channels, kernel_size=kernel_size, padding=padding),
            nn.BatchNorm1d(out_channels),
            nn.ReLU(inplace=True),
        )

        # Residual projection if channel dimensions differ
        self.residual_proj = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if use_residual and in_channels != out_channels
            else nn.Identity()
        )

        # Temporal downsampling
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (batch, channels, time_steps)
        Returns:
            Output tensor of shape (batch, out_channels, time_steps // 2)
        """
        out = self.conv_block(x)

        if self.use_residual:
            residual = self.residual_proj(x)
            # Match temporal dimensions if needed (due to pooling)
            out = out + residual

        out = self.pool(out)
        return out


class CH4FluxCNNLSTM(nn.Module):
    """
    Hybrid CNN-LSTM model for methane flux reduction estimation
    from SAR time-series data.

    The model processes multi-variate time-series input:
      - VV backscatter (dB)
      - VH backscatter (dB)
      - Soil moisture (%)
      - Methane proxy (mg/m²/day)

    And outputs a single regression value: predicted CH4 flux reduction.
    """

    def __init__(
        self,
        num_features: int = 4,
        seq_length: int = 30,
        cnn_channels: list = None,
        lstm_hidden_size: int = 64,
        lstm_num_layers: int = 2,
        fc_hidden_size: int = 32,
        dropout: float = 0.3,
    ):
        """
        Args:
            num_features:     Number of input features per time step (default: 4)
            seq_length:       Number of time steps in the input sequence (default: 30)
            cnn_channels:     List of CNN output channel sizes (default: [16, 32, 64])
            lstm_hidden_size: Number of hidden units in LSTM layers (default: 64)
            lstm_num_layers:  Number of stacked LSTM layers (default: 2)
            fc_hidden_size:   Hidden size of the fully connected regression head (default: 32)
            dropout:          Dropout probability (default: 0.3)
        """
        super().__init__()

        if cnn_channels is None:
            cnn_channels = [16, 32, 64]

        self.num_features = num_features
        self.seq_length = seq_length

        # -------------------------------------------------------------------
        # CNN FEATURE EXTRACTOR
        # -------------------------------------------------------------------
        # Stack of 1D conv blocks that progressively extract higher-level
        # temporal features while downsampling the time dimension.
        # -------------------------------------------------------------------
        cnn_layers = []
        in_ch = num_features
        for out_ch in cnn_channels:
            cnn_layers.append(TemporalCNNBlock(in_ch, out_ch, kernel_size=3))
            in_ch = out_ch

        self.cnn = nn.Sequential(*cnn_layers)

        # Calculate CNN output temporal dimension after pooling
        # Each TemporalCNNBlock halves the time dimension via MaxPool(2)
        cnn_output_time = seq_length
        for _ in cnn_channels:
            cnn_output_time = cnn_output_time // 2

        # Ensure we have at least 1 time step
        cnn_output_time = max(cnn_output_time, 1)
        self.cnn_output_channels = cnn_channels[-1]

        # -------------------------------------------------------------------
        # LSTM TEMPORAL ENCODER
        # -------------------------------------------------------------------
        # Bidirectional LSTM captures both forward and backward temporal
        # dependencies in the CNN feature sequence.
        # -------------------------------------------------------------------
        self.lstm = nn.LSTM(
            input_size=self.cnn_output_channels,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_num_layers,
            batch_first=True,
            dropout=dropout if lstm_num_layers > 1 else 0.0,
            bidirectional=True,
        )

        # -------------------------------------------------------------------
        # ATTENTION MECHANISM
        # -------------------------------------------------------------------
        # Temporal attention allows the model to focus on the most
        # informative time steps (e.g., transition points in AWD cycles).
        # -------------------------------------------------------------------
        self.attention = nn.Sequential(
            nn.Linear(lstm_hidden_size * 2, lstm_hidden_size),  # *2 for bidirectional
            nn.Tanh(),
            nn.Linear(lstm_hidden_size, 1),
        )

        # -------------------------------------------------------------------
        # FULLY CONNECTED REGRESSION HEAD
        # -------------------------------------------------------------------
        # Maps the attended LSTM features to the final CH4 flux reduction
        # prediction. Uses layer normalization for training stability.
        # -------------------------------------------------------------------
        self.fc = nn.Sequential(
            nn.Linear(lstm_hidden_size * 2, fc_hidden_size),
            nn.LayerNorm(fc_hidden_size),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(fc_hidden_size, fc_hidden_size // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout * 0.5),
            nn.Linear(fc_hidden_size // 2, 1),  # Single output: flux reduction score
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the CNN-LSTM model.

        Args:
            x: Input tensor of shape (batch_size, seq_length, num_features)
               e.g., (32, 30, 4) for a batch of 32 samples, 30 days, 4 features

        Returns:
            Predicted CH4 flux reduction of shape (batch_size, 1)
        """
        batch_size = x.size(0)

        # ------- CNN expects (batch, channels, time) -------
        x = x.permute(0, 2, 1)  # (batch, features, seq_len)

        # ------- Extract local temporal features -------
        cnn_out = self.cnn(x)  # (batch, cnn_channels, reduced_time)

        # ------- Reshape for LSTM: (batch, time, features) -------
        lstm_in = cnn_out.permute(0, 2, 1)  # (batch, reduced_time, cnn_channels)

        # ------- Capture long-range dependencies -------
        lstm_out, (h_n, c_n) = self.lstm(lstm_in)
        # lstm_out: (batch, reduced_time, lstm_hidden * 2)

        # ------- Apply temporal attention -------
        attn_weights = self.attention(lstm_out)  # (batch, reduced_time, 1)
        attn_weights = torch.softmax(attn_weights, dim=1)

        # Weighted sum of LSTM outputs
        context = torch.sum(attn_weights * lstm_out, dim=1)  # (batch, lstm_hidden * 2)

        # ------- Regression head -------
        output = self.fc(context)  # (batch, 1)

        return output

    def get_attention_weights(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns both predictions and attention weights for interpretability.
        Useful for visualizing which time steps the model considers most important.
        """
        batch_size = x.size(0)

        x = x.permute(0, 2, 1)
        cnn_out = self.cnn(x)
        lstm_in = cnn_out.permute(0, 2, 1)
        lstm_out, _ = self.lstm(lstm_in)

        attn_weights = self.attention(lstm_out)
        attn_weights = torch.softmax(attn_weights, dim=1)

        context = torch.sum(attn_weights * lstm_out, dim=1)
        output = self.fc(context)

        return output, attn_weights.squeeze(-1)


def run_mock_inference(
    sar_data: np.ndarray = None,
    seq_length: int = 30,
    num_features: int = 4,
) -> dict:
    """
    Run a mock inference pass through the CNN-LSTM model.

    This function initializes the model with random weights and performs
    a forward pass to demonstrate the architecture. In production, the
    model would be loaded from a trained checkpoint (.pt file).

    Args:
        sar_data:     Optional numpy array of shape (seq_length, num_features).
                      If None, generates random input data.
        seq_length:   Number of time steps (default: 30)
        num_features: Number of SAR features per step (default: 4)

    Returns:
        dict with:
            - "flux_reduction_score": Predicted CH4 reduction (kg CO₂e)
            - "model_params": Total trainable parameters
            - "attention_weights": Temporal attention distribution
    """
    # Set evaluation mode seed for reproducibility
    torch.manual_seed(42)

    # Initialize model
    model = CH4FluxCNNLSTM(
        num_features=num_features,
        seq_length=seq_length,
        cnn_channels=[16, 32, 64],
        lstm_hidden_size=64,
        lstm_num_layers=2,
        fc_hidden_size=32,
        dropout=0.3,
    )

    # Set to evaluation mode (disables dropout and batch normalization)
    model.eval()

    # Prepare input data
    if sar_data is not None:
        input_tensor = torch.tensor(sar_data, dtype=torch.float32).unsqueeze(0)
    else:
        input_tensor = torch.randn(1, seq_length, num_features)

    # Run inference (no gradient computation needed)
    with torch.no_grad():
        prediction, attention = model.get_attention_weights(input_tensor)

    # Map raw output to a realistic flux reduction range (5-25 kg CO₂e)
    flux_score = 5.0 + (torch.sigmoid(prediction).item() * 20.0)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "flux_reduction_score": round(flux_score, 2),
        "total_params": total_params,
        "trainable_params": trainable_params,
        "attention_weights": attention.squeeze(0).numpy().tolist(),
        "model_architecture": str(model),
    }


# ===========================================================================
# Standalone execution — demonstrate model architecture
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Amrit Vaayu dMRV — CNN-LSTM Model Architecture Demo")
    print("=" * 70)

    # --- Show model architecture ---
    model = CH4FluxCNNLSTM()
    print(f"\n{model}")

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n📊 Total parameters:     {total_params:,}")
    print(f"📊 Trainable parameters: {trainable_params:,}")

    # --- Run mock inference ---
    print("\n🔬 Running mock inference...")
    result = run_mock_inference()
    print(f"   Flux reduction score: {result['flux_reduction_score']:.2f} kg CO₂e")
    print(f"   Attention weights (top 5 time steps):")

    attn = result["attention_weights"]
    top_indices = sorted(range(len(attn)), key=lambda i: attn[i], reverse=True)[:5]
    for idx in top_indices:
        print(f"     Time step {idx}: {attn[idx]:.4f}")

    # --- Test with synthetic SAR data ---
    print("\n🛰️ Testing with synthetic SAR data...")
    try:
        from synthetic_sar import generate_sar_timeseries

        df = generate_sar_timeseries(num_days=30, seed=42)
        features = df[["vv_backscatter_db", "vh_backscatter_db",
                       "soil_moisture_pct", "methane_proxy"]].values

        result_sar = run_mock_inference(sar_data=features)
        print(f"   SAR-based flux reduction: {result_sar['flux_reduction_score']:.2f} kg CO₂e")
    except ImportError:
        print("   [SKIP] synthetic_sar module not available for integration test.")

    print("\n✅ CNN-LSTM architecture validation complete.")
