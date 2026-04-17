import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_sar_backscatter(days=30, cycle_length=7):
    """
    Generates synthetic Sentinel-1 SAR backscatter data (VV/VH bands) 
    over a specified number of days.
    
    The script generates distinct peaks (representing flooded/Wet cycle)
    and troughs (representing Dry cycle) to mimic the Alternate Wetting 
    and Drying (AWD) practices.
    """
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Base backscatter parameters in dB (typical for agricultural fields)
    base_vv = -12.0
    base_vh = -18.0
    
    vv_data = []
    vh_data = []
    
    np.random.seed(42) # For reproducible deterministic output in Hackathon demo
    
    for i in range(days):
        # A simple sine wave to mimic periodic flooding cycles
        # Adding Gaussian noise to simulate satellite sensor scattering variations
        cycle = np.sin(2 * np.pi * i / cycle_length)
        noise = np.random.normal(0, 0.6)
        
        # VV is highly sensitive to standing water (increases significantly)
        vv_val = base_vv + (cycle * 2.5) + noise
        
        # VH is more sensitive to volume scattering/biomass 
        vh_val = base_vh + (cycle * 1.2) + noise
        
        vv_data.append(vv_val)
        vh_data.append(vh_val)
        
    df = pd.DataFrame({
        "Date": dates,
        "VV_Backscatter_dB": vv_data,
        "VH_Backscatter_dB": vh_data
    })
    
    return df

if __name__ == "__main__":
    df_sar = generate_sar_backscatter()
    print("Generated Synthetic SAR Time-Series Data:")
    print(df_sar.head(10))
