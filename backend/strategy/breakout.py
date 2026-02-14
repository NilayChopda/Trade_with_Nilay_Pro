"""
Breakout Strategy
Detects price breakouts above recent resistance levels with volume confirmation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.strategy.base import Strategy

class BreakoutStrategy(Strategy):
    """
    Detects Price Breakouts
    Price > 20-period High AND Volume > 1.5x Avg Volume
    """
    
    def __init__(self):
        super().__init__("Breakout", "Detects high-momentum price breakouts")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df) or len(df) < 25:
            return []
            
        signals = []
        
        # Work on a copy to avoid SettingWithCopyWarning
        temp_df = df.copy()
        
        # 1. Calculate 20-period high (lookback to find resistance)
        # We look at the high of the PREVIOUS 20 candles
        temp_df['high_20'] = temp_df['high'].shift(1).rolling(window=20).max()
        temp_df['vol_ma_20'] = temp_df['volume'].rolling(window=20).mean()
        
        # 2. Breakout condition
        # Current Close > 20-day High AND Current Volume > 1.5x Avg
        temp_df['is_breakout'] = (temp_df['close'] > temp_df['high_20']) & (temp_df['volume'] > 1.5 * temp_df['vol_ma_20'])
        
        # 3. Potential Breakout (Near resistance)
        # Price is within 1.5% of high_20 AND range is narrow
        temp_df['near_resistance'] = (temp_df['close'] >= temp_df['high_20'] * 0.985) & (temp_df['close'] <= temp_df['high_20'] * 1.0)
        
        # 4. Narrow Range Check
        temp_df['range_pct'] = (temp_df['high'].rolling(5).max() - temp_df['low'].rolling(5).min()) / temp_df['close'] * 100
        temp_df['consolidated'] = temp_df['range_pct'].shift(1) < 3.0
        
        # Check last 2 candles
        recent_df = temp_df.iloc[-2:]
        
        for i, row in recent_df.iterrows():
            if row['is_breakout']:
                vol_mult = row['volume'] / row['vol_ma_20'] if row['vol_ma_20'] > 0 else 1
                confidence = 0.7 + (0.15 if vol_mult > 3.0 else 0) + (0.1 if row['consolidated'] else 0)
                
                signals.append({
                    "strategy": self.name,
                    "signal": "BULLISH",
                    "pattern": "Price Breakout",
                    "price": row['close'],
                    "breakout_level": round(row['high_20'], 2),
                    "volume_mult": round(vol_mult, 2),
                    "is_fresh": True,
                    "timestamp": i,
                    "confidence": min(confidence, 0.95)
                })
            elif row['near_resistance'] and row['consolidated']:
                 signals.append({
                    "strategy": self.name,
                    "signal": "NEUTRAL",
                    "pattern": "Potential Breakout",
                    "price": row['close'],
                    "resistance_level": round(row['high_20'], 2),
                    "timestamp": i,
                    "confidence": 0.75
                })
                
        return signals
