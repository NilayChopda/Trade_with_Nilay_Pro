import pandas as pd
import numpy as np
# import pandas_ta as ta # Removing external dependency

class Indicators:
    @staticmethod
    def calculate_wma(series, length):
        """
        Calculates Weighted Moving Average using numpy.
        """
        weights = np.arange(1, length + 1)
        # Using pandas rolling apply
        f = lambda x: np.dot(x, weights) / weights.sum()
        return series.rolling(window=length).apply(f, raw=True)

    @staticmethod
    def process_data(data_dict):
        """
        Takes a dictionary of DFs (daily, weekly, monthly) and calculates required indicators.
        Returns a single object/dict with the latest values for scanning.
        """
        results = {}
        
        # 1. Process Update: Ensure we have data
        if not data_dict or 'daily' not in data_dict or data_dict['daily'] is None:
            return None

        daily = data_dict['daily'].copy()
        weekly = data_dict['weekly'].copy()
        monthly = data_dict['monthly'].copy()
        
        # --- Daily Indicators ---
        # Daily WMA(close, 1) is just the Close price
        daily['wma1'] = daily['close']
        
        # Historical Daily WMAs
        daily['wma12'] = Indicators.calculate_wma(daily['close'], length=12)
        daily['wma20'] = Indicators.calculate_wma(daily['close'], length=20)
        
        # Shifted values
        # "4 days ago" means shift(4)
        daily['wma12_4_ago'] = daily['wma12'].shift(4)
        
        # "2 days ago" means shift(2)
        daily['wma20_2_ago'] = daily['wma20'].shift(2)
        
        # Get latest Daily values
        last_daily = daily.iloc[-1]
        prev_daily = daily.iloc[-2] if len(daily) > 1 else None
        
        # --- Weekly Indicators ---
        if weekly is not None and not weekly.empty:
            weekly['wma6'] = Indicators.calculate_wma(weekly['close'], length=6)
            weekly['wma12'] = Indicators.calculate_wma(weekly['close'], length=12)
            last_weekly = weekly.iloc[-1]
        else:
            last_weekly = pd.Series()

        # --- Monthly Indicators ---
        if monthly is not None and not monthly.empty:
            monthly['wma2'] = Indicators.calculate_wma(monthly['close'], length=2)
            monthly['wma4'] = Indicators.calculate_wma(monthly['close'], length=4)
            last_monthly = monthly.iloc[-1]
        else:
            last_monthly = pd.Series()
            
        # Combine into a result object
        results['symbol'] = daily.index.name # or assume passed separately
        results['close'] = last_daily['close']
        results['volume'] = last_daily['volume']
        
        # Calculate Percent Change
        if prev_daily is not None:
            results['pct_change'] = ( (last_daily['close'] - prev_daily['close']) / prev_daily['close'] ) * 100
        else:
            results['pct_change'] = 0.0
        
        # Condition 1: Daily Wma(1) > Monthly Wma(2) + 1
        results['d_wma1'] = last_daily['wma1']
        results['m_wma2'] = last_monthly.get('wma2', 0)
        
        # Condition 2: Monthly Wma(2) > Monthly Wma(4) + 2
        results['m_wma4'] = last_monthly.get('wma4', 0)
        
        # Condition 3: Daily Wma(1) > Weekly Wma(6) + 2
        results['w_wma6'] = last_weekly.get('wma6', 0)
        
        # Condition 4: Weekly Wma(6) > Weekly Wma(12) + 2
        results['w_wma12'] = last_weekly.get('wma12', 0)
        
        # Condition 5: Daily Wma(1) > 4 days ago Wma(12) + 2
        results['d_wma12_4_ago'] = last_daily['wma12_4_ago']
        
        # Condition 6: Daily Wma(1) > 2 days ago Wma(20) + 2
        results['d_wma20_2_ago'] = last_daily['wma20_2_ago']
        
        return results

    @staticmethod
    def check_conditions(metrics):
        """
        Checks the 7 conditions + Post Filter.
        Returns True/False and the metrics.
        """
        if not metrics:
            return False
            
        try:
            # logic from screenshot/text
            
            # 1. Daily WMA(1) > Monthly WMA(2) + 1
            c1 = metrics['d_wma1'] > (metrics['m_wma2'] + 1)
            
            # 2. Monthly WMA(2) > Monthly WMA(4) + 2
            c2 = metrics['m_wma2'] > (metrics['m_wma4'] + 2)
            
            # 3. Daily WMA(1) > Weekly WMA(6) + 2
            c3 = metrics['d_wma1'] > (metrics['w_wma6'] + 2)
            
            # 4. Weekly WMA(6) > Weekly WMA(12) + 2
            c4 = metrics['w_wma6'] > (metrics['w_wma12'] + 2)
            
            # 5. Daily Wma(1) > 4 days ago Wma(12) + 2
            c5 = metrics['d_wma1'] > (metrics['d_wma12_4_ago'] + 2)
            
            # 6. Daily Wma(1) > 2 days ago Wma(20) + 2
            c6 = metrics['d_wma1'] > (metrics['d_wma20_2_ago'] + 2)
            
            # 7. Daily Close > 20
            c7 = metrics['close'] > 20
            
            # Combine
            passed_scan = c1 and c2 and c3 and c4 and c5 and c6 and c7
            
            if passed_scan:
                # POST FILTER: Price change between -1% and +2%
                pct = metrics.get('pct_change', 0)
                if not (-1 <= pct <= 2):
                    passed_scan = False
            
            return passed_scan
            
        except Exception as e:
            # Missing data or nan
            return False
