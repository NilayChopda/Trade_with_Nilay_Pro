"""
EMA Bounce Strategy
Detects when price touches/bounces off the 9 EMA
"""

import pandas as pd
from typing import List, Dict, Any
from backend.strategy.base import Strategy
from backend.strategy.indicators import calculate_ema

class EMABounceStrategy(Strategy):
    """
    Strategy: 9 EMA Bounce
    Timeframe: 1 Minute / 5 Minute
    Logic:
    1. Trend is UP (Price > EMA 20)
    2. Price pulls back to touch EMA 9
    3. Candle closes bullish (Close > Open)
    """
    
    def __init__(self):
        super().__init__("EMA 9 Bounce", "Trend following strategy on pullbacks to EMA 9")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        signals = []
        
        # Calculate Indicators
        df['ema_9'] = calculate_ema(df['close'], 9)
        df['ema_20'] = calculate_ema(df['close'], 20)
        
        # We need at least 20 candles
        if len(df) < 20:
            return []
            
        # Iterate through the last few candles (e.g. last 3) to find recent setups
        # We don't want to alert on old setups
        recent_df = df.iloc[-3:]
        
        for i, row in recent_df.iterrows():
            # Logic 1: Trend is UP (EMA 9 > EMA 20)
            is_uptrend = row['ema_9'] > row['ema_20']
            
            if not is_uptrend:
                continue
                
            # Logic 2: Price touched EMA 9
            # Low <= EMA 9 <= High
            touched_ema = row['low'] <= row['ema_9'] <= row['high']
            
            if not touched_ema:
                continue
                
            # Logic 3: Bullish Close (Green Candle)
            is_green = row['close'] > row['open']
            
            if is_green:
                signals.append({
                    "strategy": self.name,
                    "symbol": "UNKNOWN", # Engine fills this
                    "signal": "BUY",
                    "price": row['close'],
                    "sl": row['low'] - 0.5, # slightly below low
                    "target": row['close'] + (row['close'] - row['low']) * 2, # 1:2 Risk Reward
                    "timestamp": i,
                    "confidence": 0.8
                })
                
        return signals
