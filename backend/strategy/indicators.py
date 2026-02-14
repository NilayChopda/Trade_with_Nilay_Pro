"""
Technical Indicators Library
Helper functions for calculating common technical indicators on pandas DataFrame
"""

import pandas as pd
import numpy as np

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    return true_range.rolling(window=period).mean()

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price (daily reset)"""
    # Assuming dataframe is sorted by time
    q = df['volume'] * (df['high'] + df['low'] + df['close']) / 3
    return q.cumsum() / df['volume'].cumsum()

def find_pivot_highs(series: pd.Series, left: int = 2, right: int = 2) -> pd.Series:
    """Identify pivot highs (local maxima)"""
    # Rolling window logic: current must be >= neighbors
    # This is a simple implementation
    is_high = series.rolling(window=left+right+1, center=True).apply(
        lambda x: x[left] == max(x), raw=True
    )
    return is_high == 1.0

def find_pivot_lows(series: pd.Series, left: int = 2, right: int = 2) -> pd.Series:
    """Identify pivot lows (local minima)"""
    is_low = series.rolling(window=left+right+1, center=True).apply(
        lambda x: x[left] == min(x), raw=True
    )
    return is_low == 1.0
