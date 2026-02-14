"""
Strategy Engine Test Script
"""

import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.strategy.engine import StrategyEngine
from backend.strategy.ema_bounce import EMABounceStrategy
from backend.strategy.patterns import DojiStrategy, InsideBarStrategy, DeadVolumeStrategy
from backend.strategy.smc import OrderBlockStrategy, MSSStrategy
from backend.strategy.breakout import BreakoutStrategy, ConsolidationStrategy
from backend.services.symbol_manager import get_equity_symbols

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("twn.test_strategy")
    
    logger.info("Initializing Strategy Engine...")
    engine = StrategyEngine()
    
    # Register Strategies
    strategies = [
        EMABounceStrategy(),
        DojiStrategy(),
        InsideBarStrategy(),
        DeadVolumeStrategy(),
        OrderBlockStrategy(),
        MSSStrategy(),
        BreakoutStrategy(),
        ConsolidationStrategy()
    ]
    
    for s in strategies:
        engine.register_strategy(s)
    
    # Get Symbols (limit for testing)
    all_symbols = get_equity_symbols()
    test_symbols = all_symbols[:10]
    # Add some popular liquid stocks for better chance of finding setup
    liquid_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "ICICIBANK"]
    test_symbols.extend([s for s in liquid_stocks if s not in test_symbols])
    
    logger.info(f"Running strategies on {len(test_symbols)} symbols...")
    
    all_results = {}
    for s in strategies:
        all_results[s.name] = engine.run_strategy(s.name, test_symbols)
    
    total_signals = sum(len(r) for r in all_results.values())
    logger.info(f"Found {total_signals} signals across {len(strategies)} strategies")
    
    for strategy_name, signals in all_results.items():
        if not signals:
            continue
            
        print(f"\n--- {strategy_name} ({len(signals)}) ---")
        for signal in signals:
            print(f"[{signal['signal']}] {signal['symbol']} @ {signal['price']}")
            if 'pattern' in signal:
                print(f"  Pattern: {signal['pattern']}")
            if 'confidence' in signal:
                print(f"  Confidence: {signal['confidence']}")
