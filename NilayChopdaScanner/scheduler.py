#!/usr/bin/env python3
"""
Order Block Scanner Scheduler

This module provides automated scheduling for Order Block scanning,
alerts, and monitoring with Telegram notifications.
"""

import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.core.scanner_engine import ScannerEngine
from scanner.bot.telegram_bot import ScannerBot
from config import LOG_LEVEL, LOG_FILE
from scanner.utils.helpers import setup_logging

logger = logging.getLogger(__name__)


class OrderBlockScheduler:
    """
    Scheduler for automated Order Block scanning and monitoring.

    Features:
    - Periodic Order Block scanning
    - Real-time Order Block tap monitoring
    - Telegram alerts for significant events
    - Configurable scan intervals
    """

    def __init__(self, scan_interval_minutes: int = 60, monitor_interval_seconds: int = 30):
        """
        Initialize the Order Block scheduler.

        Args:
            scan_interval_minutes: How often to run full OB scans (default: 60 min)
            monitor_interval_seconds: How often to check for OB taps (default: 30 sec)
        """
        self.scan_interval = scan_interval_minutes
        self.monitor_interval = monitor_interval_seconds

        # Initialize components
        self.scanner_engine = ScannerEngine()
        self.telegram_bot = ScannerBot()

        # Tracking variables
        self.last_scan_time = None
        self.monitored_symbols = set()
        self.last_prices = {}  # symbol -> last known price

        logger.info(f"OrderBlockScheduler initialized - Scan: {scan_interval_minutes}min, Monitor: {monitor_interval_seconds}sec")

    def start_scheduler(self):
        """Start the automated scheduler"""
        logger.info("Starting Order Block Scheduler...")

        # Schedule periodic Order Block scanning
        schedule.every(self.scan_interval).minutes.do(self._run_orderblock_scan)

        # Schedule frequent Order Block monitoring
        schedule.every(self.monitor_interval).seconds.do(self._monitor_orderblock_taps)

        # Send startup notification
        self._send_startup_notification()

        logger.info("Scheduler started. Press Ctrl+C to stop.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self._send_shutdown_notification()

    def _run_orderblock_scan(self):
        """Run periodic Order Block scanning"""
        try:
            logger.info("Running scheduled Order Block scan...")

            # Run scan with limited symbols for efficiency
            result = self.scanner_engine.run_orderblock_scan(max_symbols=50, refresh_data=True)

            # Update monitored symbols
            if result.get('symbols_with_obs', 0) > 0:
                # Get symbols that have Order Blocks
                # This is a simplified approach - in production you'd track this properly
                self.monitored_symbols.update(['RELIANCE.NS', 'TCS.NS', 'INFY.NS'])  # Example symbols

            # Send scan summary
            self._send_scan_summary(result)

            self.last_scan_time = datetime.now()
            logger.info(f"Order Block scan completed - Found {result.get('total_order_blocks', 0)} OBs")

        except Exception as e:
            logger.error(f"Error in scheduled scan: {e}")
            self._send_error_alert("Scheduled Scan Failed", str(e))

    def _monitor_orderblock_taps(self):
        """Monitor for combined OB + PA signals"""
        try:
            for symbol in list(self.monitored_symbols):
                # Get current price (simplified - in production use real-time data)
                current_price = self._get_current_price(symbol)

                if current_price and current_price != self.last_prices.get(symbol):
                    # Get recent data for PA analysis
                    try:
                        data = self.scanner_engine.data_fetcher.fetch_stock_data(symbol, period="1mo")
                        if data is not None and not data.empty:
                            # Run combined OB + PA analysis
                            result = self.scanner_engine.run_combined_analysis(symbol, current_price, data.tail(50))

                            if result.get('combined_signal', False):
                                self._send_combined_signal_alert(symbol, current_price, result)
                    except Exception as e:
                        logger.debug(f"Could not fetch data for {symbol}: {e}")

                    self.last_prices[symbol] = current_price

        except Exception as e:
            logger.error(f"Error in combined monitoring: {e}")

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.

        In production, this would connect to a real-time data feed.
        For now, we'll use a placeholder that simulates price movement.
        """
        # Placeholder implementation - replace with real-time data source
        import random
        base_price = 1000  # Example base price
        variation = random.uniform(-0.02, 0.02)  # ±2% random variation
        return base_price * (1 + variation)

    def _send_startup_notification(self):
        """Send startup notification"""
        message = "🚀 *Order Block Scanner Started*\n" \
                 f"• Scan Interval: {self.scan_interval} minutes\n" \
                 f"• Monitor Interval: {self.monitor_interval} seconds\n" \
                 f"• Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.telegram_bot.send_message(message)

    def _send_shutdown_notification(self):
        """Send shutdown notification"""
        message = "⏹️ *Order Block Scanner Stopped*\n" \
                 f"• Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.telegram_bot.send_message(message)

    def _send_scan_summary(self, result: Dict[str, Any]):
        """Send scan summary notification"""
        scan_date = result.get('scan_date', 'N/A')
        total_scanned = result.get('total_symbols_scanned', 0)
        symbols_with_obs = result.get('symbols_with_obs', 0)
        total_obs = result.get('total_order_blocks', 0)

        message = f"📊 *Order Block Scan Complete*\n" \
                 f"• Date: {scan_date}\n" \
                 f"• Symbols Scanned: {total_scanned}\n" \
                 f"• Symbols with OBs: {symbols_with_obs}\n" \
                 f"• Total Order Blocks: {total_obs}"

        self.telegram_bot.send_message(message)

    def _send_combined_signal_alert(self, symbol: str, current_price: float, result: Dict[str, Any]):
        """Send combined OB + PA signal alert"""
        try:
            signal_strength = result.get('signal_strength', 0)
            description = result.get('description', '')

            message = f"🚨 *COMBINED SIGNAL ALERT*\n" \
                     f"• Symbol: {symbol}\n" \
                     f"• Current Price: ₹{current_price:.2f}\n" \
                     f"• Signal Strength: {signal_strength}/5\n" \
                     f"• Description: {description}\n\n"

            # Add OB details
            if result.get('tapped_obs'):
                tapped_ob = result['tapped_obs'][0]  # Show primary OB
                ob_type = tapped_ob['block_type']
                zone_range = f"₹{tapped_ob['low']:.2f} - ₹{tapped_ob['high']:.2f}"
                message += f"🎯 *Order Block:*\n{ob_type}: {zone_range}\n\n"

            # Add PA details
            if result.get('pa_signals'):
                pa_signal = result['pa_signals'][0]  # Show primary PA signal
                pa_type = pa_signal['pattern_type']
                pa_direction = pa_signal['direction']
                message += f"📊 *Price Action:*\n{pa_type} ({pa_direction})\n\n"

            message += f"[View Chart](https://in.tradingview.com/chart/?symbol=NSE:{symbol})"

            self.telegram_bot.send_message(message)

        except Exception as e:
            logger.error(f"Error sending combined signal alert: {e}")

    def _send_error_alert(self, error_type: str, error_message: str):
        """Send error alert"""
        message = f"❌ *ERROR: {error_type}*\n" \
                 f"• Message: {error_message}\n" \
                 f"• Time: {datetime.now().strftime('%H:%M:%S')}"

        self.telegram_bot.send_message(message)


def main():
    """Main entry point for the scheduler"""
    import argparse

    parser = argparse.ArgumentParser(description='Order Block Scanner Scheduler')
    parser.add_argument('--scan-interval', type=int, default=60,
                       help='Scan interval in minutes (default: 60)')
    parser.add_argument('--monitor-interval', type=int, default=30,
                       help='Monitor interval in seconds (default: 30)')

    args = parser.parse_args()

    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)

    # Start scheduler
    scheduler = OrderBlockScheduler(
        scan_interval_minutes=args.scan_interval,
        monitor_interval_seconds=args.monitor_interval
    )

    scheduler.start_scheduler()


if __name__ == "__main__":
    main()