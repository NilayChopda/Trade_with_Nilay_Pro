"""
Phase 7: Signal Ranking System - Usage Examples
Demonstrates practical usage of the ranking engine with scanner results.
"""

import pandas as pd
import numpy as np
from core.ranking import SignalRankingEngine, RankedSignal
from core.indicators import Indicators
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_basic_ranking():
    """Example 1: Basic ranking of scanned results"""
    logger.info("\n" + "="*70)
    logger.info("📋 EXAMPLE 1: Basic Ranking of Scan Results")
    logger.info("="*70)
    
    # Simulated scan results
    scan_results = pd.DataFrame({
        'symbol': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS'],
        'close': [2850.50, 3650.75, 1850.25, 1580.00],
        'pct_change': [1.25, -0.75, 2.10, 0.50],
        'volume': [1500000, 800000, 2100000, 950000],
        'd_wma1': [2851.00, 3651.50, 1851.00, 1580.50],
        'm_wma2': [2840.00, 3640.00, 1840.00, 1570.00],
    })
    
    engine = SignalRankingEngine()
    ranked_signals = []
    
    # Simulate detected signals (you'd get these from other engines)
    signal_data = [
        {'ob_tapped': True, 'swing_valid': True, 'doji_detected': True},
        {'swing_valid': True, 'consolidation_detected': True},
        {'ob_tapped': True, 'volume_spiked': True},
        {'doji_detected': True, 'consolidation_detected': True},
    ]
    
    for _, row in scan_results.iterrows():
        symbol = row['symbol']
        signals = signal_data[list(scan_results['symbol']).index(symbol)]
        
        ranked = engine.calculate_rank(symbol, row.to_dict(), **signals)
        ranked_signals.append(ranked)
    
    # Rank and display
    sorted_signals = engine.rank_signals(ranked_signals)
    report = engine.format_ranking_report(sorted_signals)
    logger.info(report)
    
    return sorted_signals


def example_2_top_n_stocks():
    """Example 2: Get top N stocks by score"""
    logger.info("="*70)
    logger.info("🏆 EXAMPLE 2: Get Top N Ranked Stocks")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    
    # Simulate 10 stocks with various signals
    stocks = []
    for i in range(10):
        signal = RankedSignal(
            symbol=f'STOCK_{i+1}.NS',
            total_score=np.random.randint(0, 15),
            close_price=1000 + i*100,
            pct_change=np.random.uniform(-2, 3),
            volume=np.random.uniform(500000, 2000000),
            ob_tapped=np.random.random() > 0.5,
            swing_valid=np.random.random() > 0.5,
            doji_detected=np.random.random() > 0.5,
            consolidation_detected=np.random.random() > 0.5,
            volume_spiked=np.random.random() > 0.5,
        )
        stocks.append(signal)
    
    # Get top 5
    logger.info("\n📊 All Stocks:")
    for sig in stocks:
        logger.info(f"  {sig.symbol}: {sig.total_score}")
    
    top_5 = engine.rank_signals(stocks, top_n=5)
    logger.info("\n🎯 Top 5 Stocks:")
    for idx, sig in enumerate(top_5, 1):
        logger.info(f"  {idx}. {sig.symbol}: {sig.total_score}")
    
    return top_5


def example_3_score_breakdown():
    """Example 3: Show detailed score breakdown"""
    logger.info("\n" + "="*70)
    logger.info("📊 EXAMPLE 3: Score Breakdown Analysis")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    
    stocks = [
        RankedSignal(
            symbol='RELIANCE.NS',
            total_score=10,
            ob_tap_score=5,
            swing_condition_score=3,
            doji_score=2,
            consolidation_score=0,
            volume_spike_score=0,
            close_price=2850.50,
            pct_change=1.25,
            volume=1500000,
            ob_tapped=True,
            swing_valid=True,
            doji_detected=True,
        ),
        RankedSignal(
            symbol='TCS.NS',
            total_score=7,
            ob_tap_score=5,
            swing_condition_score=0,
            doji_score=0,
            consolidation_score=2,
            volume_spike_score=0,
            close_price=3650.75,
            pct_change=-0.75,
            volume=800000,
            ob_tapped=True,
            consolidation_detected=True,
        ),
        RankedSignal(
            symbol='INFY.NS',
            total_score=4,
            ob_tap_score=0,
            swing_condition_score=3,
            doji_score=0,
            consolidation_score=0,
            volume_spike_score=2,
            close_price=1850.25,
            pct_change=2.10,
            volume=2100000,
            swing_valid=True,
            volume_spiked=True,
        ),
    ]
    
    df = engine.to_dataframe(stocks)
    logger.info("\n" + df.to_string(index=False))
    
    # Summary stats
    stats = engine.get_summary_stats(stocks)
    logger.info("\n📈 Summary Statistics:")
    logger.info(f"  Total Signals: {stats['total_signals']}")
    logger.info(f"  Average Score: {stats['avg_score']:.2f}")
    logger.info(f"  Signals with OB Tap: {stats['ob_tapped_count']}")
    logger.info(f"  Signals with Swing: {stats['swing_valid_count']}")
    logger.info(f"  Signals with Doji: {stats['doji_count']}")
    logger.info(f"  Signals with Consolidation: {stats['consolidation_count']}")
    logger.info(f"  Signals with Volume Spike: {stats['volume_spike_count']}")


def example_4_filter_by_minimum_score():
    """Example 4: Filter stocks by minimum score threshold"""
    logger.info("\n" + "="*70)
    logger.info("🎯 EXAMPLE 4: Filter by Minimum Score Threshold")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    
    # Simulate 8 stocks
    stocks = []
    scores = [2, 5, 7, 3, 10, 4, 6, 8]
    
    for i, score in enumerate(scores):
        signal = RankedSignal(
            symbol=f'STOCK_{i+1}.NS',
            total_score=score,
            close_price=1000 + i*100,
            pct_change=np.random.uniform(-1, 2),
        )
        stocks.append(signal)
    
    # Filter by minimum score of 5
    min_score = 5
    filtered = [s for s in stocks if s.total_score >= min_score]
    
    logger.info(f"\n📊 All Stocks: {len(stocks)}")
    for sig in stocks:
        logger.info(f"  {sig.symbol}: {sig.total_score}")
    
    logger.info(f"\n🔥 Stocks with Score >= {min_score}: {len(filtered)}")
    sorted_filtered = engine.rank_signals(filtered)
    for idx, sig in enumerate(sorted_filtered, 1):
        logger.info(f"  {idx}. {sig.symbol}: {sig.total_score}")


def example_5_combined_criteria():
    """Example 5: Complex ranking with multiple criteria"""
    logger.info("\n" + "="*70)
    logger.info("🔍 EXAMPLE 5: Complex Multi-Criteria Ranking")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    
    # Create stocks with various characteristics
    stocks = [
        RankedSignal(
            symbol='HIGH_OB.NS',
            total_score=12,
            ob_tapped=True,
            swing_valid=True,
            volume_spiked=True,
            close_price=2000,
            pct_change=1.5,
            volume=1500000,
        ),
        RankedSignal(
            symbol='HIGH_SWING.NS',
            total_score=10,
            ob_tapped=True,
            swing_valid=True,
            doji_detected=True,
            close_price=1800,
            pct_change=0.8,
            volume=1200000,
        ),
        RankedSignal(
            symbol='MEDIUM_MIX.NS',
            total_score=7,
            swing_valid=True,
            consolidation_detected=True,
            volume_spiked=True,
            close_price=1500,
            pct_change=0.5,
            volume=900000,
        ),
        RankedSignal(
            symbol='LOW_SIGNAL.NS',
            total_score=2,
            doji_detected=True,
            close_price=1200,
            pct_change=-0.3,
            volume=600000,
        ),
    ]
    
    # Analysis by signal type
    logger.info("\n📊 Stocks with OB Tap (Score ≥ 5):")
    ob_stocks = [s for s in stocks if s.ob_tapped and s.total_score >= 5]
    for sig in engine.rank_signals(ob_stocks):
        logger.info(f"  {sig.symbol}: {sig.total_score} (OB: {sig.ob_tap_score})")
    
    logger.info("\n📊 Stocks with Multiple Signals (≥3 conditions):")
    multi_signal = [
        s for s in stocks if sum([s.ob_tapped, s.swing_valid, s.doji_detected,
                                   s.consolidation_detected, s.volume_spiked]) >= 3
    ]
    for sig in engine.rank_signals(multi_signal):
        logger.info(f"  {sig.symbol}: {sig.total_score}")
    
    logger.info("\n📊 High Volume Stocks (>1M):")
    high_vol = [s for s in stocks if s.volume > 1000000]
    for sig in engine.rank_signals(high_vol):
        logger.info(f"  {sig.symbol}: {sig.total_score} (Vol: {sig.volume:,.0f})")


def main():
    logger.info("\n\n")
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + " "*10 + "SIGNAL RANKING ENGINE - USAGE EXAMPLES" + " "*20 + "║")
    logger.info("╚" + "="*68 + "╝")
    
    try:
        example_1_basic_ranking()
        example_2_top_n_stocks()
        example_3_score_breakdown()
        example_4_filter_by_minimum_score()
        example_5_combined_criteria()
        
        logger.info("\n" + "="*70)
        logger.info("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        logger.info("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}\n", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
