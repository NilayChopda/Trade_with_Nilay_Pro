
import os
import sys
import pandas as pd
import yfinance as yf
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.strategy.pattern_detector import PatternDetector

def test_symbols():
    symbols = ["KROSS", "ZINKA", "RELIANCE"]
    detector = PatternDetector()
    
    for s in symbols:
        print(f"\n--- Testing {s} ---")
        try:
            df = yf.download(f"{s}.NS", period="1y", progress=False)
            if df.empty:
                print(f"No data for {s}")
                continue
                
            df.columns = [c.lower() for c in df.columns]
            df['timestamp'] = df.index
            
            result = detector.analyze(df, s)
            print(f"Patterns found: {result['patterns']}")
            print(f"Primary Pattern: {result['primary_pattern']}")
            
            # Specific checks
            is_ipo = detector.is_ipo_base(df)
            is_vcp = detector.is_vcp(df)
            
            print(f"Is IPO Base? {is_ipo}")
            print(f"Is VCP? {is_vcp}")
            
        except Exception as e:
            print(f"Error testing {s}: {e}")

if __name__ == "__main__":
    test_symbols()
