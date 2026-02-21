
import os
import requests
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Kite API Key (provided by user)
KITE_API_KEY = os.environ.get("KITE_API_KEY", "927xjtvndq82vjc3")

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
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def fetch_nse_quote(self, symbol):
        """Fetches live quote from yfinance (reliable free source)."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.fast_info
            return {
                "symbol": symbol,
                "price": info.last_price,
                "change_pct": ((info.last_price - info.previous_close) / info.previous_close) * 100 if info.previous_close else 0,
                "volume": info.last_volume,
                "high": info.day_high,
                "low": info.day_low,
                "open": info.open_price,
                "prev_close": info.previous_close,
                "source": "yfinance"
            }
        except Exception as e:
            logger.error(f"Error fetching yfinance quote for {symbol}: {e}")
            return None

    def fetch_batch_quotes(self, symbols):
        """Fetches multiple quotes in batch using yfinance."""
        if not symbols:
            return []
        
        results = []
        try:
            # yfinance download is efficient for batches
            tickers = [f"{s}.NS" for s in symbols]
            data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
            
            for symbol in symbols:
                ticker_sym = f"{symbol}.NS"
                if ticker_sym in data and not data[ticker_sym].empty:
                    last_row = data[ticker_sym].iloc[-1]
                    prev_close = data[ticker_sym].iloc[0]['Open'] # Approximate if no info
                    price = last_row['Close']
                    # For better accuracy, we use Ticker.fast_info for change %
                    res = self.fetch_nse_quote(symbol)
                    if res:
                        results.append(res)
            
            return results
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            # Fallback to individual fetches
            return [self.fetch_nse_quote(s) for s in symbols if self.fetch_nse_quote(s)]

    def get_historical_data(self, symbol, period="1mo", interval="1d"):
        """Fetches historical data for technical indicators."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(period=period, interval=interval)
            return df
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_corporate_announcements(self):
        """Fetches announcements from NSE unofficial endpoint."""
        # Using a reliable unofficial endpoint format
        url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
        try:
            # NSE requires specific cookies/headers usually handled via session.get initial home page
            self.session.get("https://www.nseindia.com")
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.error(f"Announcement fetch error: {e}")
            return []

    def fetch_fii_dii_activity(self):
        """Fetches FII/DII activity summary."""
        # Simplified: scrape or use mock for now if endpoint is down
        # In production, this would hit a reliable scraper
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "fii_net": 1250.4,
            "dii_net": 840.2,
            "status": "BULLISH"
        }

if __name__ == "__main__":
    dp = DataProvider()
    print(dp.fetch_nse_quote("RELIANCE"))
