
import os
import requests
import logging
import pandas as pd
import pandas as pd
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Kite API Key (provided by user)
KITE_API_KEY = os.environ.get("KITE_API_KEY", "927xjtvndq82vjc3")

class DataProvider:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def get_all_nse_symbols(self):
        """Fetches all listed equity symbols from NSE."""
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        try:
            df = pd.read_csv(url)
            # Standard NSE Equity list has 'SYMBOL' column
            symbols = df['SYMBOL'].tolist()
            logger.info(f"Fetched {len(symbols)} symbols from NSE.")
            return [s for s in symbols if isinstance(s, str)]
        except Exception as e:
            logger.error(f"Error fetching symbols from NSE: {e}")
            return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    def fetch_nse_quote(self, symbol):
        """Fetches live quote from Kite API."""
        try:
            from kite_provider import KiteProvider
            kp = KiteProvider()
            res = kp.get_live_quote(symbol)
            if res:
                return res
            
            # Fallback to nsepython only if Kite fails
            from nsepython import nse_quote
            quote = nse_quote(symbol)
            if quote:
                price = quote.get('priceInfo', {}).get('lastPrice', 0)
                change_pct = quote.get('priceInfo', {}).get('pChange', 0)
                return {
                    "symbol": symbol,
                    "price": float(price),
                    "change_pct": float(change_pct),
                    "volume": quote.get('marketDeptOrderBook', {}).get('tradeInfo', {}).get('totalTradedVolume', 0),
                    "source": "nsepython_fallback"
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching live quote for {symbol}: {e}")
            return None

    def fetch_batch_quotes(self, symbols):
        """Fetches multiple quotes in batch."""
        if not symbols:
            return []
        
        results = []
        # Kite has a limit on quote calls, but usually 500 symbols is fine
        for symbol in symbols:
            res = self.fetch_nse_quote(symbol)
            if res:
                results.append(res)
            # Small delay if using fallback to avoid rate limits
            if results and results[-1].get("source") == "nsepython_fallback":
                time.sleep(0.5)
            
        return results

    def get_historical_data(self, symbol, period="1y", interval="1d"):
        """Fetches historical data from local DB, Kite, or NSE."""
        try:
            # 1. Try local SQLite cache first (Official NSE Bhavcopy)
            from database import get_db
            with get_db() as conn:
                query = "SELECT * FROM historical_prices WHERE symbol = ? ORDER BY date ASC"
                df_local = pd.read_sql_query(query, conn, params=(symbol,))
                if not df_local.empty and len(df_local) > 50:
                    df_local['date'] = pd.to_datetime(df_local['date'])
                    df_local.set_index('date', inplace=True)
                    df_local.columns = [c.capitalize() for c in df_local.columns]
                    return df_local

            # 2. Try Kite API
            from kite_provider import KiteProvider
            api_key = os.environ.get("KITE_API_KEY")
            access_token = os.environ.get("KITE_ACCESS_TOKEN")

            if api_key and access_token:
                try:
                    kp = KiteProvider(api_key)
                    kp.set_access_token(access_token)
                    
                    # Special Case for NIFTY 50 index token
                    token = None
                    if symbol == "NIFTY 50":
                        token = 256265
                    
                    df_kite = kp.get_historical_data(symbol, days=365, token=token)
                    if not df_kite.empty:
                        return df_kite
                except Exception as e:
                    logger.debug(f"Kite historical fail for {symbol}: {e}")

            # 3. Robust Manual NSE Fetch (Fallback)
            import requests
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=" + symbol,
                "Accept": "*/*"
            })
            
            # Need to visit home page first for cookies
            session.get("https://www.nseindia.com", timeout=10)
            
            from datetime import datetime, timedelta
            from_date = (datetime.now() - timedelta(days=365)).strftime("%d-%m-%Y")
            to_date = datetime.now().strftime("%d-%m-%Y")
            
            # Using the official historical data API
            url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={from_date}&to={to_date}"
            
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data and data['data']:
                    df = pd.DataFrame(data['data'])
                    # Filter EQ series and map columns
                    df = df[df['CH_SERIES'] == 'EQ']
                    cols = {
                        'CH_CLOSING_PRICE': 'Close',
                        'CH_OPENING_PRICE': 'Open',
                        'CH_TRADE_HIGH_PRICE': 'High',
                        'CH_TRADE_LOW_PRICE': 'Low',
                        'CH_TOT_TRADED_QTY': 'Volume',
                        'CH_TIMESTAMP': 'Date'
                    }
                    df = df.rename(columns=cols)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    # Sort by date
                    df.sort_index(inplace=True)
                    return df[list(cols.values())[:-1]] # Return only OHLCV

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Global historical fetch error for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_corporate_announcements(self):
        """Fetches announcements from NSE unofficial endpoint."""
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        try:
            # NSE requires specific cookies/headers usually handled via session.get initial home page
            self.session.get("https://www.nseindia.com", timeout=5)
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.error(f"Announcement fetch error: {e}")
            return []

    def fetch_fii_dii_activity(self):
        """Fetches FII/DII activity summary from NSE."""
        try:
            from nsepython import nse_fii_dii
            data = nse_fii_dii()
            # Expecting a list of dicts, find the latest one
            if data and isinstance(data, list):
                latest = data[0] # Usually the most recent
                return {
                    "date": latest.get('date', datetime.now().strftime("%Y-%m-%d")),
                    "fii_net": float(latest.get('fiiNet', 0)),
                    "dii_net": float(latest.get('diiNet', 0)),
                    "status": "BULLISH" if float(latest.get('fiiNet', 0)) > 0 else "BEARISH"
                }
        except Exception as e:
            logger.error(f"FII/DII fetch error: {e}")
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "fii_net": 0,
            "dii_net": 0,
            "status": "NEUTRAL"
        }

if __name__ == "__main__":
    dp = DataProvider()
    print(dp.fetch_nse_quote("RELIANCE"))
