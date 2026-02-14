import pandas as pd
import os

# Check scanner results
results_dir = 'scanner_results'
if os.path.exists(results_dir):
    files = [f for f in os.listdir(results_dir) if f.startswith('results_')]
    
    if files:
        latest = max(files)  # Get most recent file
        df = pd.read_csv(f'scanner_results/{latest}')
        
        print(f"📊 LATEST SCAN RESULTS ({latest}):")
        print(f"Found {len(df)} stocks")
        print("\n" + "="*50)
        print(df[['symbol', 'name', 'price', 'change']])
    else:
        print("No scan results found yet")
else:
    print("scanner_results folder doesn't exist")