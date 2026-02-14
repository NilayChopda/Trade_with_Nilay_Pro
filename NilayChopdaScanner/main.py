#!/usr/bin/env python3
"""
Main entry point for NilayChopdaScanner
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import LOG_LEVEL, LOG_FILE
from scanner.core.scanner_engine import ScannerEngine
from scanner.utils.helpers import setup_logging


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='NilayChopdaScanner - Stock Scanning System')
    parser.add_argument('--swing-scan', action='store_true', help='Run swing trading scan')
    parser.add_argument('--orderblock-scan', action='store_true', help='Run Order Block analysis')
    parser.add_argument('--monitor-ob', nargs=2, metavar=('SYMBOL', 'PRICE'),
                       help='Monitor Order Block taps for SYMBOL at PRICE')
    parser.add_argument('--combined-analysis', nargs=2, metavar=('SYMBOL', 'PRICE'),
                       help='Run combined OB + Price Action analysis for SYMBOL at PRICE')
    parser.add_argument('--scheduler', action='store_true', help='Start automated Order Block scheduler')
    parser.add_argument('--scan-interval', type=int, default=60,
                       help='Scheduler scan interval in minutes (default: 60)')
    parser.add_argument('--monitor-interval', type=int, default=30,
                       help='Scheduler monitor interval in seconds (default: 30)')
    parser.add_argument('--max-symbols', type=int, default=100, help='Maximum symbols to scan (default: 100)')
    parser.add_argument('--refresh-data', action='store_true', help='Refresh stock data before scanning')
    parser.add_argument('--fetch-universe', action='store_true', help='Fetch universe data')
    parser.add_argument('--universe-info', action='store_true', help='Show universe information')
    parser.add_argument('--ob-summary', nargs='?', const='all', metavar='SYMBOL',
                       help='Show Order Block summary (for specific symbol or all)')

    args = parser.parse_args()

    try:
        # Setup logging
        setup_logging(LOG_LEVEL, LOG_FILE)

        logger = logging.getLogger(__name__)
        logger.info("Starting NilayChopdaScanner...")

        # Initialize components
        scanner_engine = ScannerEngine()

        if args.universe_info:
            # Show universe information
            info = scanner_engine.get_universe_info()
            print("=== Universe Information ===")
            print(f"Total Universe Symbols: {info.get('total_universe_symbols', 0)}")
            print(f"Downloaded Symbols: {info.get('downloaded_symbols', 0)}")
            print(".1f")
            print(f"Data Summary: {info.get('data_summary', {})}")

        elif args.fetch_universe:
            # Fetch universe data
            logger.info("Fetching universe data...")
            result = scanner_engine.fetch_universe_data(max_symbols=args.max_symbols)
            print("=== Data Fetch Results ===")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Total Symbols: {result.get('total_symbols', 0)}")
            print(f"Successful Downloads: {result.get('successful_downloads', 0)}")
            print(f"Failed Downloads: {result.get('failed_downloads', 0)}")

        elif args.orderblock_scan:
            # Run Order Block analysis
            logger.info("Running Order Block analysis...")
            result = scanner_engine.run_orderblock_scan(max_symbols=args.max_symbols, refresh_data=args.refresh_data)

            print("=== Order Block Analysis Results ===")
            print(f"Scan Date: {result.get('scan_date', 'N/A')}")
            print(f"Total Symbols Scanned: {result.get('total_symbols_scanned', 0)}")
            print(f"Symbols with Order Blocks: {result.get('symbols_with_obs', 0)}")
            print(f"Total Order Blocks Found: {result.get('total_order_blocks', 0)}")

        elif args.monitor_ob:
            # Monitor Order Block taps
            symbol, price_str = args.monitor_ob
            try:
                current_price = float(price_str)
                tapped_obs = scanner_engine.monitor_orderblock_taps(symbol, current_price)

                if tapped_obs:
                    print(f"🚨 ALERT: {len(tapped_obs)} Order Block(s) tapped for {symbol} at ₹{current_price}")
                    for ob in tapped_obs:
                        ob_type = ob['block_type']
                        zone_range = f"₹{ob['low']:.2f} - ₹{ob['high']:.2f}"
                        strength = ob['strength']
                        print(f"  {ob_type}: {zone_range} (Strength: {strength}/5)")
                else:
                    print(f"ℹ️  No Order Block taps detected for {symbol} at ₹{current_price}")

            except ValueError:
                print("❌ Error: Invalid price format. Use a number like 150.50")

        elif args.combined_analysis:
            # Run combined OB + Price Action analysis
            symbol, price_str = args.combined_analysis
            try:
                current_price = float(price_str)

                # Get recent data for PA analysis
                data = scanner_engine.data_fetcher.fetch_stock_data(symbol, period="3mo")
                if data is None or data.empty:
                    print(f"❌ No data available for {symbol}")
                    return

                # Run combined analysis
                result = scanner_engine.run_combined_analysis(symbol, current_price, data)

                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print("=== Combined OB + Price Action Analysis ===")
                    print(f"Symbol: {result['symbol']}")
                    print(f"Current Price: ₹{result['current_price']:.2f}")
                    print(f"OB Tapped: {'✅ Yes' if result['ob_tapped'] else '❌ No'}")
                    print(f"PA Signals: {len(result['pa_signals'])} detected")
                    print(f"Combined Signal: {'🚨 ACTIVE' if result['combined_signal'] else '💤 None'}")

                    if result['combined_signal']:
                        print(f"Signal Strength: {result['signal_strength']}/5")
                        print(f"Description: {result['description']}")

                        if result['pa_signals']:
                            print("\nPrice Action Signals:")
                            for pa in result['pa_signals'][:3]:  # Show top 3
                                print(f"  • {pa['pattern_type']} ({pa['direction']}) - Strength: {pa['strength']}/5")

            except ValueError:
                print("❌ Error: Invalid price format. Use a number like 150.50")

        elif args.scheduler:
            # Start automated Order Block scheduler
            from scheduler import OrderBlockScheduler
            scheduler = OrderBlockScheduler(
                scan_interval_minutes=args.scan_interval,
                monitor_interval_seconds=args.monitor_interval
            )
            scheduler.start_scheduler()

        elif args.ob_summary:
            # Show Order Block summary
            if args.ob_summary == 'all':
                summary = scanner_engine.get_orderblock_summary()
                print("=== Overall Order Block Summary ===")
                print(f"Total Symbols Analyzed: {summary.get('total_symbols_analyzed', 0)}")
                print(f"Symbols with Order Blocks: {summary.get('symbols_with_obs', 0)}")
                print(f"Total Order Blocks: {summary.get('total_order_blocks', 0)}")
                print(".2f")
            else:
                summary = scanner_engine.get_orderblock_summary(args.ob_summary)
                print(f"=== Order Block Summary for {args.ob_summary} ===")
                print(f"Total Order Blocks: {summary.get('total_obs', 0)}")
                print(f"Bullish OBs: {summary.get('bullish_obs', 0)}")
                print(f"Bearish OBs: {summary.get('bearish_obs', 0)}")
                print(f"Tapped OBs: {summary.get('tapped_obs', 0)}")
                print(".2f")
                if summary.get('most_recent_ob'):
                    print(f"Most Recent OB: {summary['most_recent_ob']}")

        elif args.swing_scan:
            # Run swing trading scan
            logger.info("Running swing trading scan...")
            result = scanner_engine.run_swing_scan(max_symbols=args.max_symbols, refresh_data=args.refresh_data)

            print("=== Swing Trading Scan Results ===")
            print(f"Scan Date: {result.get('scan_date', 'N/A')}")
            print(f"Total Symbols Scanned: {result.get('total_symbols_scanned', 0)}")
            print(f"Qualifying Stocks: {result.get('qualifying_stocks', 0)}")
            print(".2f")

            if result.get('qualifying_stocks', 0) > 0:
                print("\n=== Qualifying Stocks ===")
                for stock in result.get('results', []):
                    print(f"Symbol: {stock['symbol']}, Price: ₹{stock['close_price']:.2f}, "
                          f"Volume: {stock['volume']:,}, Return: {stock.get('daily_return_pct', 0):.2f}%")

        else:
            # Default: Show help
            logger.info("Scanner initialized. Use --help for available options.")
            parser.print_help()

        logger.info("NilayChopdaScanner completed successfully.")

    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()