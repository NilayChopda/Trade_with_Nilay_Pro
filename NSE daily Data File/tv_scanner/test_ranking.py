"""
Test suite for Signal Ranking Engine (Phase 7)
"""

import pandas as pd
import numpy as np
from core.ranking import SignalRankingEngine, RankedSignal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_test_metrics():
    """Generate test metrics for multiple stocks"""
    stocks = [
        {'symbol': 'RELIANCE.NS', 'close': 2850.50, 'pct_change': 1.25, 'volume': 1500000},
        {'symbol': 'TCS.NS', 'close': 3650.75, 'pct_change': -0.75, 'volume': 800000},
        {'symbol': 'INFY.NS', 'close': 1850.25, 'pct_change': 2.10, 'volume': 2100000},
        {'symbol': 'HDFCBANK.NS', 'close': 1580.00, 'pct_change': 0.50, 'volume': 950000},
        {'symbol': 'WIPRO.NS', 'close': 425.75, 'pct_change': 1.75, 'volume': 3200000},
        {'symbol': 'MARUTI.NS', 'close': 9650.00, 'pct_change': -0.25, 'volume': 450000},
    ]
    return stocks


def test_individual_scoring():
    """Test scoring for individual signals"""
    logger.info("\n" + "="*70)
    logger.info("🧪 TEST 1: Individual Signal Scoring")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics = {'close': 1000.0, 'pct_change': 1.5, 'volume': 1000000}
    
    # Test each signal type
    test_cases = [
        ('STOCK_OB', {'ob_tapped': True}, 5),
        ('STOCK_SWING', {'swing_valid': True}, 3),
        ('STOCK_DOJI', {'doji_detected': True}, 2),
        ('STOCK_CONS', {'consolidation_detected': True}, 2),
        ('STOCK_VOL', {'volume_spiked': True}, 2),
    ]
    
    for name, kwargs, expected_score in test_cases:
        ranked = engine.calculate_rank(name, test_metrics, **kwargs)
        logger.info(f"  {name}: Score={ranked.total_score} (Expected: {expected_score}) ✓")
        assert ranked.total_score == expected_score, f"Score mismatch for {name}"
    
    logger.info("✅ Individual scoring test passed!\n")


def test_combined_scoring():
    """Test combined scoring with multiple signals"""
    logger.info("="*70)
    logger.info("🧪 TEST 2: Combined Signal Scoring")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics = {'close': 1500.0, 'pct_change': 1.0, 'volume': 2000000}
    
    # Test combination: OB + Swing + Doji = 5 + 3 + 2 = 10
    ranked = engine.calculate_rank(
        'TEST_COMBINED',
        test_metrics,
        ob_tapped=True,
        swing_valid=True,
        doji_detected=True
    )
    
    expected_total = 5 + 3 + 2
    logger.info(f"  OB + Swing + Doji: Score={ranked.total_score} (Expected: {expected_total})")
    assert ranked.total_score == expected_total, f"Combined score mismatch"
    
    # Test max score: All signals = 5 + 3 + 2 + 2 + 2 = 14
    ranked_max = engine.calculate_rank(
        'TEST_MAX',
        test_metrics,
        ob_tapped=True,
        swing_valid=True,
        doji_detected=True,
        consolidation_detected=True,
        volume_spiked=True
    )
    
    expected_max = 5 + 3 + 2 + 2 + 2
    logger.info(f"  All signals: Score={ranked_max.total_score} (Expected: {expected_max})")
    assert ranked_max.total_score == expected_max, f"Max score mismatch"
    
    logger.info("✅ Combined scoring test passed!\n")


def test_ranking_and_sorting():
    """Test ranking and sorting of multiple signals"""
    logger.info("="*70)
    logger.info("🧪 TEST 3: Ranking and Sorting")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics_list = generate_test_metrics()
    
    ranked_signals = []
    
    # Create ranked signals with different score combinations
    signal_configs = [
        (0, {'ob_tapped': True, 'swing_valid': True, 'doji_detected': True}),  # 5+3+2=10
        (1, {'swing_valid': True, 'consolidation_detected': True}),  # 3+2=5
        (2, {'ob_tapped': True, 'volume_spiked': True}),  # 5+2=7
        (3, {'doji_detected': True, 'consolidation_detected': True, 'volume_spiked': True}),  # 2+2+2=6
        (4, {'ob_tapped': True}),  # 5
        (5, {'swing_valid': True, 'doji_detected': True}),  # 3+2=5
    ]
    
    for idx, config in signal_configs:
        metrics = test_metrics_list[idx]
        ranked = engine.calculate_rank(metrics['symbol'], metrics, **config)
        ranked_signals.append(ranked)
        logger.info(f"  {metrics['symbol']}: Score={ranked.total_score}")
    
    # Rank and sort
    sorted_signals = engine.rank_signals(ranked_signals)
    logger.info("\n  After sorting:")
    for idx, sig in enumerate(sorted_signals, 1):
        logger.info(f"    {idx}. {sig.symbol}: {sig.total_score}")
    
    # Verify sorting
    scores = [s.total_score for s in sorted_signals]
    assert scores == sorted(scores, reverse=True), "Signals not properly sorted"
    
    logger.info("✅ Ranking and sorting test passed!\n")


def test_top_n_filtering():
    """Test top N filtering"""
    logger.info("="*70)
    logger.info("🧪 TEST 4: Top N Filtering")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics_list = generate_test_metrics()
    
    ranked_signals = []
    for metrics in test_metrics_list:
        ranked = engine.calculate_rank(
            metrics['symbol'],
            metrics,
            ob_tapped=np.random.random() > 0.5,
            swing_valid=np.random.random() > 0.5,
            doji_detected=np.random.random() > 0.5,
            consolidation_detected=np.random.random() > 0.5,
            volume_spiked=np.random.random() > 0.5,
        )
        ranked_signals.append(ranked)
    
    # Get top 3
    top_3 = engine.rank_signals(ranked_signals, top_n=3)
    logger.info(f"  Total signals: {len(ranked_signals)}")
    logger.info(f"  Top 3: {len(top_3)}")
    logger.info(f"  Top 3 scores: {[s.total_score for s in top_3]}")
    
    assert len(top_3) <= 3, "Top N filtering failed"
    logger.info("✅ Top N filtering test passed!\n")


def test_dataframe_conversion():
    """Test conversion to DataFrame"""
    logger.info("="*70)
    logger.info("🧪 TEST 5: DataFrame Conversion")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics_list = generate_test_metrics()
    
    ranked_signals = []
    for metrics in test_metrics_list:
        ranked = engine.calculate_rank(
            metrics['symbol'],
            metrics,
            ob_tapped=True,
            swing_valid=np.random.random() > 0.5,
            doji_detected=np.random.random() > 0.5,
        )
        ranked_signals.append(ranked)
    
    # Convert to DataFrame
    df = engine.to_dataframe(ranked_signals)
    
    logger.info(f"  DataFrame shape: {df.shape}")
    logger.info(f"  Columns: {list(df.columns)}")
    logger.info("\n  DataFrame head:")
    logger.info(f"\n{df.head()}\n")
    
    assert not df.empty, "DataFrame is empty"
    assert 'Rank' in df.columns, "Rank column missing"
    assert 'Total_Score' in df.columns, "Total_Score column missing"
    
    logger.info("✅ DataFrame conversion test passed!\n")


def test_summary_stats():
    """Test summary statistics calculation"""
    logger.info("="*70)
    logger.info("🧪 TEST 6: Summary Statistics")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics_list = generate_test_metrics()
    
    ranked_signals = []
    for metrics in test_metrics_list:
        ranked = engine.calculate_rank(
            metrics['symbol'],
            metrics,
            ob_tapped=np.random.random() > 0.5,
            swing_valid=np.random.random() > 0.5,
            doji_detected=np.random.random() > 0.5,
            consolidation_detected=np.random.random() > 0.5,
            volume_spiked=np.random.random() > 0.5,
        )
        ranked_signals.append(ranked)
    
    stats = engine.get_summary_stats(ranked_signals)
    
    logger.info(f"  Total Signals: {stats['total_signals']}")
    logger.info(f"  Avg Score: {stats['avg_score']:.2f}")
    logger.info(f"  Max Score: {stats['max_score']:.2f}")
    logger.info(f"  Min Score: {stats['min_score']:.2f}")
    logger.info(f"  OB Tapped: {stats['ob_tapped_count']}")
    logger.info(f"  Swing Valid: {stats['swing_valid_count']}")
    logger.info(f"  Doji: {stats['doji_count']}")
    logger.info(f"  Consolidation: {stats['consolidation_count']}")
    logger.info(f"  Volume Spike: {stats['volume_spike_count']}")
    
    assert stats['total_signals'] == len(ranked_signals), "Stats count mismatch"
    logger.info("✅ Summary statistics test passed!\n")


def test_ranking_report():
    """Test ranking report formatting"""
    logger.info("="*70)
    logger.info("🧪 TEST 7: Ranking Report Formatting")
    logger.info("="*70)
    
    engine = SignalRankingEngine()
    test_metrics_list = generate_test_metrics()
    
    ranked_signals = []
    for i, metrics in enumerate(test_metrics_list):
        ranked = engine.calculate_rank(
            metrics['symbol'],
            metrics,
            ob_tapped=i % 2 == 0,
            swing_valid=i % 3 == 0,
            doji_detected=i % 4 == 0,
        )
        ranked_signals.append(ranked)
    
    # Sort and get report
    sorted_signals = engine.rank_signals(ranked_signals, top_n=5)
    report = engine.format_ranking_report(sorted_signals)
    
    logger.info("\n" + report)
    
    assert "SIGNAL RANKING REPORT" in report, "Report missing title"
    assert len(sorted_signals) > 0, "No signals in report"
    
    logger.info("✅ Ranking report formatting test passed!\n")


def main():
    """Run all tests"""
    logger.info("\n\n")
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + " "*15 + "SIGNAL RANKING ENGINE TEST SUITE" + " "*21 + "║")
    logger.info("╚" + "="*68 + "╝")
    
    try:
        test_individual_scoring()
        test_combined_scoring()
        test_ranking_and_sorting()
        test_top_n_filtering()
        test_dataframe_conversion()
        test_summary_stats()
        test_ranking_report()
        
        logger.info("\n" + "="*70)
        logger.info("✅ ALL TESTS PASSED SUCCESSFULLY!")
        logger.info("="*70 + "\n")
        
    except AssertionError as e:
        logger.error(f"\n❌ Test failed: {e}\n")
        return False
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}\n")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
