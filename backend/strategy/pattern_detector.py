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
    
    def analyze(self, df: pd.DataFrame, symbol: str, nifty_df: pd.DataFrame = None) -> Dict:
        """
        Analyze price data and detect all patterns
        
        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume
            symbol: Stock symbol
            nifty_df: Optional Nifty 50 historical data for RS calculation
            
        Returns:
            Dict with detected patterns and confidence scores
        """
        if df.empty or len(df) < 20:
            return {"symbol": symbol, "patterns": [], "primary_pattern": None}
        
        patterns_found = []
        
        # Detect each pattern type and add a human-readable note
        if self.is_breakout(df):
            patterns_found.append({
                "type": "BREAKOUT",
                "confidence": self.breakout_confidence(df),
                "note": "Price moved above 20‑day high with volume confirmation"
            })
        
        if self.is_order_block(df):
            patterns_found.append({
                "type": "ORDER_BLOCK",
                "confidence": self.order_block_confidence(df),
                "note": "Bullish rally after a bearish candle indicates institutional order block"
            })
        
        support, resistance = self.find_support_resistance(df)
        if support or resistance:
            patterns_found.append({
                "type": "SUPPORT_RESISTANCE",
                "confidence": 0.8,
                "support": support,
                "resistance": resistance,
                "note": "Defined support/resistance levels with multiple touches"
            })
        
        if self.is_consolidation(df):
            # treat tight-range consolidation as box/tight zone as well
            patterns_found.append({
                "type": "CONSOLIDATION",
                "confidence": self.consolidation_confidence(df),
                "note": "Tight 10‑day range (<3%) signalling a box/tight zone setup"
            })
            patterns_found.append({
                "type": "BOX",
                "confidence": self.consolidation_confidence(df),
                "note": "Alias for consolidation; useful for UI/filters"
            })

        if self.is_vcp(df):
            patterns_found.append({
                "type": "VCP",
                "confidence": self.vcp_confidence(df),
                "note": "Volatility contraction pattern with shrinking drops and volume dry‑up"
            })

        if self.is_ipo_base(df):
            patterns_found.append({"type": "IPO_BASE", "confidence": 0.8})

        if self.is_rocket_base(df):
            patterns_found.append({"type": "ROCKET_BASE", "confidence": 0.85})

        if self.is_high_tight_flag(df):
            patterns_found.append({
                "type": "HIGH_TIGHT_FLAG", 
                "confidence": 0.9,
                "note": "Explosive 100%+ move followed by ultra-tight consolidation"
            })
            
        if self.is_blue_sky_breakout(df):
            patterns_found.append({
                "type": "BLUE_SKY",
                "confidence": 0.95,
                "note": "Price at All-Time High (ATH) with no overhead resistance"
            })

        if self.is_volume_surge(df):
            patterns_found.append({"type": "VOLUME_SURGE", "confidence": self.volume_surge_confidence(df)})
        
        # Relative Strength (RS) vs Nifty
        rs_score = 0
        if nifty_df is not None and not nifty_df.empty:
            rs_score = self.calculate_rs_score(df, nifty_df)
            if rs_score > 90:
                patterns_found.append({
                    "type": "HIGH_RS", 
                    "confidence": rs_score/100, 
                    "note": f"Strong Relative Strength ({rs_score}) vs Nifty 50"
                })
        
        # Determine primary pattern (highest confidence)
        primary = max(patterns_found, key=lambda x: x['confidence']) if patterns_found else None
        
        # detect last candle shape
        candlestick = self.detect_candlestick(df)

        # compute simple breakout target for box/consolidation/cup patterns
        target = None
        target_pct = None
        if primary and primary['type'] in ("CONSOLIDATION", "BOX", "VCP", "BREAKOUT", "CUP", "SUPPORT_RESISTANCE", "ORDER_BLOCK"):
            # use support/resistance levels to estimate height
            sup, res = self.find_support_resistance(df)
            if sup and res:
                height = res - sup
                current = df['close'].iloc[-1]
                tgt = current + height
                target = round(tgt, 2)
                if current > 0:
                    target_pct = round(((tgt - current) / current) * 100, 2)

        return {
            "symbol": symbol,
            "patterns": patterns_found,
            "primary_pattern": primary['type'] if primary else None,
            "confidence": primary['confidence'] if primary else 0,
            "candlestick": candlestick,
            "target": target,
            "target_pct": target_pct,
            "rs_score": rs_score
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
            "CONSOLIDATION": "#6B7280",  # Gray
            "VCP": "#F43F5E",  # Rose
            "IPO_BASE": "#8B5CF6",  # Violet
            "ROCKET_BASE": "#EC4899",  # Pink
            "VOLUME_SURGE": "#EAB308", # Yellow
            "HIGH_RS": "#8B5CF6",     # Violet
            "HIGH_TIGHT_FLAG": "#D946EF", # Fuchsia
            "BLUE_SKY": "#0EA5E9"      # Sky Blue
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


    def is_ipo_base(self, df: pd.DataFrame) -> bool:
        """
        Detect IPO Base / Recent Listing Accumulation
        Logic:
        1. Stock is relatively new (last 2-3 years)
        2. Forming a base (Stage 1 consolidation)
        3. Breakout or tightening near pivot
        """
        # Recent listings: Up to 750 trading days (~3 years)
        if len(df) > 750 or len(df) < 15:
            return False
            
        # Check for recovery if it dropped after IPO
        # Or consolidation near ATH
        ath = df['high'].max()
        current_close = df['close'].iloc[-1]
        
        # 1. High-Tight-Flag or Consolidation near Highs (within 10%)
        near_high = current_close >= ath * 0.90
        
        # 2. Tightness (Volatility contraction)
        recent = df.tail(15)
        tightness = (recent['high'].max() - recent['low'].min()) / recent['low'].min()
        is_tight = tightness < 0.12 # 12% range in 15 days
        
        # 3. Volume Drying up (Dry up before breakout)
        avg_vol = df['volume'].tail(30).mean()
        recent_vol = df['volume'].tail(5).mean()
        vol_dry = recent_vol < avg_vol * 0.8
        
        return is_tight and (near_high or vol_dry)

    def is_vcp(self, df: pd.DataFrame) -> bool:
        """
        Refined VCP (Volatility Contraction Pattern) Detection
        Logic:
        1. Uptrend check (Stage 2)
        2. Shrinking drops (T1 > T2 > T3)
        3. Volume dry-up at right side
        """
        if len(df) < 150:
            return False
            
        close = df['close']
        ema_50 = close.ewm(span=50).mean()
        ema_200 = close.ewm(span=200).mean()
        curr_price = close.iloc[-1]
        
        # 1. Base Trend
        in_uptrend = curr_price > ema_50.iloc[-1] > ema_200.iloc[-1] and ema_200.iloc[-1] > ema_200.iloc[-20]
        if not in_uptrend:
            return False

        # 2. Measure Contractions (looking for tightening)
        # We look at the last 3 swing high-to-low drops
        recent_60 = df.tail(60)
        highs = recent_60['high'].values
        lows = recent_60['low'].values
        
        # Simple drop measure over 3 windows
        drops = []
        for i in range(3):
            # Window size decreases as we move right
            start, end = i*20, (i+1)*20
            w_high = highs[start:end].max()
            w_low = lows[start:end].min()
            drops.append((w_high - w_low) / w_high)
            
        # VCP requirement: drops must be decreasing (e.g. 15% -> 8% -> 4%)
        is_tightening = drops[0] > drops[1] and drops[1] > drops[2]
        is_ultra_tight = drops[2] < 0.05 # Last contraction < 5%
        
        # 3. Volume dry-up (last 5 days vol < 70% of 50d avg)
        avg_vol = df['volume'].tail(50).mean()
        recent_vol = df['volume'].tail(5).mean()
        vol_dry = recent_vol < avg_vol * 0.7
        
        return in_uptrend and is_tightening and (is_ultra_tight or vol_dry)

    def calculate_rs_score(self, stock_df: pd.DataFrame, nifty_df: pd.DataFrame) -> float:
        """Calculate Relative Strength Score (0-100) vs Nifty 50"""
        try:
            # Align dates
            common_dates = stock_df.index.intersection(nifty_df.index)
            if len(common_dates) < 60:
                return 0
                
            s_close = stock_df.loc[common_dates, 'close']
            n_close = nifty_df.loc[common_dates, 'close']
            
            # RS Line = Stock Price / Nifty Price
            rs_line = s_close / n_close
            
            # 3-month RS Rating (Weighted)
            # Recent performance weighted higher
            rs_change = rs_line.pct_change(20).tail(60)
            weights = np.linspace(0.5, 1.0, len(rs_change))
            score = (rs_change * weights).sum() * 1000
            
            return round(min(99, max(1, 50 + score)), 2)
        except:
            return 0

    def is_rocket_base(self, df: pd.DataFrame) -> bool:
        """
        Detect Rocket Base pattern
        Logic:
        1. Strong rally (e.g., > 20% in last 20 days)
        2. Tight consolidation (base) in last 5-10 days
        """
        if len(df) < 30:
            return False
            
        # 1. Strong Rally check
        start_price = df['close'].iloc[-30]
        peak_price = df['high'].iloc[-10:].max()
        rally_pct = (peak_price - start_price) / start_price
        
        if rally_pct < 0.20:
            return False
            
        # 2. Tight Base check (last 7 days range < 6%)
        recent = df.tail(7)
        price_range = (recent['high'].max() - recent['low'].min()) / recent['low'].min()
        
        return price_range < 0.06

    def is_volume_surge(self, df: pd.DataFrame) -> bool:
        """Detect significant volume surge"""
        if len(df) < 21:
            return False
            
        avg_vol = df['volume'].iloc[-21:-1].mean()
        curr_vol = df['volume'].iloc[-1]
        
        return curr_vol > (avg_vol * 2.5)

    def volume_surge_confidence(self, df: pd.DataFrame) -> float:
        avg_vol = df['volume'].iloc[-21:-1].mean()
        curr_vol = df['volume'].iloc[-1]
        ratio = curr_vol / avg_vol
        return min(1.0, ratio / 5.0)

    def is_high_tight_flag(self, df: pd.DataFrame) -> bool:
        """
        Detect High Tight Flag (HTF)
        1. 100%+ move in < 8 weeks (40 trading days)
        2. Consolidation < 25% deep
        3. Tightness in last 10 days
        """
        if len(df) < 40:
            return False
            
        # 1. 100% Move
        low_40d = df['low'].tail(40).min()
        high_40d = df['high'].tail(40).max()
        move_pct = (high_40d - low_40d) / low_40d
        
        if move_pct < 1.0: # 100% minimum
            return False
            
        # 2. Shallow consolidation (not dropped more than 25% from high)
        curr_price = df['close'].iloc[-1]
        dist_from_high = (high_40d - curr_price) / high_40d
        
        if dist_from_high > 0.25:
            return False
            
        # 3. Tightness (last 10 days range < 12%)
        recent_10 = df.tail(10)
        range_10 = (recent_10['high'].max() - recent_10['low'].min()) / recent_10['low'].min()
        
        return range_10 < 0.12

    def is_blue_sky_breakout(self, df: pd.DataFrame) -> bool:
        """
        Detect Blue Sky Breakout (All-Time High / Multi-year High)
        """
        if len(df) < 250:
            return False
            
        curr_price = df['close'].iloc[-1]
        ath = df['high'].max()
        
        # Within 2% of ATH or breaking above
        return curr_price >= ath * 0.98

    # --- Candlestick helpers ---
    def detect_candlestick(self, df: pd.DataFrame) -> str:
        """Return simple candlestick pattern name for the last candle."""
        if df.empty or len(df) < 2:
            return None
        last = df.iloc[-1]
        prev = df.iloc[-2]

        body = abs(last['close'] - last['open'])
        lower_shadow = last['open'] - last['low'] if last['close'] >= last['open'] else last['close'] - last['low']
        upper_shadow = last['high'] - last['close'] if last['close'] >= last['open'] else last['high'] - last['open']

        # Bullish Engulfing
        if last['close'] > last['open'] and prev['close'] < prev['open']:
            if last['open'] <= prev['close'] and last['close'] >= prev['open']:
                return "Bullish Engulfing"

        # Bearish Engulfing
        if last['close'] < last['open'] and prev['close'] > prev['open']:
            if last['open'] >= prev['close'] and last['close'] <= prev['open']:
                return "Bearish Engulfing"

        # Hammer (small body near high, long lower shadow)
        if body < (last['high'] - last['low']) * 0.3 and lower_shadow > body * 2 and upper_shadow < body:
            if last['close'] > last['open']:
                return "Hammer"
            else:
                return "Hanging Man"

        # Doji
        if body < (last['high'] - last['low']) * 0.1:
            return "Doji"

        # Bullish Harami (Large bearish candle followed by small bullish candle inside the body)
        if prev['close'] < prev['open'] and last['close'] > last['open']:
            if last['open'] > prev['close'] and last['close'] < prev['open']:
                if (prev['open'] - prev['close']) > (last['close'] - last['open']) * 2:
                    return "Bullish Harami"

        # Inside Bar (Last candle's high/low are dentro the previous candle's high/low)
        if last['high'] < prev['high'] and last['low'] > prev['low']:
            return "Inside Bar"

        return None

if __name__ == "__main__":
    pass
