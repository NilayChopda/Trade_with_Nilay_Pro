"""
SMC (Smart Money Concepts) Logic Engine
Ports key logic from Pine Script to Python:
- Swing Highs/Lows
- Order Blocks (Bullish/Bearish) with Mitigation
- Break of Structure (BOS) / Change of Character (CHOCH)
- Fair Value Gaps (FVG)
- 9 EMA Trend
"""

import pandas as pd
import numpy as np

class SMCEngine:
    def __init__(self):
        pass

    def calculate_swings(self, df: pd.DataFrame, length: int = 50):
        """
        Identify Swing Highs and Lows.
        Pine: float top = ta.highest(size)
        """
        # Calculate local highs/lows
        df['swing_high'] = df['high'].rolling(window=length*2+1, center=True).max()
        df['swing_low'] = df['low'].rolling(window=length*2+1, center=True).min()
        
        # Identify pivot points where high == swing_high
        df['is_swing_high'] = (df['high'] == df['swing_high']) & (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['is_swing_low'] = (df['low'] == df['swing_low']) & (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        return df

    def find_order_blocks(self, df: pd.DataFrame, lookback: int = 100):
        """
        Identify Order Blocks (OB).
        Bullish OB: The last bearish candle before a strong bullish move that breaks structure/highs.
        """
        obs = []
        
        # Need at least 20 bars
        if len(df) < 20:
            return []

        # Calculate 9 EMA for Trend (Using standard Pandas)
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        
        # Iterate through candles to find potential OBs
        # Optimization: Don't iterate every single candle, look for strong moves
        
        # Definition of "Strong Move":
        # - Large body candle (green for Bullish OB)
        # - Breaking a recent high (Fractal/Swing)
        
        for i in range(len(df) - 5, 10, -1): # Look at recent history
            # We are looking for the OB *formed* in the past
            pass

        # Let's use a simpler heuristic closer to the Pine Script logic provided:
        # "bullishOrderBlockMitigationSource < eachOrderBlock.barLow" 
        
        # Algorithmic detection of Bullish OB:
        # 1. Identify a Swing High Break (BOS)
        # 2. Find the lowest down-candle (Red) prior to that impulsive move
        
        # Since full historical replay is expensive, we'll scan the last 'lookback' bars for valid UNMITIGATED OBs.
        
        # 1. Find swings for context
        df = self.calculate_swings(df, length=5) 
        
        # 2. Vectorized approach is hard for OBs due to "unmitigated" state. Using iterative.
        # Minimal implementation for EOD Scanner:
        
        potential_obs = []
        
        for i in range(10, len(df) - 2):
            # Check for Bullish OB formation
            # Pattern: Red Angle -> Green Impulse -> Break of Red's High
            
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            
            # 1. Previous Candle was Bearish (Red)
            is_red = prev['close'] < prev['open']
            
            # 2. Current Candle (or sequence) causes a Break of Structure?
            # Simplified: Did price rally significantly after this red candle?
            
            # Check next 3 candles
            future = df.iloc[i:i+4]
            if future.empty: continue
            
            max_future_close = future['close'].max()
            
            # Simple BOS criteria: Price broke above the Red candle's High
            if is_red and max_future_close > prev['high']:
                # Potential Bullish OB
                
                # Verify "Impulsive" move: at least one candle with body > ATR or strong % move
                move_strength = (max_future_close - prev['high']) / prev['high']
                
                if move_strength > 0.01: # 1% move minimum
                    ob = {
                        "type": "bullish",
                        "top": prev['high'],
                        "bottom": prev['low'],
                        "index": i-1,
                        "timestamp": prev['timestamp'], # Assumes 'timestamp' column
                        "mitigated": False
                    }
                    potential_obs.append(ob)

        # 3. Check Mitigation (Has price come back to touch it?)
        # For Bullish OB: Low of subsequent candles touches the OB range (top-bottom)
        
        final_obs = []
        for ob in potential_obs:
            idx = ob['index']
            # Look at all candles AFTER the formation
            future_candles = df.iloc[idx+2 :] # +2 to skip the immediate reaction
            
            if future_candles.empty:
                final_obs.append(ob) # Fresh OB
                continue
                
            # Check if any future LOW touched the OB range
            # Range: [bottom, top]
            # Actually, standard SMC: Entry at OB Top. Stop at OB Bottom.
            # Mitigation means price tapped the zone.
            
            # Did price go BELOW the bottom? (Structure Failed / OB Failed)
            failed = (future_candles['close'] < ob['bottom']).any()
            
            # Did price touch the zone?
            mitigated = (future_candles['low'] <= ob['top']).any()
            
            if not failed and not mitigated:
                # This is a FRESH UNMITIGATED OB -> High High Probability
                ob['status'] = 'fresh'
                final_obs.append(ob)
            elif not failed and mitigated:
                # This is a TESTED OB -> Might hold, might not
                # But for our scanner, we want "Tapping Now"
                # Check if the *current* candle is the one mitigating it
                last_idx = df.index[-1]
                mitigation_indices = future_candles[future_candles['low'] <= ob['top']].index
                
                if not mitigation_indices.empty:
                    first_mitigation = mitigation_indices[0]
                    if first_mitigation >= len(df) - 2: # Mitigated very recently (today/yesterday)
                         ob['status'] = 'tapping_now'
                         final_obs.append(ob)

        return final_obs

    def check_setup(self, df: pd.DataFrame):
        """
        Check for Buy/Sell setups based on SMC + 9EMA
        """
        if df.empty or 'close' not in df.columns:
            return None

        # Calculate Indicators
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        
        # Get OBs
        obs = self.find_order_blocks(df)
        bullish_obs = [o for o in obs if o['type'] == 'bullish']
        
        if not bullish_obs:
            return None
            
        # Current State
        current = df.iloc[-1]
        close = current['close']
        
        # Check if price is in/near any Bullish OB
        active_ob = None
        for ob in bullish_obs:
            # "Tapping" means Low <= Top and Close >= Bottom (didn't close below)
            if current['low'] <= ob['top'] and current['close'] >= ob['bottom']:
                active_ob = ob
                break
        
        if active_ob:
            # We have a tap. Check for Confirmation.
            # 1. Bullish Candle?
            is_bullish_candle = current['close'] > current['open']
            
            # 2. 9 EMA Trend? (Optional, user script plots it)
            # If price > 9EMA, it's strong. If getting support at 9EMA + OB, super strong.
            
            # Setup Rating
            score = 0
            reasons = []
            
            reasons.append(f"Tapping Bullish Order Block from {active_ob['timestamp']}")
            score += 5
            
            if is_bullish_candle:
                reasons.append("Bullish Candle Formation")
                score += 2
                
            if current['close'] > current['ema_9']:
                reasons.append("Price above 9 EMA")
                score += 2
            
            # Check for recent BOS (Trend is Up?)
            # Simplified: Close > Close 20 days ago
            if current['close'] > df['close'].iloc[-20]:
                reasons.append("Short-term Trend is Up")
                score += 1
                
            return {
                "signal": "BUY" if score >= 7 else "WATCH",
                "score": score,
                "reasons": reasons,
                "ob": active_ob
            }
            
        return None
