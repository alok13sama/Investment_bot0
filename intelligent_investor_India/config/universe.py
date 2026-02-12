# config/universe.py
import pandas as pd
import os
from config.settings import DATA_DIR

def get_nifty500_tickers():
    """
    Reads the NIFTY 500 CSV and adds '.NS' suffix for Yahoo Finance.
    """
    csv_path = DATA_DIR / "nifty500.csv"
    
    if not os.path.exists(csv_path):
        print(f"⚠ Warning: {csv_path} not found. Using NIFTY 50 fallback.")
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'] # Fallback
        
    try:
        df = pd.read_csv(csv_path)
        # NSE CSVs usually have a 'Symbol' column
        tickers = df['Symbol'].tolist()
        
        # Add .NS suffix if missing
        tickers = [f"{t}.NS" if not str(t).endswith('.NS') else t for t in tickers]
        
        print(f"✅ Loaded {len(tickers)} stocks from NIFTY 500 CSV.")
        return tickers
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []