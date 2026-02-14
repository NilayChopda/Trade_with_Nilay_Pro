"""
Multi-Source Data Fetcher for Trade With Nilay
Fetches live market data from multiple sources with intelligent fallback

Primary: NSEpy (official NSE data, free)
Backup: yfinance
Future:  Kite API when credentials are ready

Production features:
- Exponential backoff for rate limiting
- Batch processing
- Error recovery queue
- Data quality monitoring
- Multi-threading for performance
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Data source imports
try:
    from nsepy import get_quote, get_history
    NSEPY_AVAILABLE = True
except ImportError:
    NSEPY_AVAILABLE = False
    logging.warning("NSEpy not available, will use yfinance only")

import yfinance as yf

# Internal imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, bulk_insert, log_data_quality, log_system_health
from services.symbol_manager import SymbolManager

logger = logging.getLogger("twn.fetcher")


class RateLimiter:
    """Simple rate limiter with exponential backoff"""
    
    def __init__(self, calls_per_second: float = 2.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        self.backoff_factor = 1.0
        self.max_backoff = 10.0
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        time_since_last = now - self.last_call
        wait_time = (self.min_interval * self.backoff_factor) - time_since_last
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        self.last_call = time.time()
    
    def success(self):
        """Reset backoff on successful call"""
        self.backoff_factor = max(1.0, self.backoff_factor * 0.9)
    
    def failure(self):
        """Increase backoff on failed call"""
        self.backoff_factor = min(self.max_backoff, self.backoff_factor * 1.5)
        logger.warning(f"Rate limit backoff increased to {self.backoff_factor:.2f}x")


class NSEFetcher:
    """Fetch data from NSE using nsepy library"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(calls_per_second=2.0)
    
    def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch latest quote for a symbol
        Returns dict with OHLCV data or None on error
        """
        if not NSEPY_AVAILABLE:
            return None
        
        try:
            self.rate_limiter.wait()
            
            # Get today's data
            today = datetime.now().date()
            data = get_history(
                symbol=symbol,
                start=today,
                end=today,
                index=False
            )
            
            if data.empty:
                return None
            
            # Get latest row
            row = data.iloc[-1]
            
            self.rate_limiter.success()
            
            return {
                'symbol': symbol,
                'timestamp': int(datetime.now().timestamp()),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'source': 'nsepy'
            }
            
        except Exception as e:
            self.rate_limiter.failure()
            logger.debug(f"NSEpy fetch failed for {symbol}: {e}")
            return None


class YahooFetcher:
    """Fetch data from Yahoo Finance (backup source)"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(calls_per_second=5.0)
    
    def fetch_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch latest quote for a symbol
        Returns dict with OHLCV data or None on error
        """
        try:
            self.rate_limiter.wait()
            
            # Yahoo needs .NS suffix for NSE
            yahoo_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            
            # Get 1-day 1-minute data
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if data.empty:
                return None
            
            # Get latest row
            row = data.iloc[-1]
            
            self.rate_limiter.success()
            
            return {
                'symbol': symbol,
                'timestamp': int(pd.Timestamp(row.name).timestamp()),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'source': 'yfinance'
            }
            
        except Exception as e:
            self.rate_limiter.failure()
            logger.debug(f"Yahoo fetch failed for {symbol}: {e}")
            return None


class MultiSourceFetcher:
    """
    Orchestrates multiple data sources with intelligent fallback
    
    Priority order:
    1. NSEpy (free, official NSE)
    2. yfinance (backup)
    """
    
    def __init__(self, batch_size: int = 50, max_workers: int = 5):
        init_db()
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        self.nse_fetcher = NSEFetcher() if NSEPY_AVAILABLE else None
        self.yahoo_fetcher = YahooFetcher()
        
        self.symbol_manager = SymbolManager()
        
        # Retry queue for failed symbols
        self.retry_queue = []
        
        logger.info(f"MultiSourceFetcher initialized (NSEpy: {NSEPY_AVAILABLE})")
    
    def fetch_single(self, symbol: str) -> Optional[Tuple]:
        """
        Fetch data for a single symbol with fallback
        Returns tuple: (symbol, ts, o, h, l, c, volume)
        """
        # Try NSEpy first
        if self.nse_fetcher:
            data = self.nse_fetcher.fetch_quote(symbol)
            if data:
                return (
                    data['symbol'],
                    data['timestamp'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['volume']
                )
        
        # Fallback to Yahoo
        data = self.yahoo_fetcher.fetch_quote(symbol)
        if data:
            return (
                data['symbol'],
                data['timestamp'],
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume']
            )
        
        # All sources failed
        return None
    
    def fetch_batch(self, symbols: List[str]) -> List[Tuple]:
        """
        Fetch data for a batch of symbols in parallel
        Returns list of tuples
        """
        results = []
        failed = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_single, symbol): symbol
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result(timeout=30)
                    if data:
                        results.append(data)
                    else:
                        failed.append(symbol)
                except Exception as e:
                    logger.error(f"Exception fetching {symbol}: {e}")
                    failed.append(symbol)
        
        return results, failed
    
    def fetch_all_equity(self, limit: int = None) -> Dict:
        """
        Fetch data for all NSE equity symbols
        
        Args:
            limit: Optional limit for testing (e.g., 100 stocks)
        
        Returns:
            Dict with stats: total, successful, failed, duration
        """
        start_time = time.time()
        
        # Get symbol universe
        logger.info("Fetching NSE equity universe...")
        all_symbols = self.symbol_manager.fetch_nse_equity_universe()
        
        if limit:
            all_symbols = all_symbols[:limit]
            logger.info(f"Limited to {limit} symbols for testing")
        
        total_symbols = len(all_symbols)
        logger.info(f"Starting data collection for {total_symbols} symbols...")
        
        # Process in batches
        all_results = []
        all_failed = []
        
        for i in range(0, total_symbols, self.batch_size):
            batch = all_symbols[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_symbols + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} symbols)")
            
            results, failed = self.fetch_batch(batch)
            all_results.extend(results)
            all_failed.extend(failed)
            
            # Small delay between batches
            if i + self.batch_size < total_symbols:
                time.sleep(1)
        
        # Store results in database
        if all_results:
            logger.info(f"Inserting {len(all_results)} records into database...")
            bulk_insert(all_results)
        
        # Calculate stats
        duration = time.time() - start_time
        successful = len(all_results)
        failed = len(all_failed)
        
        stats = {
            'total': total_symbols,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_symbols * 100) if total_symbols > 0 else 0,
            'duration_sec': duration,
            'symbols_per_sec': total_symbols / duration if duration > 0 else 0
        }
        
        # Log to data quality table
        status = 'success' if failed == 0 else ('partial' if successful > 0 else 'failed')
        error_details = f"Failed symbols: {', '.join(all_failed[:10])}" if all_failed else None
        
        log_data_quality(
            data_type='equity',
            total=total_symbols,
            successful=successful,
            failed=failed,
            duration=duration,
            status=status,
            errors=error_details
        )
        
        # Log system health
        health_status = 'healthy' if stats['success_rate'] > 90 else ('degraded' if stats['success_rate'] > 50 else 'down')
        log_system_health(
            component='fetcher',
            status=health_status,
            latency_ms=duration * 1000 / total_symbols if total_symbols > 0 else 0,
            error_count=failed,
            message=f"{successful}/{total_symbols} symbols fetched successfully"
        )
        
        logger.info(f"Fetch complete: {successful}/{total_symbols} successful ({stats['success_rate']:.1f}%) in {duration:.1f}s")
        
        return stats
    
    def retry_failed(self) -> int:
        """Retry failed symbols from queue"""
        if not self.retry_queue:
            return 0
        
        logger.info(f"Retrying {len(self.retry_queue)} failed symbols...")
        results, still_failed = self.fetch_batch(self.retry_queue)
        
        if results:
            bulk_insert(results)
        
        self.retry_queue = still_failed
        logger.info(f"Retry complete: {len(results)} recovered, {len(still_failed)} still failing")
        
        return len(results)


def run_once(limit: int = None):
    """
    Run a single fetch cycle
    
    Args:
        limit: Optional limit for testing (e.g., 100 stocks)
    """
    logger.info("=" * 60)
    logger.info("TRADE WITH NILAY - Data Fetcher")
    logger.info("=" * 60)
    
    fetcher = MultiSourceFetcher()
    
    stats = fetcher.fetch_all_equity(limit=limit)
    
    logger.info("\n" + "=" * 60)
    logger.info("FETCH STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total symbols:    {stats['total']}")
    logger.info(f"Successful:       {stats['successful']} ({stats['success_rate']:.1f}%)")
    logger.info(f"Failed:           {stats['failed']}")
    logger.info(f"Duration:         {stats['duration_sec']:.1f}s")
    logger.info(f"Throughput:       {stats['symbols_per_sec']:.1f} symbols/sec")
    logger.info("=" * 60 + "\n")
    
    return stats


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run with limit for testing (remove limit for production)
    run_once(limit=100)
