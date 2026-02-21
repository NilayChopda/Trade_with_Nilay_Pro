
import pandas as pd
import numpy as np

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(df, period):
    return df['Close'].ewm(span=period, adjust=False).mean()

def calculate_wma(df, period):
    weights = np.arange(1, period + 1)
    return df['Close'].rolling(window=period).apply(lambda x: np.sum(weights * x) / weights.sum(), raw=True)

def detect_patterns(df):
    """Detects candlestick patterns in the last 2 bars."""
    if len(df) < 5:
        return []

    patterns = []
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Body and Wick calculations
    curr_body = abs(curr['Close'] - curr['Open'])
    curr_range = curr['High'] - curr['Low']
    curr_upper_wick = curr['High'] - max(curr['Open'], curr['Close'])
    curr_lower_wick = min(curr['Open'], curr['Close']) - curr['Low']
    
    prev_body = abs(prev['Close'] - prev['Open'])
    
    # 1. Doji
    if curr_range > 0 and curr_body / curr_range < 0.1:
        patterns.append("Doji")
        
    # 2. Hammer (Bullish)
    if curr_range > 0 and curr_lower_wick > (2 * curr_body) and curr_upper_wick < (0.1 * curr_range):
        patterns.append("Hammer")
        
    # 3. Engulfing (Bullish)
    if curr['Close'] > curr['Open'] and prev['Close'] < prev['Open']:
        if curr['Close'] > prev['Open'] and curr['Open'] < prev['Close']:
            patterns.append("Bullish Engulfing")
            
    # 4. Inside Bar
    if curr['High'] <= prev['High'] and curr['Low'] >= prev['Low']:
        patterns.append("Inside Bar")
        
    return patterns

def detect_ema_cross(df):
    """Detects EMA crosses (9, 20, 50, 200)."""
    if len(df) < 200:
        return []
    
    ema9 = calculate_ema(df, 9)
    ema20 = calculate_ema(df, 20)
    ema50 = calculate_ema(df, 50)
    ema200 = calculate_ema(df, 200)
    
    signals = []
    
    # Golden Cross
    if ema50.iloc[-2] < ema200.iloc[-2] and ema50.iloc[-1] > ema200.iloc[-1]:
        signals.append("Golden Cross (50/200)")
        
    # Short term cross
    if ema9.iloc[-2] < ema200.iloc[-2] and ema9.iloc[-1] > ema200.iloc[-1]:
        signals.append("EMA 9 Cross 200")
        
    if ema20.iloc[-2] < ema50.iloc[-2] and ema20.iloc[-1] > ema50.iloc[-1]:
        signals.append("EMA 20 Cross 50")
        
    return signals

def get_technical_summary(df):
    """Returns combined patterns and indicator status."""
    if df.empty:
        return {"patterns": [], "signals": [], "trend": "Unknown"}
    
    patterns = detect_patterns(df)
    signals = detect_ema_cross(df)
    
    ema200 = calculate_ema(df, 200).iloc[-1]
    curr_price = df['Close'].iloc[-1]
    trend = "Bullish" if curr_price > ema200 else "Bearish"
    
    return {
        "patterns": patterns,
        "signals": signals,
        "trend": trend,
        "ema200": round(ema200, 2)
    }
