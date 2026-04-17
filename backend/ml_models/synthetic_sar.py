"""
=============================================================================
Amrit Vaayu dMRV — Synthetic SAR Data Generator
=============================================================================
Generates realistic mock time-series data mimicking Sentinel-1 C-band SAR
(Synthetic Aperture Radar) backscatter variations over a 30-day period.

The generated data models VV and VH polarization backscatter coefficients
that exhibit clear peaks (flooding/wetting) and troughs (drying) consistent
with Alternate Wetting and Drying (AWD) rice paddy management cycles.

Scientific basis:
  - Sentinel-1 operates at C-band (5.405 GHz)
  - VV polarization is sensitive to surface water presence
  - VH polarization responds to vegetation structure and moisture
  - Flooded paddies show σ° VV ≈ -8 to -12 dB (specular reflection)
  - Dry paddies show σ° VV ≈ -15 to -22 dB (rough surface scattering)
  - AWD creates periodic 5-7 day wetting/drying oscillations

Output:
  - Pandas DataFrame with columns:
    [day, date, vv_backscatter_db, vh_backscatter_db, soil_moisture_pct,
     awd_phase, methane_proxy]
  - Suitable for ingestion by the CNN-LSTM model

Author: Binary Bros (Vedant Shivarkar & Akshad Kolawar)
=============================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def generate_sar_timeseries(
    num_days: int = 30,
    awd_cycle_days: int = 6,
    start_date: Optional[str] = None,
    noise_level: float = 0.5,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generate synthetic Sentinel-1 SAR backscatter time-series data
    that models AWD (Alternate Wetting and Drying) rice cultivation.

    Args:
        num_days:        Number of days in the time series (default: 30)
        awd_cycle_days:  Length of one full AWD cycle in days (default: 6)
        start_date:      Start date in 'YYYY-MM-DD' format (default: today)
        noise_level:     Standard deviation of Gaussian noise added (default: 0.5 dB)
        seed:            Random seed for reproducibility (default: None)

    Returns:
        pd.DataFrame with columns:
            - day:                 Day index (0 to num_days-1)
            - date:                Date string (YYYY-MM-DD)
            - vv_backscatter_db:   VV polarization backscatter (dB)
            - vh_backscatter_db:   VH polarization backscatter (dB)
            - soil_moisture_pct:   Simulated volumetric soil moisture (%)
            - awd_phase:           Current phase ("Wetting" or "Drying")
            - methane_proxy:       Simulated CH4 emission proxy (mg/m²/day)
    """

    # -----------------------------------------------------------------------
    # Initialize random number generator
    # -----------------------------------------------------------------------
    rng = np.random.default_rng(seed)

    # -----------------------------------------------------------------------
    # Date range
    # -----------------------------------------------------------------------
    if start_date:
        base_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        base_date = datetime.now() - timedelta(days=num_days)

    dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]

    # -----------------------------------------------------------------------
    # Generate AWD oscillation pattern
    # -----------------------------------------------------------------------
    # The AWD cycle creates a sawtooth-like waveform:
    #   - Wetting phase: water level rises → VV backscatter increases (less negative)
    #   - Drying phase: water drains → VV backscatter decreases (more negative)
    #
    # We use a sine wave modulated by a phase offset to create this pattern.
    # -----------------------------------------------------------------------
    t = np.arange(num_days, dtype=np.float64)
    omega = 2 * np.pi / awd_cycle_days  # Angular frequency

    # Primary AWD oscillation signal
    awd_signal = np.sin(omega * t)

    # Add a secondary harmonic for realistic sub-cycle variations
    awd_signal += 0.3 * np.sin(2 * omega * t + np.pi / 4)

    # Normalize to [0, 1] range
    awd_signal = (awd_signal - awd_signal.min()) / (awd_signal.max() - awd_signal.min())

    # -----------------------------------------------------------------------
    # VV Polarization Backscatter (σ° VV)
    # -----------------------------------------------------------------------
    # Flooded (wet) state:   σ° ≈ -8 to -12 dB (specular reflection from water)
    # Dry state:             σ° ≈ -18 to -22 dB (rough surface backscatter)
    # -----------------------------------------------------------------------
    vv_wet_db = -9.0    # Mean VV when fully flooded
    vv_dry_db = -20.0   # Mean VV when fully dry
    vv_range = vv_wet_db - vv_dry_db  # ≈ 11 dB dynamic range

    vv_backscatter = vv_dry_db + (awd_signal * vv_range)
    vv_backscatter += rng.normal(0, noise_level, num_days)  # Add sensor noise

    # -----------------------------------------------------------------------
    # VH Polarization Backscatter (σ° VH)
    # -----------------------------------------------------------------------
    # VH is less sensitive to surface water but responds to vegetation.
    # Typically 5-8 dB lower than VV, with smaller dynamic range.
    # -----------------------------------------------------------------------
    vh_offset = -6.5     # VH is typically ~6.5 dB below VV
    vh_dynamic_range = 0.4  # VH shows muted response to AWD

    vh_backscatter = vv_backscatter + vh_offset + (awd_signal * vh_dynamic_range * vv_range)
    vh_backscatter += rng.normal(0, noise_level * 0.7, num_days)

    # -----------------------------------------------------------------------
    # Soil Moisture (volumetric %)
    # -----------------------------------------------------------------------
    # Correlated with AWD signal but with a slight temporal lag (~1 day)
    # Saturated (wet): 45-55%  |  Dry: 15-25%
    # -----------------------------------------------------------------------
    moisture_wet = 50.0
    moisture_dry = 18.0

    # Apply 1-day lag via shifted signal
    moisture_signal = np.roll(awd_signal, 1)
    moisture_signal[0] = awd_signal[0]  # Fix boundary

    soil_moisture = moisture_dry + (moisture_signal * (moisture_wet - moisture_dry))
    soil_moisture += rng.normal(0, noise_level * 2.0, num_days)
    soil_moisture = np.clip(soil_moisture, 5.0, 65.0)  # Physical bounds

    # -----------------------------------------------------------------------
    # AWD Phase Label
    # -----------------------------------------------------------------------
    # Determine wetting vs drying based on signal derivative
    # -----------------------------------------------------------------------
    signal_diff = np.diff(awd_signal, prepend=awd_signal[0])
    awd_phase = ["Wetting" if d >= 0 else "Drying" for d in signal_diff]

    # -----------------------------------------------------------------------
    # Methane (CH4) Emission Proxy
    # -----------------------------------------------------------------------
    # CH4 emissions from paddies are strongly correlated with:
    #   1. Duration of continuous flooding (anaerobic conditions)
    #   2. Soil organic matter decomposition rate
    #   3. Soil temperature (simplified as constant here)
    #
    # AWD reduces CH4 by 30-50% compared to continuous flooding.
    # Proxy units: mg CH4/m²/day
    #
    # Continuously flooded baseline:  ~250 mg/m²/day
    # AWD cycle average:              ~120-180 mg/m²/day
    # Dry phase minimum:              ~30-60 mg/m²/day
    # -----------------------------------------------------------------------
    ch4_baseline = 250.0            # Continuous flooding baseline
    ch4_min = 35.0                  # Minimum during dry phase
    ch4_range = ch4_baseline - ch4_min

    # Exponential relationship: CH4 increases non-linearly with water level
    methane_proxy = ch4_min + (awd_signal ** 1.5) * ch4_range
    methane_proxy += rng.normal(0, noise_level * 15, num_days)
    methane_proxy = np.clip(methane_proxy, 10.0, 350.0)

    # -----------------------------------------------------------------------
    # Assemble DataFrame
    # -----------------------------------------------------------------------
    df = pd.DataFrame({
        "day": np.arange(num_days),
        "date": dates,
        "vv_backscatter_db": np.round(vv_backscatter, 3),
        "vh_backscatter_db": np.round(vh_backscatter, 3),
        "soil_moisture_pct": np.round(soil_moisture, 2),
        "awd_phase": awd_phase,
        "methane_proxy": np.round(methane_proxy, 2),
    })

    return df


def generate_multi_farmer_sar(
    num_farmers: int = 8,
    num_days: int = 30,
    base_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate SAR time-series data for multiple farmers, each with slightly
    different AWD cycle timing and noise characteristics.

    Args:
        num_farmers: Number of farmer datasets to generate
        num_days:    Days in each time series
        base_seed:   Base random seed (each farmer gets base_seed + farmer_id)

    Returns:
        pd.DataFrame with an additional 'farmer_id' column
    """
    all_data = []

    for farmer_id in range(1, num_farmers + 1):
        # Each farmer has a slightly different cycle length (5-7 days)
        cycle_days = 5 + (farmer_id % 3)  # Cycles of 5, 6, or 7 days

        # Generate individual farmer data
        df = generate_sar_timeseries(
            num_days=num_days,
            awd_cycle_days=cycle_days,
            noise_level=0.3 + (farmer_id * 0.05),  # Varying noise per farmer
            seed=base_seed + farmer_id,
        )

        # Add farmer identifier
        df.insert(0, "farmer_id", farmer_id)
        all_data.append(df)

    # Concatenate all farmer data
    combined_df = pd.concat(all_data, ignore_index=True)

    return combined_df


# ===========================================================================
# Standalone execution — generate and preview data
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Amrit Vaayu dMRV — Synthetic SAR Data Generator")
    print("=" * 70)

    # Generate single farmer data
    print("\n📡 Generating 30-day SAR time series for a single farmer...")
    df_single = generate_sar_timeseries(num_days=30, seed=42)
    print(f"\nShape: {df_single.shape}")
    print(f"\nSample data (first 10 days):")
    print(df_single.head(10).to_string(index=False))

    print(f"\n--- Statistics ---")
    print(f"VV Backscatter range: {df_single['vv_backscatter_db'].min():.1f} to "
          f"{df_single['vv_backscatter_db'].max():.1f} dB")
    print(f"VH Backscatter range: {df_single['vh_backscatter_db'].min():.1f} to "
          f"{df_single['vh_backscatter_db'].max():.1f} dB")
    print(f"Soil Moisture range:  {df_single['soil_moisture_pct'].min():.1f} to "
          f"{df_single['soil_moisture_pct'].max():.1f} %")
    print(f"Methane proxy range:  {df_single['methane_proxy'].min():.1f} to "
          f"{df_single['methane_proxy'].max():.1f} mg/m²/day")

    wetting_count = (df_single["awd_phase"] == "Wetting").sum()
    drying_count = (df_single["awd_phase"] == "Drying").sum()
    print(f"Wetting days: {wetting_count} | Drying days: {drying_count}")

    # Generate multi-farmer data
    print("\n\n📡 Generating multi-farmer SAR data (8 farmers × 30 days)...")
    df_multi = generate_multi_farmer_sar(num_farmers=8, num_days=30)
    print(f"Combined shape: {df_multi.shape}")
    print(f"Farmers: {df_multi['farmer_id'].nunique()}")
    print(f"\nMean methane by farmer:")
    print(df_multi.groupby("farmer_id")["methane_proxy"].mean().round(1).to_string())

    print("\n✅ Synthetic SAR data generation complete.")
