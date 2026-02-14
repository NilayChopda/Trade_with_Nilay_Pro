"""
Pattern Detection Engine for Trade With Nilay
Identifies technical patterns: Breakout, Order Block, Support/Resistance, Consolidation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger("twn.pattern_detector")

class PatternDetector:
    """Detects technical patterns in stock price data"""
    
    def __init__(self):
        self.patterns = []
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Analyze price data and detect all patterns
        
        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume
            symbol: Stock symbol
            
        Returns:
            Dict with detected patterns and confidence scores
        """
        if df.empty or len(df) < 20:
            return {"symbol": symbol, "patterns": [], "primary_pattern": None}
        
        patterns_found = []
        
        # Detect each pattern type
        if self.is_breakout(df):
            patterns_found.append({"type": "BREAKOUT", "confidence": self.breakout_confidence(df)})
        
        if self.is_order_block(df):
            patterns_found.append({"type": "ORDER_BLOCK", "confidence": self.order_block_confidence(df)})
        
        support, resistance = self.find_support_resistance(df)
        if support or resistance:
            patterns_found.append({
                "type": "SUPPORT_RESISTANCE",
                "confidence": 0.8,
                "support": support,
                "resistance": resistance
            })
        
        if self.is_consolidation(df):
            patterns_found.append({"type": "CONSOLIDATION", "confidence": self.consolidation_confidence(df)})
        
        # Determine primary pattern (highest confidence)
        primary = max(patterns_found, key=lambda x: x['confidence']) if patterns_found else None
        
        return {
            "symbol": symbol,
            "patterns": patterns_found,
            "primary_pattern": primary['type'] if primary else None,
            "confidence": primary['confidence'] if primary else 0
        }
    
    def is_breakout(self, df: pd.DataFrame) -> bool:
        """
        Detect breakout pattern
        Current price > 20-day high with volume > 1.5x average
        """
        if len(df) < 20:
            return False
        
        current_price = df['close'].iloc[-1]
        high_20d = df['high'].iloc[-21:-1].max()  # Exclude current candle
        
        avg_volume = df['volume'].iloc[-21:-1].mean()
        current_volume = df['volume'].iloc[-1]
        
        return current_price > high_20d and current_volume > (avg_volume * 1.5)
    
    def breakout_confidence(self, df: pd.DataFrame) -> float:
        """Calculate breakout confidence score (0-1)"""
        current_price = df['close'].iloc[-1]
        high_20d = df['high'].iloc[-21:-1].max()
        
        # Higher breakout = higher confidence
        breakout_pct = ((current_price - high_20d) / high_20d) * 100
        
        # Volume confirmation
        avg_volume = df['volume'].iloc[-21:-1].mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        # Combine factors
        confidence = min(1.0, (breakout_pct * 10 + volume_ratio) / 3)
        return round(confidence, 2)
    
    def is_order_block(self, df: pd.DataFrame) -> bool:
        """
        Detect Order Block pattern
        Find last bearish candle before bullish rally
        """
        if len(df) < 10:
            return False
        
        # Look for bearish candle followed by bullish move
        for i in range(-10, -1):
            candle = df.iloc[i]
            next_candles = df.iloc[i+1:]
            
            # Bearish candle (close < open)
            if candle['close'] < candle['open']:
                # Check if followed by bullish rally (3+ green candles)
                green_candles = sum(next_candles['close'] > next_candles['open'])
                if green_candles >= 3:
                    return True
        
        return False
    
    def order_block_confidence(self, df: pd.DataFrame) -> float:
        """Calculate order block confidence"""
        # Simple confidence based on strength of rally after bearish candle
        recent_gain = ((df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]) * 100
        confidence = min(1.0, abs(recent_gain) / 5)  # 5% gain = 100% confidence
        return round(confidence, 2)
    
    def find_support_resistance(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Find support and resistance levels
        Returns: (support_price, resistance_price)
        """
        if len(df) < 20:
            return None, None
        
        # Use recent 20 candles
        recent = df.iloc[-20:]
        
        # Support: lowest low with multiple touches
        support = recent['low'].min()
        
        # Resistance: highest high with multiple touches
        resistance = recent['high'].max()
        
        # Validate with "touches" (price came within 1% of level)
        support_touches = sum(abs(recent['low'] - support) / support < 0.01)
        resistance_touches = sum(abs(recent['high'] - resistance) / resistance < 0.01)
        
        # Need at least 2 touches to be valid
        valid_support = support if support_touches >= 2 else None
        valid_resistance = resistance if resistance_touches >= 2 else None
        
        return valid_support, valid_resistance
    
    def is_consolidation(self, df: pd.DataFrame) -> bool:
        """
        Detect consolidation pattern
        Low volatility with tight price range
        """
        if len(df) < 10:
            return False
        
        recent = df.iloc[-10:]
        
        # Calculate Average True Range (ATR)
        high_low = recent['high'] - recent['low']
        high_close = abs(recent['high'] - recent['close'].shift(1))
        low_close = abs(recent['low'] - recent['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.mean()
        
        # Calculate price range
        price_range = recent['high'].max() - recent['low'].min()
        avg_price = recent['close'].mean()
        
        # Consolidation if range < 3% and low ATR
        range_pct = (price_range / avg_price) * 100
        
        return range_pct < 3 and atr < (avg_price * 0.02)
    
    def consolidation_confidence(self, df: pd.DataFrame) -> float:
        """Calculate consolidation confidence"""
        recent = df.iloc[-10:]
        price_range = recent['high'].max() - recent['low'].min()
        avg_price = recent['close'].mean()
        range_pct = (price_range / avg_price) * 100
        
        # Tighter range = higher confidence
        confidence = max(0, 1 - (range_pct / 3))
        return round(confidence, 2)
    
    def get_pattern_badge(self, pattern_type: str, confidence: float) -> str:
        """
        Get colored badge for pattern display
        
        Returns:
            HTML badge string
        """
        colors = {
            "BREAKOUT": "#10B981",  # Green
            "ORDER_BLOCK": "#3B82F6",  # Blue
            "SUPPORT_RESISTANCE": "#F59E0B",  # Orange
            "CONSOLIDATION": "#6B7280"  # Gray
        }
        
        color = colors.get(pattern_type, "#6B7280")
        
        # Confidence indicator
        if confidence >= 0.8:
            indicator = "🔥"
        elif confidence >= 0.6:
            indicator = "✅"
        else:
            indicator = "⚠️"
        
        return f"{indicator} {pattern_type}"


if __name__ == "__main__":
    # Test pattern detection
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    # Simulate breakout pattern
    prices = list(range(100, 120)) + [125, 130, 135, 140, 145, 150, 155, 160, 165, 170]
    volumes = [1000000] * 20 + [2000000] * 10
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 2 for p in prices],
        'low': [p - 2 for p in prices],
        'close': prices,
        'volume': volumes
    })
    
    detector = PatternDetector()
    result = detector.analyze(df, "TEST")
    
    print(f"Symbol: {result['symbol']}")
    print(f"Primary Pattern: {result['primary_pattern']}")
    print(f"Confidence: {result['confidence']}")
    print(f"All Patterns: {result['patterns']}")
