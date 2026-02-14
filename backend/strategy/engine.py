"""
Strategy Engine
Orchestrates the running of strategies on market data
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Type
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from backend.strategy.base import Strategy
from backend.database.db import get_conn, get_historical_data
from backend.services.symbol_manager import get_equity_symbols

logger = logging.getLogger("twn.strategy_engine")

class StrategyEngine:
    """
    Manages and executes registered trading strategies
    """
    
    def __init__(self):
        self.strategies: List[Strategy] = []
    
    def register_strategy(self, strategy: Strategy):
        """Add a strategy instance to the engine"""
        self.strategies.append(strategy)
        logger.info(f"Registered strategy: {strategy.name}")

    def run_strategy(self, strategy_name: str, symbols: List[str] = None) -> List[Dict]:
        """Run a specific strategy on a list of symbols"""
        if symbols is None:
            symbols = get_equity_symbols()
        
        target_strat = next((s for s in self.strategies if s.name == strategy_name), None)
        if not target_strat:
            logger.error(f"Strategy {strategy_name} not found")
            return []
            
        results = []
        
        # Parallel processing for speed
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._analyze_symbol, target_strat, sym): sym 
                for sym in symbols[:50]  # Limit to 50 for testing/safety for now
            }
            
            for future in futures:
                try:
                    signals = future.result()
                    results.extend(signals)
                except Exception as e:
                    logger.error(f"Error analyzing {futures[future]}: {e}")
                    
        return results

    def _analyze_symbol(self, strategy: Strategy, symbol: str) -> List[Dict]:
        """Worker function to analyze a single symbol"""
        # Fetch data (last 200 candles approx 3.5 hours)
        import time
        end_ts = int(time.time())
        start_ts = end_ts - (200 * 60) # 200 minutes
        
        df = get_historical_data(symbol, start_ts, end_ts)
        
        if df.empty or len(df) < 50:
            return []
            
        signals = strategy.analyze(df)
        
        # Inject symbol into results
        for signal in signals:
            signal['symbol'] = symbol
            
        return signals

    def run_all(self) -> Dict[str, List[Dict]]:
        """Run all registered strategies"""
        all_results = {}
        for strategy in self.strategies:
            all_results[strategy.name] = self.run_strategy(strategy.name)
        return all_results
