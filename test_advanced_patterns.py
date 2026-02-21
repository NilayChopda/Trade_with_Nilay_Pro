
import pandas as pd
import numpy as np
import logging
from backend.strategy.patterns import AdvancedPatternsStrategy

def test_signal_generation():
    logging.basicConfig(level=logging.INFO)
    print("Testing AdvancedPatternsStrategy...")
    
    # 1. Create VCP-like data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Uptrend
    prices = np.linspace(100, 200, 40).tolist()
    
    # Contraction 1 (Deep)
    prices += [200, 180, 195, 175, 190]
    # Contraction 2 (Tighter)
    prices += [190, 185, 189, 186, 188]
    # Contraction 3 (Very Tight)
    prices += [188, 187.5, 188, 187.8, 188.1]
    
    # Fill remaining
    prices += [188.1] * (100 - len(prices))
    
    # Volume - decreasing
    volumes = np.linspace(2000000, 1500000, 40).tolist()
    volumes += np.linspace(1500000, 1000000, 30).tolist()
    volumes += np.linspace(1000000, 500000, 30).tolist()
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': prices,
        'volume': volumes
    })
    
    strategy = AdvancedPatternsStrategy()
    signals = strategy.analyze(df)
    
    print(f"\nSignals found: {len(signals)}")
    for s in signals:
        print(f"Pattern detected: {s['pattern']} (Confidence: {s['confidence']})")
        
    if any(s['pattern'] == 'VCP' for s in signals):
        print("\n✅ SUCCESS: VCP Pattern detected correctly!")
    else:
        print("\n❌ FAILURE: VCP Pattern not detected.")

if __name__ == "__main__":
    test_signal_generation()
