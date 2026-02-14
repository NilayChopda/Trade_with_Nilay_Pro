"""
SCANNER CORE - WMA Calculations
This will be the heart of your Chartink-like scanner
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class WMACalculator:
    """
    Calculates Weighted Moving Average (WMA)
    Formula: WMA = (P1*n + P2*(n-1) + ... + Pn*1) / (n*(n+1)/2)
    """
    
    @staticmethod
    def calculate_wma(prices, period):
        """
        Calculate WMA for given prices and period
        """
        if len(prices) < period:
            return np.nan
        
        weights = np.arange(1, period + 1)
        wma = np.sum(prices[-period:] * weights) / weights.sum()
        return round(wma, 2)
    
    @staticmethod
    def calculate_all_wmas(close_prices):
        """
        Calculate all WMAs needed for scanner logic
        Returns dict with all WMA values
        """
        # Need at least 20 days of data
        if len(close_prices) < 20:
            return None
        
        wmas = {
            # Your scanner conditions:
            # 1. Daily WMA(close, 1) > Monthly WMA(close, 2) + 1
            'daily_wma_1': WMACalculator.calculate_wma(close_prices, 1),
            
            # 2. Monthly WMA(close, 2) > Monthly WMA(close, 4) + 2
            'monthly_wma_2': WMACalculator.calculate_wma(close_prices, 2),
            'monthly_wma_4': WMACalculator.calculate_wma(close_prices, 4),
            
            # 3. Daily WMA(close, 1) > Weekly WMA(close, 6) + 2
            'weekly_wma_6': WMACalculator.calculate_wma(close_prices, 6),
            
            # 4. Weekly WMA(close, 6) > Weekly WMA(close, 12) + 2
            'weekly_wma_12': WMACalculator.calculate_wma(close_prices, 12),
            
            # 5. Daily WMA(close, 1) > WMA(close, 12) from 4 days ago + 2
            # Need to calculate WMA 12 using data from 4 days ago
            'wma_12_4days_ago': WMACalculator.calculate_wma(close_prices[:-4], 12) if len(close_prices) >= 16 else np.nan,
            
            # 6. Daily WMA(close, 1) > WMA(close, 20) from 2 days ago + 2
            'wma_20_2days_ago': WMACalculator.calculate_wma(close_prices[:-2], 20) if len(close_prices) >= 22 else np.nan,
            
            # Current close for condition 7: Daily Close > 20
            'current_close': close_prices[-1] if len(close_prices) > 0 else 0
        }
        
        return wmas
    
    @staticmethod
    def check_scanner_conditions(wmas):
        """
        Check all 7 scanner conditions
        Returns True if ALL conditions pass
        """
        if not wmas:
            return False
        
        conditions = [
            # 1. Daily WMA(close, 1) > Monthly WMA(close, 2) + 1
            wmas['daily_wma_1'] > (wmas['monthly_wma_2'] + 1),
            
            # 2. Monthly WMA(close, 2) > Monthly WMA(close, 4) + 2
            wmas['monthly_wma_2'] > (wmas['monthly_wma_4'] + 2),
            
            # 3. Daily WMA(close, 1) > Weekly WMA(close, 6) + 2
            wmas['daily_wma_1'] > (wmas['weekly_wma_6'] + 2),
            
            # 4. Weekly WMA(close, 6) > Weekly WMA(close, 12) + 2
            wmas['weekly_wma_6'] > (wmas['weekly_wma_12'] + 2),
            
            # 5. Daily WMA(close, 1) > WMA(close, 12) from 4 days ago + 2
            wmas['daily_wma_1'] > (wmas['wma_12_4days_ago'] + 2),
            
            # 6. Daily WMA(close, 1) > WMA(close, 20) from 2 days ago + 2
            wmas['daily_wma_1'] > (wmas['wma_20_2days_ago'] + 2),
            
            # 7. Daily Close > 20
            wmas['current_close'] > 20
        ]
        
        # All conditions must be True
        return all(conditions)

# TEST THE WMA CALCULATOR
if __name__ == "__main__":
    print("🧪 Testing WMA Calculator...")
    
    # Sample price data (20 days)
    sample_prices = [100, 102, 101, 105, 107, 110, 108, 112, 115, 118,
                     120, 122, 121, 119, 117, 120, 123, 125, 127, 130]
    
    calculator = WMACalculator()
    
    # Calculate WMAs
    wmas = calculator.calculate_all_wmas(sample_prices)
    
    if wmas:
        print("✅ WMA Calculation Successful!")
        print(f"Daily WMA(1): {wmas['daily_wma_1']}")
        print(f"Monthly WMA(2): {wmas['monthly_wma_2']}")
        print(f"Monthly WMA(4): {wmas['monthly_wma_4']}")
        print(f"Weekly WMA(6): {wmas['weekly_wma_6']}")
        print(f"Weekly WMA(12): {wmas['weekly_wma_12']}")
        
        # Check conditions
        passes = calculator.check_scanner_conditions(wmas)
        print(f"\n📊 Scanner Result: {'PASS' if passes else 'FAIL'}")
    else:
        print("❌ Need more price data")