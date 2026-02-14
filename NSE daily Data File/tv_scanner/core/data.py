import time
import pandas as pd
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try importing TvDatafeed, else set to None
try:
    from tvdatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    TV_AVAILABLE = False
    logger.warning("tvdatafeed library not found. Using Mock Data for demonstration.")
    # Mocking Interval enum
    class Interval:
        in_daily = 'daily'
        in_weekly = 'weekly'
        in_monthly = 'monthly'

class TVDataLoader:
    def __init__(self, username=None, password=None):
        if TV_AVAILABLE:
            self.tv = TvDatafeed(username, password)
        else:
            self.tv = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_data(self, symbol, exchange='NSE', interval=Interval.in_daily, n_bars=100):
        """
        Fetches data from TradingView with retries.
        """
        if not TV_AVAILABLE:
            return self._generate_mock_data(n_bars)

        try:
            # tvdatafeed usually expects 'NSE' as exchange for Indian stocks
            df = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
            if df is None or df.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise e

    def _generate_mock_data(self, n_bars):
        """Generates random OHLCV data for testing."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_bars, freq='D')
        data = {
            'open': np.random.uniform(100, 200, n_bars),
            'high': np.random.uniform(200, 210, n_bars),
            'low': np.random.uniform(90, 100, n_bars),
            'close': np.random.uniform(100, 200, n_bars),
            'volume': np.random.randint(1000, 100000, n_bars)
        }
        df = pd.DataFrame(data, index=dates)
        df.index.name = 'datetime'
        return df

    def fetch_multiple_timeframes(self, symbol, exchange='NSE'):
        """
        Fetches Daily, Weekly, and Monthly data for a symbol.
        Returns a dictionary of DataFrames.
        """
        data = {}
        try:
            # Daily data (need enough for WMA lookback)
            data['daily'] = self.fetch_data(symbol, exchange, Interval.in_daily, n_bars=50)
            
            # Weekly data
            data['weekly'] = self.fetch_data(symbol, exchange, Interval.in_weekly, n_bars=20)
            
            # Monthly data
            data['monthly'] = self.fetch_data(symbol, exchange, Interval.in_monthly, n_bars=12)
            
            return data
        except Exception as e:
            logger.error(f"Failed to fetch complete data for {symbol}: {e}")
            return None
