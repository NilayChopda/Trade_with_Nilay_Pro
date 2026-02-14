"""
Smart Money Concepts (SMC) Strategies
Detects Order Blocks and Market Structure Shifts
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.strategy.base import Strategy
from backend.strategy.indicators import find_pivot_highs, find_pivot_lows

class OrderBlockStrategy(Strategy):
    """
    Detects Bullish/Bearish Order Blocks (OB)
    Bullish OB: The last bearish candle before a strong bullish move that breaks structure/high.
    Bearish OB: The last bullish candle before a strong bearish move that breaks structure/low.
    """
    
    def __init__(self):
        super().__init__("Order Block", "Institutional entry zones")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Simplified OB Detection logic:
        1. Find Pivot Lows/Highs
        2. Identify strong impulsive moves (large body candles)
        3. Trace back to the origin candle (OB)
        """
        if not self.validate_data(df):
            return []
            
        signals = []
        
        # We need at least 50 candles to find meaningful structure
        if len(df) < 50:
            return []
            
        # Helper: Calculate body size
        df['body'] = abs(df['close'] - df['open'])
        df['range'] = df['high'] - df['low']
        avg_body = df['body'].rolling(20).mean()
        
        # Detect Bullish OBs
        # Logic: A down candle followed by a sequence that breaks a recent high with momentum
        
        # Look at last 20 candles for potential active OBs
        subset = df.iloc[-20:]
        
        for i in range(len(subset) - 3): # Need space for follow through
             # Identifying potential OB candle
            ob_idx = subset.index[i]
            ob_candle = subset.loc[ob_idx]
            
            # Bullish OB Candidate: Must be a Red Candle (Close < Open)
            if ob_candle['close'] >= ob_candle['open']:
                continue
                
            # Check for subsequent break of structure (BOS) or strong move
            # Look ahead 3-5 candles
            future_candles = subset.loc[subset.index[i+1 : i+6]]
            
            if future_candles.empty:
                continue
                
            # Condition 1: Strong bullish move (at least one large green candle)
            has_big_green = any((c['close'] > c['open']) and (c['body'] > 1.5 * avg_body.loc[ob_idx]) for _, c in future_candles.iterrows())
            
            # Condition 2: Price broke above OB high
            broke_high = future_candles['close'].max() > ob_candle['high']
            
            if has_big_green and broke_high:
                # Potential Bullish OB found.
                # Check if price is currently retesting it? Or just report the zone.
                # For signalling, we usually want to know if price is NEAR the OB now.
                
                current_price = df.iloc[-1]['close']
                ob_high = ob_candle['high']
                ob_low = ob_candle['low']
                
                # Check if current price is retesting the zone (within or near)
                # Zone: Low to High of the OB candle
                dist_to_zone = abs(current_price - ob_high)
                is_retesting = (ob_low <= current_price <= ob_high * 1.001)
                
                # Report if it's a fresh OB (created recently) OR we are retesting it
                is_fresh = (i >= len(subset) - 5) # Created in last 5 candles
                
                if is_fresh or is_retesting:
                    signals.append({
                        "strategy": self.name,
                        "signal": "BUY" if is_retesting else "NEUTRAL",
                        "pattern": "Bullish Order Block",
                        "price": current_price,
                        "zone_high": ob_high,
                        "zone_low": ob_low,
                        "timestamp": subset.index[-1], # Current time
                        "confidence": 0.8 if is_retesting else 0.5
                    })

        return signals


class MSSStrategy(Strategy):
    """
    Market Structure Shift (MSS) / Change of Character (ChoCh)
    Detects trend reversals by identifying breaks of recent pivot points.
    """
    
    def __init__(self):
        super().__init__("Market Structure Shift", "Trend reversal detector using pivots")
        
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        signals = []
        
        # Calculate Pivots
        df['is_pivot_high'] = find_pivot_highs(df['high'], left=5, right=5)
        df['is_pivot_low'] = find_pivot_lows(df['low'], left=5, right=5)
        
        # Get recent pivots
        pivot_highs = df[df['is_pivot_high'] == True]
        pivot_lows = df[df['is_pivot_low'] == True]
        
        if pivot_highs.empty or pivot_lows.empty:
            return []
            
        # Logic for Bullish MSS:
        # 1. Price was making Lower Lows (Downtrend)
        # 2. Price breaks above the last valid Lower High
        
        last_ph = pivot_highs.iloc[-1]
        last_pl = pivot_lows.iloc[-1]
        
        # Check current price action (last 3 candles)
        recent_df = df.iloc[-3:]
        
        for i, row in recent_df.iterrows():
            # Bullish MSS Check
            # Current Close > Last Pivot High
            # And that Pivot High index < Current Index
            if row['close'] > last_ph['high'] and last_ph.name < i:
                # Filter: Ensure the pivot high is somewhat recent (within last 50 candles)
                # (Assuming index is timestamp or sequential int, relying on list position here effectively)
                
                signals.append({
                    "strategy": self.name,
                    "signal": "BUY",
                    "pattern": "Bullish MSS",
                    "price": row['close'],
                    "break_level": last_ph['high'],
                    "sl": last_pl['low'],
                    "timestamp": i,
                    "confidence": 0.75
                })
                
            # Bearish MSS Check
            if row['close'] < last_pl['low'] and last_pl.name < i:
                signals.append({
                    "strategy": self.name,
                    "signal": "SELL",
                    "pattern": "Bearish MSS",
                    "price": row['close'],
                    "break_level": last_pl['low'],
                    "sl": last_ph['high'],
                    "timestamp": i,
                    "confidence": 0.75
                })
                
        return signals
