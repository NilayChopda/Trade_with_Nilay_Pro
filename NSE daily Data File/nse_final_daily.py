"""
FINAL NSE DAILY UPDATER - Uses REAL 2773 stocks
"""
import pandas as pd
import requests
import os
from datetime import datetime

BASE_PATH = r"G:\My Drive\Trade_with_Nilay\NSE daily Data File"

def fetch_daily_nse():
    print(f"\n📅 NSE DAILY UPDATE - {datetime.now()}")
    print("=" * 50)
    
    # Use the SAME code as nse_real_all.py
    url = "https://scanner.tradingview.com/india/scan"
    payload = {
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "NSE"},
            {"left": "type", "operation": "in_range", "right": ["stock", "dr"]}
        ],
        "options": {"lang": "en"},
        "markets": ["india"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "description", "close", "volume"],
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 4000]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        data = response.json()
        
        stocks = []
        seen = set()
        
        for item in data.get('data', []):
            symbol_full = item.get('s', '')
            if 'NSE:' in symbol_full:
                symbol = symbol_full.split(':')[-1]
                
                # Skip bonds/futures
                if (len(symbol) <= 5 and symbol[:2].isdigit()) or '-' in symbol:
                    continue
                    
                if symbol not in seen:
                    seen.add(symbol)
                    d = item.get('d', [])
                    if len(d) >= 2:
                        stocks.append({
                            'SYMBOL': symbol,
                            'NAME': d[0],
                            'CLOSE': d[2] if len(d) > 2 else 0,
                            'VOLUME': d[3] if len(d) > 3 else 0,
                            'UPDATE_DATE': datetime.now().strftime('%Y-%m-%d'),
                            'UPDATE_TIME': datetime.now().strftime('%H:%M:%S')
                        })
        
        df = pd.DataFrame(stocks)
        
        # Save files
        os.makedirs('daily_final_backups', exist_ok=True)
        today = datetime.now().strftime('%Y%m%d')
        
        # 1. Daily backup
        df.to_csv(f'daily_final_backups/nse_{today}.csv', index=False)
        
        # 2. Current for scanner
        df.to_csv('nse_scanner_current.csv', index=False)
        
        # 3. Just symbols
        with open('nse_scanner_symbols.txt', 'w') as f:
            for symbol in df['SYMBOL']:
                f.write(f"{symbol}\n")
        
        print(f"✅ UPDATED: {len(df)} NSE stocks")
        print(f"📁 Current: nse_scanner_current.csv")
        print(f"📁 Symbols: nse_scanner_symbols.txt")
        print(f"📁 Backup: daily_final_backups/nse_{today}.csv")
        
        # Log
        with open('nse_update_log.txt', 'a') as f:
            f.write(f"{datetime.now()}: Updated {len(df)} stocks\n")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Fallback: Use existing file
        if os.path.exists('nse_full_current.csv'):
            df = pd.read_csv('nse_full_current.csv')
            df['UPDATE_DATE'] = datetime.now().strftime('%Y-%m-%d')
            df['UPDATE_TIME'] = datetime.now().strftime('%H:%M:%S')
            df.to_csv('nse_scanner_current.csv', index=False)
            print(f"⚠️ Using cached data: {len(df)} stocks")
            return df
        return None

if __name__ == "__main__":
    fetch_daily_nse()