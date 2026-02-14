import concurrent.futures
import time
import pandas as pd
from typing import List
from core.data import TVDataLoader
from core.indicators import Indicators
from core.ranking import SignalRankingEngine, RankedSignal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self, username=None, password=None):
        self.loader = TVDataLoader(username, password)
        self.results = []
        self.ranking_engine = SignalRankingEngine()
        
    def scan_symbol(self, symbol):
        """
        Scans a single symbol. Returns result dict if passed, else None.
        """
        try:
            # logger.info(f"Scanning {symbol}...")
            # Fetch data (Daily, Weekly, Monthly)
            data_dict = self.loader.fetch_multiple_timeframes(symbol)
            if not data_dict:
                return None
            
            # Process indicators
            # Temporarily attach symbol name to daily df for 'process_data' usage if needed, 
            # though process_data uses index name usually.
            if data_dict['daily'] is not None:
                data_dict['daily'].index.name = symbol

            metrics = Indicators.process_data(data_dict)
            if not metrics:
                return None
            
            metrics['symbol'] = symbol # Ensure symbol is set explicitly
            
            # Check conditions
            if Indicators.check_conditions(metrics):
                logger.info(f"MATCH: {symbol}")
                return metrics
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
        
        return None

    def run_scan(self, symbols, max_workers=5):
        """
        Runs the scan for a list of symbols using thread pool.
        """
        self.results = []
        logger.info(f"Starting scan for {len(symbols)} symbols with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {executor.submit(self.scan_symbol, sym): sym for sym in symbols}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    res = future.result()
                    if res:
                        self.results.append(res)
                except Exception as exc:
                    logger.error(f"{sym} generated an exception: {exc}")
                
                completed += 1
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(symbols)}")
        
        logger.info(f"Scan complete. Found {len(self.results)} matches.")
        return pd.DataFrame(self.results)
    
    def rank_results(self, df: pd.DataFrame, 
                     ob_tapped_symbols: List[str] = None,
                     swing_valid_symbols: List[str] = None,
                     doji_symbols: List[str] = None,
                     consolidation_symbols: List[str] = None,
                     volume_spike_symbols: List[str] = None,
                     top_n: int = None) -> pd.DataFrame:
        """
        Rank scanned results based on multiple signal conditions.
        
        Args:
            df: DataFrame with scan results
            ob_tapped_symbols: List of symbols where OB was tapped
            swing_valid_symbols: List of symbols with valid swing condition
            doji_symbols: List of symbols with doji pattern
            consolidation_symbols: List of symbols with consolidation
            volume_spike_symbols: List of symbols with volume spike
            top_n: Return top N results
        
        Returns:
            Ranked DataFrame
        """
        if df.empty:
            logger.warning("No results to rank.")
            return df
        
        # Set defaults
        ob_tapped_symbols = ob_tapped_symbols or []
        swing_valid_symbols = swing_valid_symbols or []
        doji_symbols = doji_symbols or []
        consolidation_symbols = consolidation_symbols or []
        volume_spike_symbols = volume_spike_symbols or []
        
        ranked_signals = []
        
        for _, row in df.iterrows():
            symbol = row['symbol']
            
            ranked_signal = self.ranking_engine.calculate_rank(
                symbol=symbol,
                metrics=row.to_dict(),
                ob_tapped=symbol in ob_tapped_symbols,
                swing_valid=symbol in swing_valid_symbols,
                doji_detected=symbol in doji_symbols,
                consolidation_detected=symbol in consolidation_symbols,
                volume_spiked=symbol in volume_spike_symbols
            )
            
            ranked_signals.append(ranked_signal)
        
        # Rank and format
        ranked_signals = self.ranking_engine.rank_signals(ranked_signals, top_n=top_n)
        
        # Convert to DataFrame
        ranked_df = self.ranking_engine.to_dataframe(ranked_signals)
        
        logger.info(f"Ranked {len(ranked_signals)} signals.")
        return ranked_df
