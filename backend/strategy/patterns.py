"""
Candlestick Pattern Strategies
Implements simple candlestick patterns: Doji, Inside Bar, Dead Volume
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.strategy.base import Strategy

class DojiStrategy(Strategy):
    """
    Detects Doji Candles
    Body is very small relative to total range (< 10%)
    """
    
    def __init__(self):
        super().__init__("Doji Detector", "Detects indecision candles (Dojies)")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        signals = []
        recent_df = df.iloc[-3:] # Check last 3 candles
        
        for i, row in recent_df.iterrows():
            body_size = abs(row['close'] - row['open'])
            total_range = row['high'] - row['low']
            
            if total_range == 0:
                continue
                
            # Doji Definition: Body is < 15% of range (increased sensitivity)
            is_doji = (body_size / total_range) < 0.15
            
            if is_doji:
                signals.append({
                    "strategy": self.name,
                    "signal": "NEUTRAL",
                    "pattern": "Doji",
                    "price": row['close'],
                    "timestamp": i,
                    "confidence": 0.6
                })
                
        return signals

class InsideBarStrategy(Strategy):
    """
    Detects Inside Bars
    Current High < Previous High AND Current Low > Previous Low
    """
    
    def __init__(self):
        super().__init__("Inside Bar", "Potential breakout setup (consolidation)")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        signals = []
        
        # We need at least 2 candles
        if len(df) < 2:
            return []
            
        # Calculate Previous High/Low
        df['prev_high'] = df['high'].shift(1)
        df['prev_low'] = df['low'].shift(1)
        
        # Inside Bar Logic: High < Prev High AND Low > Prev Low
        df['is_inside'] = (df['high'] < df['prev_high']) & (df['low'] > df['prev_low'])
        
        # Check last 3 candles only to report recent patterns
        recent_df = df.iloc[-3:]
        
        for i, row in recent_df.iterrows():
            if row['is_inside']:
                signals.append({
                    "strategy": self.name,
                    "signal": "NEUTRAL",
                    "pattern": "Inside Bar",
                    "price": row['close'],
                    "mother_bar_high": row['prev_high'],
                    "mother_bar_low": row['prev_low'],
                    "timestamp": i,
                    "confidence": 0.7
                })
                
        return signals

class DeadVolumeStrategy(Strategy):
    """
    Detects Dead Volume (Dry up)
    Volume is < 50% of 20-period average volume
    """
    
    def __init__(self):
        super().__init__("Dead Volume", "Volume dry up indicating potential big move")
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        signals = []
        
        # Calculate Volume MA
        df['vol_ma_20'] = df['volume'].rolling(window=20).mean()
        
        if len(df) < 20: 
            return []
            
        recent_df = df.iloc[-3:]
        
        for i, row in recent_df.iterrows():
            if pd.isna(row['vol_ma_20']) or row['vol_ma_20'] == 0:
                continue
                
            # Logic: Current volume < 50% of average
            is_dead = row['volume'] < (0.5 * row['vol_ma_20'])
            
            if is_dead:
                signals.append({
                    "strategy": self.name,
                    "signal": "NEUTRAL",
                    "pattern": "Dead Volume",
                    "price": row['close'],
                    "volume": row['volume'],
                    "avg_volume": row['vol_ma_20'],
                    "timestamp": i,
                    "confidence": 0.65
                })
                
        return signals

class AdvancedPatternsStrategy(Strategy):
    """
    Wraps the PatternDetector to find VCP, IPO Bases, Rocket Bases, etc.
    """
    
    def __init__(self):
        super().__init__("Advanced Patterns", "Detects VCP, IPB, Rocket Base, etc.")
        from backend.strategy.pattern_detector import PatternDetector
        self.detector = PatternDetector()
    
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.validate_data(df):
            return []
            
        # Get all patterns from detector
        # We pass a dummy symbol here
        analysis = self.detector.analyze(df, "TEMP")
        
        signals = []
        for pattern in analysis.get('patterns', []):
            signals.append({
                "strategy": self.name,
                "signal": "BUY",  # Advanced patterns are usually bullish
                "pattern": pattern['type'],
                "price": df['close'].iloc[-1],
                "timestamp": df.index[-1],
                "confidence": pattern.get('confidence', 0.8)
            })
            
        return signals
