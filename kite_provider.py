
import logging
import pandas as pd
from kiteconnect import KiteConnect
import os
from datetime import datetime, timedelta

logger = logging.getLogger("twn.kite_provider")

class KiteProvider:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("KITE_API_KEY", "927xjtvndq82vjc3")
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token = os.environ.get("KITE_ACCESS_TOKEN")
        if self.access_token:
            self.kite.set_access_token(self.access_token)

    def set_access_token(self, token):
        self.access_token = token
        self.kite.set_access_token(token)

    def get_live_quote(self, symbol):
        """Fetch live quote for a symbol."""
        try:
            # Kite uses 'NSE:SYMBOL' format
            instrument = f"NSE:{symbol}"
            # Batch fetch for just this one symbol is reliable
            quote_map = self.kite.quote(instrument)
            
            if instrument in quote_map:
                data = quote_map[instrument]
                
                # KiteNet Change is points, but we need percentage logic consistent with yfinance
                price = data['last_price']
                prev_close = data['ohlc']['close']
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                
                return {
                    "symbol": symbol,
                    "price": float(price),
                    "change_pct": round(float(change_pct), 2),
                    "volume": int(data.get('volume', 0)),
                    "high": float(data['ohlc']['high']),
                    "low": float(data['ohlc']['low']),
                    "open": float(data['ohlc']['open']),
                    "prev_close": float(prev_close),
                    "source": "kite"
                }
            else:
                logger.warning(f"Symbol {instrument} not found in Kite quote response")
            return None
        except Exception as e:
            logger.error(f"Kite live quote error for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol, days=365, interval="day"):
        """Fetch historical data using Kite API."""
        try:
            # Need instrument token for historical data
            # For simplicity, we assume we can resolve it or use the symbol if supported
            # In a real app, we'd load an instruments list and map SYMBOL -> instrument_token
            # Let's try to find the token first
            instruments = self.kite.instruments("NSE")
            df_inst = pd.DataFrame(instruments)
            token_row = df_inst[df_inst['tradingsymbol'] == symbol]
            
            if token_row.empty:
                logger.error(f"Instrument token not found for {symbol}")
                return pd.DataFrame()
                
            token = int(token_row.iloc[0]['instrument_token'])
            
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            records = self.kite.historical_data(token, from_date, to_date, interval)
            df = pd.DataFrame(records)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                # Ensure columns match expected format
                df.columns = [c.capitalize() for c in df.columns]
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Kite historical data error for {symbol}: {e}")
            return pd.DataFrame()

# Keep existing bhavcopy functions for backup/EOD reports
def download_bhavcopy(date):
    import requests
    import io
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/all-reports",
        "Origin": "https://www.nseindia.com"
    })

    date_str = date.strftime("%d-%m-%Y")
    url = f"https://www.nseindia.com/api/reports?archives=cm&date={date_str}&type=equities"

    try:
        session.get("https://www.nseindia.com", timeout=10)
        r = session.get(url, timeout=15)

        if r.status_code != 200:
            return None

        df = pd.read_csv(io.BytesIO(r.content))
        return df
    except Exception as e:
        logger.error(f"Bhavcopy error: {e}")
        return None