"""
KITE API Data Fetcher - Direct NSE Real-time Prices
Replaces Yahoo Finance with Zerodha KITE API for accurate live prices
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    logger.warning("kiteconnect library not found. Install with: pip install kiteconnect")


class KITEDataFetcher:
    """
    Real-time data fetcher using Zerodha KITE API
    Provides accurate live NSE prices
    """
    
    def __init__(self, api_key: str, access_token: str):
        """
        Initialize KITE API connection
        
        Args:
            api_key: Your Zerodha API key
            access_token: Your KITE access token
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect library required. Install with: pip install kiteconnect")
        
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.api_key = api_key
        self.access_token = access_token
        self.symbols_cache = None
        self.last_update = None
        
        logger.info("KITE API initialized successfully")
    
    def get_all_nse_symbols(self, refresh: bool = False) -> List[str]:
        """
        Get all NSE symbols (2700+)
        Caches for 1 hour to avoid repeated API calls
        
        Args:
            refresh: Force refresh even if cached
        
        Returns:
            List of NSE symbols
        """
        # Return cache if available and fresh
        if self.symbols_cache and self.last_update:
            age = datetime.now() - self.last_update
            if age.total_seconds() < 3600 and not refresh:
                logger.info(f"Using cached symbols ({len(self.symbols_cache)} symbols)")
                return self.symbols_cache
        
        try:
            logger.info("Fetching all NSE symbols from KITE API...")
            instruments = self.kite.instruments("NSE")
            
            # Filter for equity only (not options, futures, etc)
            nse_symbols = []
            for inst in instruments:
                if inst['segment'] == 'NSE' and inst['instrument_type'] == 'EQ':
                    nse_symbols.append(inst['tradingsymbol'])
            
            self.symbols_cache = nse_symbols
            self.last_update = datetime.now()
            
            logger.info(f"Fetched {len(nse_symbols)} NSE securities")
            return nse_symbols
            
        except Exception as e:
            logger.error(f"Error fetching NSE symbols: {e}")
            return self.symbols_cache or []
    
    def fetch_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch Last Traded Price (LTP) for multiple symbols
        
        Args:
            symbols: List of NSE symbols
        
        Returns:
            Dictionary of {symbol: ltp_price}
        """
        if not symbols:
            return {}
        
        try:
            # Add NSE: prefix if not present
            instrument_tokens = []
            for sym in symbols:
                if not sym.startswith('NSE:'):
                    instrument_tokens.append(f'NSE:{sym}')
                else:
                    instrument_tokens.append(sym)
            
            # Fetch data
            ltp_data = self.kite.quote(instrument_tokens)
            
            result = {}
            for inst in ltp_data:
                symbol = inst['tradingsymbol'].replace('NSE:', '')
                result[symbol] = {
                    'ltp': inst['last_price'],
                    'bid': inst['bid'],
                    'ask': inst['ask'],
                    'volume': inst.get('volume', 0),
                    'timestamp': datetime.now()
                }
            
            logger.debug(f"Fetched LTP for {len(result)} symbols")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching LTP: {e}")
            return {}
    
    def fetch_daily_ohlc(self, symbol: str, days: int = 50) -> Optional[pd.DataFrame]:
        """
        Fetch daily OHLC data
        
        Args:
            symbol: NSE symbol (e.g., 'INFY')
            days: Number of days of historical data
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.debug(f"Fetching {days} days of data for {symbol}")
            
            instrument_token = f'NSE:{symbol}'
            
            data = self.kite.historical_data(
                instrument_token,
                start_date.date(),
                end_date.date(),
                interval='day'
            )
            
            if not data:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df.columns = ['close', 'high', 'low', 'open', 'volume']
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.debug(f"Fetched {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLC for {symbol}: {e}")
            return None
    
    def fetch_multiple_daily_ohlc(self, symbols: List[str], days: int = 50,
                                  max_workers: int = 5) -> Dict[str, pd.DataFrame]:
        """
        Fetch daily OHLC for multiple symbols using threading
        
        Args:
            symbols: List of NSE symbols
            days: Days of historical data
            max_workers: Number of concurrent threads
        
        Returns:
            Dictionary of {symbol: DataFrame}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        result = {}
        
        def fetch_single(sym):
            df = self.fetch_daily_ohlc(sym, days)
            return sym, df
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_single, sym) for sym in symbols]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    sym, df = future.result()
                    if df is not None:
                        result[sym] = df
                    completed += 1
                    if completed % 50 == 0:
                        logger.info(f"Fetched {completed}/{len(symbols)} symbols")
                except Exception as e:
                    logger.error(f"Error in fetch_single: {e}")
        
        logger.info(f"Successfully fetched {len(result)}/{len(symbols)} symbols")
        return result
    
    def fetch_intraday_data(self, symbol: str, interval: str = '5minute',
                           limit_bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch intraday data (5min, 15min, etc)
        
        Args:
            symbol: NSE symbol
            interval: '5minute', '15minute', '30minute', '60minute'
            limit_bars: Number of bars to fetch
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            instrument_token = f'NSE:{symbol}'
            
            data = self.kite.historical_data(
                instrument_token,
                datetime.now().date(),
                datetime.now().date(),
                interval=interval,
                continuous=False,
                oi=False
            )
            
            if not data:
                return None
            
            # Keep only last N bars
            data = data[-limit_bars:]
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df.columns = ['close', 'high', 'low', 'open', 'volume']
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None


class YAMLConfigKITE:
    """Helper to set up KITE API from config"""
    
    @staticmethod
    def from_env() -> KITEDataFetcher:
        """Create KITE fetcher from environment variables"""
        import os
        
        api_key = os.getenv('KITE_API_KEY')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if not api_key or not access_token:
            raise ValueError("Set KITE_API_KEY and KITE_ACCESS_TOKEN environment variables")
        
        return KITEDataFetcher(api_key, access_token)
    
    @staticmethod
    def from_config(config_dict: Dict) -> KITEDataFetcher:
        """Create KITE fetcher from config dictionary"""
        api_key = config_dict.get('api_key')
        access_token = config_dict.get('access_token')
        
        if not api_key or not access_token:
            raise ValueError("Config must contain 'api_key' and 'access_token'")
        
        return KITEDataFetcher(api_key, access_token)
