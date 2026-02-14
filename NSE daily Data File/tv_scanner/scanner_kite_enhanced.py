"""
Enhanced NSE Scanner using KITE API
Fetches real-time prices from Zerodha for ALL 2700+ NSE securities
Sends alerts to Telegram bot
"""

import concurrent.futures
import logging
from typing import List, Dict, Optional
import pandas as pd
from core.indicators import Indicators
from core.ranking import SignalRankingEngine
from bot.telegram_bot import ScannerBot

logger = logging.getLogger(__name__)


class KITEScannerEnhanced:
    """
    Enhanced scanner using KITE API for real-time NSE prices
    Supports scanning all 2700+ NSE securities
    """
    
    def __init__(self, kite_fetcher, telegram_token: Optional[str] = None, 
                 telegram_chat_id: Optional[str] = None):
        """
        Initialize scanner with KITE API
        
        Args:
            kite_fetcher: KITEDataFetcher instance
            telegram_token: Telegram bot token for alerts
            telegram_chat_id: Telegram chat ID for alerts
        """
        self.fetcher = kite_fetcher
        self.results = []
        self.ranking_engine = SignalRankingEngine()
        
        # Initialize Telegram bot
        self.bot = ScannerBot(token=telegram_token, chat_id=telegram_chat_id)
        
        logger.info("KITE Scanner Enhanced initialized")
    
    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Scan a single symbol for trading signals
        
        Args:
            symbol: NSE symbol
        
        Returns:
            Signal metrics dict or None
        """
        try:
            # Fetch daily OHLC data
            daily_df = self.fetcher.fetch_daily_ohlc(symbol, days=50)
            if daily_df is None or daily_df.empty:
                return None
            
            # Prepare data dict
            data_dict = {'daily': daily_df}
            
            # Process indicators
            metrics = Indicators.process_data(data_dict)
            if not metrics:
                return None
            
            metrics['symbol'] = symbol
            
            # Get current LTP for reference
            try:
                ltp_data = self.fetcher.fetch_ltp([symbol])
                if symbol in ltp_data:
                    metrics['current_ltp'] = ltp_data[symbol]['ltp']
                    metrics['current_bid'] = ltp_data[symbol]['bid']
                    metrics['current_ask'] = ltp_data[symbol]['ask']
                    metrics['live_volume'] = ltp_data[symbol]['volume']
            except Exception as e:
                logger.warning(f"Could not fetch LTP for {symbol}: {e}")
            
            # Check conditions
            if Indicators.check_conditions(metrics):
                logger.info(f"MATCH: {symbol}")
                return metrics
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
        
        return None
    
    def run_scan_all_nse(self, max_workers: int = 10, 
                        max_symbols: Optional[int] = None) -> pd.DataFrame:
        """
        Scan ALL NSE securities (2700+)
        
        Args:
            max_workers: Number of concurrent workers
            max_symbols: Limit symbols for testing (None = all)
        
        Returns:
            DataFrame with scan results
        """
        logger.info("Fetching all NSE symbols...")
        symbols = self.fetcher.get_all_nse_symbols()
        
        if max_symbols:
            symbols = symbols[:max_symbols]
        
        logger.info(f"Scanning {len(symbols)} NSE securities...")
        return self.run_scan(symbols, max_workers)
    
    def run_scan(self, symbols: List[str], max_workers: int = 10) -> pd.DataFrame:
        """
        Run scan for specified symbols
        
        Args:
            symbols: List of NSE symbols
            max_workers: Number of concurrent workers
        
        Returns:
            DataFrame with scan results
        """
        self.results = []
        logger.info(f"Starting scan for {len(symbols)} symbols with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.scan_symbol, sym): sym for sym in symbols}
            
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                sym = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        
                        # Send alert immediately to Telegram
                        self._send_signal_alert(result)
                        
                except Exception as e:
                    logger.error(f"{sym} generated exception: {e}")
                
                completed += 1
                if completed % 50 == 0:
                    logger.info(f"Progress: {completed}/{len(symbols)} | Signals found: {len(self.results)}")
        
        logger.info(f"Scan complete. Found {len(self.results)} signals.")
        
        # Send summary to Telegram
        self._send_scan_summary(len(symbols), len(self.results))
        
        return pd.DataFrame(self.results) if self.results else pd.DataFrame()
    
    def _send_signal_alert(self, signal_dict: Dict):
        """Send individual signal alert to Telegram"""
        try:
            message = self._format_signal_message(signal_dict)
            self.bot.send_message(message)
            logger.debug(f"Sent alert for {signal_dict.get('symbol')}")
        except Exception as e:
            logger.error(f"Error sending signal alert: {e}")
    
    def _send_scan_summary(self, total_scanned: int, signals_found: int):
        """Send scan summary to Telegram"""
        try:
            message = (
                f"🔍 **Scan Complete**\n\n"
                f"Total Scanned: {total_scanned}\n"
                f"Signals Found: {signals_found}\n"
                f"Match Rate: {(signals_found/total_scanned*100):.2f}%\n"
            )
            self.bot.send_message(message)
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
    
    def _format_signal_message(self, signal_dict: Dict) -> str:
        """Format signal as Telegram message"""
        symbol = signal_dict.get('symbol', 'UNKNOWN')
        close = signal_dict.get('close', 0)
        ltp = signal_dict.get('current_ltp', close)
        ob_low = signal_dict.get('ob_low', 0)
        ob_high = signal_dict.get('ob_high', 0)
        
        return (
            f"🎯 **SIGNAL: {symbol}**\n\n"
            f"📊 Current Price: ₹{ltp:.2f}\n"
            f"💰 Close: ₹{close:.2f}\n"
            f"🔲 OB Low: ₹{ob_low:.2f}\n"
            f"🔲 OB High: ₹{ob_high:.2f}\n"
            f"📈 Volume: {signal_dict.get('live_volume', 0):,.0f}\n"
        )
    
    def rank_results(self, df: pd.DataFrame, top_n: Optional[int] = None) -> pd.DataFrame:
        """
        Rank scanned results
        
        Args:
            df: DataFrame with scan results
            top_n: Return top N results
        
        Returns:
            Ranked DataFrame
        """
        if df.empty:
            return df
        
        ranked_signals = self.ranking_engine.rank_signals(df)
        ranked_df = self.ranking_engine.to_dataframe(ranked_signals)
        
        if top_n:
            ranked_df = ranked_df.head(top_n)
        
        return ranked_df
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get results as DataFrame"""
        return pd.DataFrame(self.results) if self.results else pd.DataFrame()
