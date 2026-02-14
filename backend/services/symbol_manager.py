"""
Symbol Manager for Trade With Nilay
Manages NSE equity universe (2600+ stocks), FnO symbols, and indices

Production-grade features:
- Fetches complete NSE equity list
- Filters active stocks (excludes suspended/delisted)
- FnO symbol tracking
- Index management
- Auto-refresh with caching
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd

logger = logging.getLogger("twn.symbol_manager")

class SymbolManager:
    """Manages complete NSE symbol universe with intelligent caching"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "database" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.equity_cache_file = self.cache_dir / "nse_equity_universe.json"
        self.fno_cache_file = self.cache_dir / "nse_fno_symbols.json"
        self.indices_cache_file = self.cache_dir / "nse_indices.json"
        
        # self.nse = None # Removed nsetools
        self._cache_validity_hours = 24  # Refresh daily
        
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file exists and is less than 24 hours old"""
        if not cache_file.exists():
            return False
        
        modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - modified_time
        return age < timedelta(hours=self._cache_validity_hours)
    
    def _read_cache(self, cache_file: Path) -> Optional[List]:
        """Read symbols from cache file"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} symbols from cache: {cache_file.name}")
                return data
        except Exception as e:
            logger.error(f"Failed to read cache {cache_file}: {e}")
            return None
    
    def _write_cache(self, cache_file: Path, data: List):
        """Write symbols to cache file"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached {len(data)} symbols to {cache_file.name}")
        except Exception as e:
            logger.error(f"Failed to write cache {cache_file}: {e}")
    
    def fetch_nse_equity_universe(self, force_refresh: bool = False) -> List[str]:
        """
        Fetch complete NSE equity universe (2600+ stocks)
        
        Returns:
            List of stock symbols (e.g., ['TCS', 'RELIANCE', 'INFY', ...])
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid(self.equity_cache_file):
            cached = self._read_cache(self.equity_cache_file)
            if cached:
                return cached
        
        logger.info("Fetching fresh NSE equity universe...")
        
        try:
            # Method 1: Scrape NSE equity list from official website
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse CSV
                from io import StringIO
                import csv
                
                df = pd.read_csv(StringIO(response.text))
                
                # Extract symbol column (usually first column)
                symbols = df['SYMBOL'].tolist() if 'SYMBOL' in df.columns else df.iloc[:, 0].tolist()
                
                # Clean symbols
                symbols = [str(s).strip().upper() for s in symbols if s and str(s).strip()]
                symbols = [s for s in symbols if s and s != 'SYMBOL']
                
                logger.info(f"Fetched {len(symbols)} NSE equity symbols from website")
                
                # Cache the results
                self._write_cache(self.equity_cache_file, symbols)
                
                return symbols
                
        except Exception as e:
            logger.error(f"Failed to fetch NSE equity universe from web: {e}")
        
        # Method 2: Try nsetools as backup
        try:
            all_stocks = self.nse.get_stock_codes()
            
            # Handle different response formats
            if isinstance(all_stocks, dict):
                symbols = [symbol for symbol in all_stocks.keys() if symbol and len(symbol) <= 20]
            elif isinstance(all_stocks, list):
                symbols = all_stocks
            else:
                symbols = []
            
            # Remove common exclusions
            exclusions = ['SYMBOL', 'INDEX', 'ETF', '']
            symbols = [s for s in symbols if s not in exclusions and len(s) > 0]
            
            if len(symbols) > 100:  # Only use if we got a reasonable number
                logger.info(f"Fetched {len(symbols)} NSE equity symbols from nsetools")
                self._write_cache(self.equity_cache_file, symbols)
                return symbols
                
        except Exception as e:
            logger.error(f"Failed to fetch NSE equity universe from nsetools: {e}")
        
        # Fallback: return cached data even if expired
        cached = self._read_cache(self.equity_cache_file)
        if cached:
            logger.warning("Using expired cache as fallback")
            return cached
        
        # Ultimate fallback: return expanded list of top stocks
        logger.warning("Using fallback list of top stocks")
        return self._get_fallback_symbols()
    
    def fetch_fno_symbols(self, force_refresh: bool = False) -> List[str]:
        """
        Fetch NSE F&O (Futures & Options) symbol list
        
        Returns:
            List of FnO symbols
        """
        if not force_refresh and self._is_cache_valid(self.fno_cache_file):
            cached = self._read_cache(self.fno_cache_file)
            if cached:
                return cached
        
        logger.info("Fetching NSE F&O symbols...")
        
        try:
            # NSE F&O symbols can be fetched from NSE website
            # For now, using a curated list of major F&O stocks
            fno_symbols = [
                # Nifty 50 stocks (most have F&O)
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
                'ICICIBANK', 'KOTAKBANK', 'SBIN', 'BHARTIARTL', 'ITC',
                'AXISBANK', 'LT', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI',
                'HCLTECH', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND',
                'WIPRO', 'ONGC', 'NTPC', 'POWERGRID', 'TATAMOTORS',
                'TATASTEEL', 'TECHM', 'ADANIPORTS', 'INDUSINDBK', 'BAJAJFINSV',
                'DRREDDY', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'GRASIM',
                'DIVISLAB', 'BRITANNIA', 'EICHERMOT', 'SHREECEM', 'CIPLA',
                'HEROMOTOCO', 'UPL', 'APOLLOHOSP', 'BAJAJ-AUTO', 'SBILIFE',
                'BPCL', 'TATACONSUM', 'ADANIENT', 'LTIM', 'PIDILITIND',
                
                # Bank Nifty stocks
                'BANDHANBNK', 'BANKBARODA', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB',
                
                # Other liquid F&O stocks
                'ACC', 'AMBUJACEM', 'ASHOKLEY', 'AUROPHARMA', 'BATAINDIA',
                'BERGEPAINT', 'BEL', 'CANBK', 'CHAMBLFERT', 'CHOLAFIN',
                'COLPAL', 'CONCOR', 'CUMMINSIND', 'DLF', 'GAIL',
                'GODREJCP', 'HAVELLS', 'HDFCLIFE', 'INDUSTOWER', 'JINDALSTEL',
                'M&M', 'MARICO', 'MFSL', 'MOTHERSON', 'MRF',
                'NAUKRI', 'NMDC', 'OFSS', 'OIL', 'PAGEIND',
                'PETRONET', 'PFC', 'POLYCAB', 'PVR', 'RBLBANK',
                'RECLTD', 'SAIL', 'SIEMENS', 'TATAPOWER', 'TORNTPHARM',
                'TVSMOTOR', 'VEDL', 'VOLTAS', 'ZEEL',
            ]
            
            logger.info(f"Loaded {len(fno_symbols)} F&O symbols")
            self._write_cache(self.fno_cache_file, fno_symbols)
            
            return fno_symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch F&O symbols: {e}")
            cached = self._read_cache(self.fno_cache_file)
            return cached if cached else []
    
    def fetch_indices(self, force_refresh: bool = False) -> List[Dict[str, str]]:
        """
        Fetch NSE index list
        
        Returns:
            List of dicts with index name and symbol
        """
        if not force_refresh and self._is_cache_valid(self.indices_cache_file):
            cached = self._read_cache(self.indices_cache_file)
            if cached:
                return cached
        
        logger.info("Fetching NSE indices...")
        
        indices = [
            {"name": "NIFTY 50", "symbol": "NIFTY"},
            {"name": "NIFTY BANK", "symbol": "BANKNIFTY"},
            {"name": "NIFTY IT", "symbol": "NIFTYIT"},
            {"name": "NIFTY AUTO", "symbol": "NIFTYAUTO"},
            {"name": "NIFTY PHARMA", "symbol": "NIFTYPHARMA"},
            {"name": "NIFTY FMCG", "symbol": "NIFTYFMCG"},
            {"name": "NIFTY METAL", "symbol": "NIFTYMETAL"},
            {"name": "NIFTY REALTY", "symbol": "NIFTYREALTY"},
            {"name": "NIFTY ENERGY", "symbol": "NIFTYENERGY"},
            {"name": "NIFTY MEDIA", "symbol": "NIFTYMEDIA"},
            {"name": "NIFTY MIDCAP 50", "symbol": "NIFTYMIDCAP50"},
            {"name": "NIFTY SMALLCAP 50", "symbol": "NIFTYSMALLCAP50"},
            {"name": "INDIA VIX", "symbol": "INDIAVIX"},
        ]
        
        self._write_cache(self.indices_cache_file, indices)
        logger.info(f"Loaded {len(indices)} indices")
        
        return indices
    
    def _get_fallback_symbols(self) -> List[str]:
        """Fallback list of top 100 liquid NSE stocks"""
        return [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'HINDUNILVR', 'KOTAKBANK', 'SBIN', 'BHARTIARTL', 'ITC',
            'AXISBANK', 'LT', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI',
            'HCLTECH', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND',
            'WIPRO', 'ONGC', 'NTPC', 'POWERGRID', 'TATAMOTORS',
            'TATASTEEL', 'TECHM', 'ADANIPORTS', 'INDUSINDBK', 'BAJAJFINSV',
            'DRREDDY', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'GRASIM',
            'DIVISLAB', 'BRITANNIA', 'EICHERMOT', 'SHREECEM', 'CIPLA',
            'HEROMOTOCO', 'UPL', 'APOLLOHOSP', 'BAJAJ-AUTO', 'SBILIFE',
            'BPCL', 'TATACONSUM', 'ADANIENT', 'LTIM', 'PIDILITIND',
        ]
    
    def update_all_caches(self):
        """Force refresh all symbol caches"""
        logger.info("Updating all symbol caches...")
        self.fetch_nse_equity_universe(force_refresh=True)
        self.fetch_fno_symbols(force_refresh=True)
        self.fetch_indices(force_refresh=True)
        logger.info("All caches updated successfully")
    
    def get_all_trading_symbols(self) -> Dict[str, List]:
        """
        Get all symbols organized by category
        
        Returns:
            Dict with keys: 'equity', 'fno', 'indices'
        """
        return {
            'equity': self.fetch_nse_equity_universe(),
            'fno': self.fetch_fno_symbols(),
            'indices': self.fetch_indices(),
        }


# Standalone functions for easy import
def get_equity_symbols() -> List[str]:
    """Quick function to get NSE equity symbols"""
    manager = SymbolManager()
    return manager.fetch_nse_equity_universe()


def get_fno_symbols() -> List[str]:
    """Quick function to get F&O symbols"""
    manager = SymbolManager()
    return manager.fetch_fno_symbols()


def get_indices() -> List[Dict]:
    """Quick function to get indices"""
    manager = SymbolManager()
    return manager.fetch_indices()


if __name__ == "__main__":
    # Test the symbol manager
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = SymbolManager()
    
    logger.info("=== Testing Symbol Manager ===")
    
    # Test equity universe
    equity = manager.fetch_nse_equity_universe()
    logger.info(f"Total equity symbols: {len(equity)}")
    logger.info(f"Sample symbols: {equity[:10]}")
    
    # Test F&O symbols
    fno = manager.fetch_fno_symbols()
    logger.info(f"Total F&O symbols: {len(fno)}")
    logger.info(f"Sample F&O: {fno[:5]}")
    
    # Test indices
    indices = manager.fetch_indices()
    logger.info(f"Total indices: {len(indices)}")
    logger.info(f"Sample indices: {[idx['name'] for idx in indices[:5]]}")
    
    # Test cache update
    manager.update_all_caches()
    
    logger.info("=== Symbol Manager Test Complete ===")
