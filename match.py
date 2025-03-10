import pandas as pd
import os

def load_csv_files():
    # Get absolute path to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, 'csv', 'equi')
    
    # Verify directory exists
    if not os.path.exists(csv_dir):
        print(f"Directory not found: {csv_dir}")
        return None
        
    try:
        # Load CSVs using absolute paths
        dataframes = {
            'pfsi': pd.read_csv(os.path.join(csv_dir, 'pfsi_v2_principal.csv')),
            'cedulas': pd.read_csv(os.path.join(csv_dir, 'repd_vp_cedulas_principal.csv')),
            'senas': pd.read_csv(os.path.join(csv_dir, 'repd_vp_cedulas_senas.csv')),
            'vestimenta': pd.read_csv(os.path.join(csv_dir, 'repd_vp_cedulas_vestimenta.csv'))
        }
        return dataframes
    
    except FileNotFoundError as e:
        print(f"Error: Could not find one or more CSV files in {csv_dir}")
        print(f"Detailed error: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

# Load and verify
df_dict = load_csv_files()
if df_dict:
    for name, df in df_dict.items():
        print(f"{name} shape: {df.shape}")