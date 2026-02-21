
import logging
from kiteconnect import KiteConnect
import os

logger = logging.getLogger(__name__)

class KiteProvider:
    def __init__(self, api_key):
        self.api_key = api_key
        self.kite = None

    def set_access_token(self, access_token):
        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(access_token)

    def get_live_quote(self, symbol):
        """Fetches live LTP and volume from Kite."""
        if not self.kite:
            return None
        try:
            # Kite uses 'NSE:SYMBOL' format
            instrument = f"NSE:{symbol}"
            quote = self.kite.quote([instrument])
            if instrument in quote:
                q = quote[instrument]
                return {
                    "symbol": symbol,
                    "price": q["last_price"],
                    "volume": q["volume"],
                    "change_pct": ((q["last_price"] - q["ohlc"]["close"]) / q["ohlc"]["close"]) * 100 if q["ohlc"]["close"] > 0 else 0,
                    "source": "Kite"
                }
        except Exception as e:
            logger.error(f"Kite quote error for {symbol}: {e}")
        return None

    def get_login_url(self):
        return KiteConnect(api_key=self.api_key).login_url()
