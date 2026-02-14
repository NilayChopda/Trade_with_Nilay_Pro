#!/usr/bin/env python3
"""
Test Price Action Engine

This script demonstrates the Price Action Engine functionality
and tests the combined OB + PA analysis.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.engine.price_action import PriceActionEngine, PriceActionSignal
from scanner.core.scanner_engine import ScannerEngine


def create_test_data(days=100, start_price=1000):
    """Create test OHLCV data with various price action patterns."""
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    dates.reverse()

    prices = []
    highs, lows, opens, closes, volumes = [], [], [], [], []

    for i in range(days):
        if i == 0:
            price = start_price
        else:
            # Add some trend and volatility
            trend = 0.0005 if i < 50 else -0.0003
            volatility = 0.02
            change = np.random.normal(trend, volatility)
            price = prices[-1] * (1 + change)

        # Create OHLC with realistic spreads
        spread = abs(np.random.normal(0, 0.015))
        high = price * (1 + spread)
        low = price * (1 - spread)
        open_price = prices[-1] if i > 0 else price
        close_price = price

        # Ensure OHLC relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)

        highs.append(high)
        lows.append(low)
        opens.append(open_price)
        closes.append(close_price)
        volumes.append(np.random.randint(100000, 1000000))

        prices.append(price)

    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    }, index=pd.DatetimeIndex(dates))

    return data


def test_price_action_engine():
    """Test the Price Action Engine functionality."""
    print("=== Price Action Engine Test ===\n")

    # Create test data
    print("Creating test data...")
    test_data = create_test_data(days=100, start_price=1000)
    print(f"Generated {len(test_data)} days of test data")
    print(".2f")
    print()

    # Initialize Price Action Engine
    pa_engine = PriceActionEngine()

    # Test individual functions
    print("Testing individual PA functions...")

    # Test is_doji
    recent_data = test_data.tail(5)
    is_doji_result = pa_engine.is_doji(recent_data)
    print(f"is_doji (last 5 bars): {'✅ Detected' if is_doji_result else '❌ Not detected'}")

    # Test is_consolidation
    is_consolidation_result = pa_engine.is_consolidation(test_data.tail(20))
    print(f"is_consolidation (last 20 bars): {'✅ Detected' if is_consolidation_result else '❌ Not detected'}")

    # Test is_rejection
    is_rejection_result = pa_engine.is_rejection(test_data.tail(3))
    print(f"is_rejection (last 3 bars): {'✅ Detected' if is_rejection_result else '❌ Not detected'}")
    print()

    # Test full analysis
    print("Running full Price Action analysis...")
    signals = pa_engine.analyze_price_action(test_data, "TEST.NS")

    print(f"Found {len(signals)} Price Action signals:")
    for signal in signals[:5]:  # Show first 5
        print(f"  • {signal.pattern_type} ({signal.direction}) - Strength: {signal.strength}/5")
    print()

    # Test summary
    summary = pa_engine.get_price_action_summary(signals)
    print("Price Action Summary:")
    print(f"  • Total Signals: {summary['total_signals']}")
    print(f"  • Patterns: {summary['patterns']}")
    print(f"  • Directions: {summary['directions']}")
    print(".2f")
    print()


def test_combined_analysis():
    """Test combined OB + PA analysis."""
    print("=== Combined OB + PA Analysis Test ===\n")

    # Create test data
    test_data = create_test_data(days=200, start_price=1000)

    # Initialize scanner engine
    scanner_engine = ScannerEngine()

    # Test current price (use last close)
    current_price = test_data['Close'].iloc[-1]
    symbol = "TEST.NS"

    print(f"Testing combined analysis for {symbol} at ₹{current_price:.2f}")

    # Run combined analysis
    result = scanner_engine.run_combined_analysis(symbol, current_price, test_data.tail(50))

    print("Analysis Results:")
    print(f"  • OB Tapped: {'✅ Yes' if result['ob_tapped'] else '❌ No'}")
    print(f"  • PA Signals: {len(result['pa_signals'])} detected")
    print(f"  • Combined Signal: {'🚨 ACTIVE' if result['combined_signal'] else '💤 None'}")

    if result['combined_signal']:
        print(f"  • Signal Strength: {result['signal_strength']}/5")
        print(f"  • Description: {result['description']}")

        if result['pa_signals']:
            print("  • Top PA Signals:")
            for pa in result['pa_signals'][:2]:
                print(f"    - {pa['pattern_type']} ({pa['direction']}) - Strength: {pa['strength']}/5")

    print()


def main():
    """Run all tests."""
    print("🧪 Price Action Engine Test Suite\n")

    try:
        test_price_action_engine()
        test_combined_analysis()

        print("✅ All tests completed successfully!")
        print("\n💡 The Price Action Engine is ready for integration with Order Blocks!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()