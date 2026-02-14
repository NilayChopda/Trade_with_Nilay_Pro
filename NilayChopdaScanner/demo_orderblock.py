#!/usr/bin/env python3
"""
Demo Order Block Analysis with Mock Data

This script demonstrates the Order Block Engine functionality
using synthetic price data that exhibits typical market patterns.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.engine.orderblock_engine import OrderBlockEngine


def create_mock_price_data(days=200, start_price=1000, volatility=0.02):
    """
    Create mock price data with guaranteed Order Block patterns.

    Pattern for Bullish OB:
    - Days 30-50: Strong downtrend (impulse)
    - Day 51: Bullish BOS (break above recent high)
    - Day 52: Upward candle (last opposite candle)
    - Creates bullish OB zone

    Pattern for Bearish OB:
    - Days 100-120: Strong uptrend (impulse)
    - Day 121: Bearish BOS (break below recent low)
    - Day 122: Downward candle (last opposite candle)
    - Creates bearish OB zone
    """
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    dates.reverse()

    prices = []
    highs, lows, opens, closes, volumes = [], [], [], [], []

    for i in range(days):
        if i < 30:
            # Initial ranging
            trend = 0.0005
            vol = volatility * 0.3
            price_change = np.random.normal(trend, vol)
        elif i < 50:
            # Strong downtrend (impulse for bullish OB)
            trend = -0.008
            vol = volatility * 2.0
            price_change = np.random.normal(trend, vol)
        elif i == 50:
            # Bullish BOS - strong upward breakout
            price_change = 0.05  # 5% breakout
        elif i == 51:
            # Last opposite candle - upward
            price_change = 0.02
        elif i < 100:
            # Sideways/consolidation
            trend = 0.0002
            vol = volatility * 0.5
            price_change = np.random.normal(trend, vol)
        elif i < 120:
            # Strong uptrend (impulse for bearish OB)
            trend = 0.008
            vol = volatility * 2.0
            price_change = np.random.normal(trend, vol)
        elif i == 120:
            # Bearish BOS - strong downward breakout
            price_change = -0.05  # 5% breakdown
        elif i == 121:
            # Last opposite candle - downward
            price_change = -0.02
        else:
            # Final ranging
            trend = 0.0001
            vol = volatility * 0.3
            price_change = np.random.normal(trend, vol)

        if i == 0:
            price = start_price
            open_price = price
            close_price = price
            high = price
            low = price
        else:
            price = prices[-1] * (1 + price_change)
            close_price = price

            if i in [50, 51, 120, 121]:  # BOS and opposite candles
                # Make these candles more significant
                spread = 0.03  # 3% spread
                high = price * (1 + spread)
                low = price * (1 - spread)
                open_price = prices[-1] * (1 + price_change * 0.5)  # Partial gap
            else:
                spread = abs(np.random.normal(0, vol * 2))
                high = price * (1 + spread)
                low = price * (1 - spread)
                open_price = prices[-1] * (1 + np.random.normal(0, vol/2))

        # Ensure OHLC relationships
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)

        highs.append(high)
        lows.append(low)
        opens.append(open_price)
        closes.append(close_price)
        volumes.append(np.random.randint(1000000, 5000000) if i in [50, 51, 120, 121] else np.random.randint(200000, 1000000))

        prices.append(price)

    # Create DataFrame
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    }, index=pd.DatetimeIndex(dates))

    return data


def demo_orderblock_analysis():
    """Demonstrate Order Block analysis on mock data"""
    print("=== Order Block Engine Demo ===\n")

    # Create mock data
    print("Creating mock price data...")
    mock_data = create_mock_price_data(days=200, start_price=1000, volatility=0.015)
    print(f"Generated {len(mock_data)} days of price data")
    print(".2f")
    print(".2f")
    print()

    # Initialize Order Block Engine
    ob_engine = OrderBlockEngine()

    # Analyze for Order Blocks
    print("Analyzing for Order Blocks...")
    symbol = "DEMO.NS"
    order_blocks = ob_engine.analyze_price_data(symbol, mock_data)

    print(f"Found {len(order_blocks)} Order Blocks\n")

    # Display results
    if order_blocks:
        print("=== Detected Order Blocks ===")
        for i, ob in enumerate(order_blocks, 1):
            print(f"{i}. {ob.block_type}")
            print(".2f")
            print(f"   Strength: {ob.strength}/5")
            print(f"   Entry Date: {ob.entry_time.date()}")
            print(f"   Tapped: {'Yes' if ob.tapped else 'No'}")
            print()

        # Save Order Blocks
        print("Saving Order Blocks...")
        ob_engine.save_order_blocks(symbol, order_blocks)
        print("Order Blocks saved successfully!\n")

        # Test zone tapping
        print("=== Testing Zone Tapping ===")
        current_price = mock_data['Close'].iloc[-1]
        print(".2f")

        tapped_zones = [ob for ob in order_blocks if ob.is_tapped(current_price)]
        if tapped_zones:
            print(f"🚨 ALERT: {len(tapped_zones)} Order Block(s) tapped!")
            for ob in tapped_zones:
                zone_range = ".2f"
                print(f"  {ob.block_type}: {zone_range} (Strength: {ob.strength}/5)")
        else:
            print("ℹ️  No Order Block taps detected at current price")

        print()

        # Show summary
        print("=== Order Block Summary ===")
        summary = ob_engine.get_order_block_summary(symbol)
        print(f"Symbol: {summary['symbol']}")
        print(f"Total Order Blocks: {summary['total_obs']}")
        print(f"Bullish OBs: {summary['bullish_obs']}")
        print(f"Bearish OBs: {summary['bearish_obs']}")
        print(f"Tapped OBs: {summary['tapped_obs']}")
        print(".2f")
        if summary['most_recent_ob']:
            print(f"Most Recent OB: {summary['most_recent_ob']}")

    else:
        print("No Order Blocks detected in the mock data.")
        print("This could be because:")
        print("- The mock data doesn't have clear impulse/BOS patterns")
        print("- Parameters need adjustment for different market conditions")
        print("- The algorithm is working correctly but no valid setups were found")

    print("\n=== Demo Complete ===")
    print("The Order Block Engine is ready for real market data!")


if __name__ == "__main__":
    demo_orderblock_analysis()