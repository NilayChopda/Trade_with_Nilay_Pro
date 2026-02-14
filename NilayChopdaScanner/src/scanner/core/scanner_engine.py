"""
Core scanner engine for stock scanning
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from scanner.data.data_fetcher import DataFetcher
from scanner.data.stock_universe import StockUniverse
from scanner.core.swing_scanner import SwingScanner
from scanner.engine.orderblock_engine import OrderBlockEngine
from scanner.engine.price_action import PriceActionEngine
from scanner.bot.telegram_bot import ScannerBot


class ScannerEngine:
    """Main scanner engine class"""

    def __init__(self, data_fetcher: DataFetcher = None, stock_universe: StockUniverse = None,
                 swing_scanner: SwingScanner = None, orderblock_engine: OrderBlockEngine = None,
                 price_action_engine: PriceActionEngine = None, telegram_bot: ScannerBot = None):
        """
        Initialize the scanner engine.

        Args:
            data_fetcher (DataFetcher): Data fetching component
            stock_universe (StockUniverse): Stock universe manager
            swing_scanner (SwingScanner): Swing trading scanner
            orderblock_engine (OrderBlockEngine): Order Block detection engine
            price_action_engine (PriceActionEngine): Price Action pattern detection engine
            telegram_bot (ScannerBot): Telegram notification bot
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.stock_universe = stock_universe or StockUniverse()
        self.swing_scanner = swing_scanner or SwingScanner(self.data_fetcher)
        self.orderblock_engine = orderblock_engine or OrderBlockEngine()
        self.price_action_engine = price_action_engine or PriceActionEngine()
        self.telegram_bot = telegram_bot or ScannerBot()
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """Run the scanning process"""
        self.logger.info("Starting scan...")
        # TODO: Implement scanning logic
        pass

    def run_swing_scan(self, max_symbols: int = None, refresh_data: bool = False) -> Dict[str, Any]:
        """
        Run the swing trading scanner on the stock universe.

        Args:
            max_symbols (int): Maximum number of symbols to scan (None for all)
            refresh_data (bool): Whether to refresh stock data before scanning

        Returns:
            Dict: Scan results summary
        """
        self.logger.info("Starting swing trading scan...")

        try:
            # Get symbols to scan
            all_symbols = self.stock_universe.get_all_nse_symbols()
            if max_symbols:
                all_symbols = all_symbols[:max_symbols]
                self.logger.info(f"Limited scan to {max_symbols} symbols")

            # Run swing scan
            scan_results = self.swing_scanner.scan_symbols(all_symbols, refresh_data)

            # Prepare summary
            summary = {
                'scan_type': 'swing_trading',
                'scan_date': datetime.now().date(),
                'total_symbols_scanned': len(all_symbols),
                'qualifying_stocks': len(scan_results),
                'success_rate': round((len(scan_results) / len(all_symbols)) * 100, 2) if all_symbols else 0,
                'results': scan_results
            }

            self.logger.info(f"Swing scan completed. Found {len(scan_results)} qualifying stocks")
            return summary

        except Exception as e:
            self.logger.error(f"Error during swing scan: {e}")
            return {
                'scan_type': 'swing_trading',
                'error': str(e),
                'qualifying_stocks': 0,
                'results': []
            }

    def run_orderblock_scan(self, max_symbols: int = None, refresh_data: bool = False) -> Dict[str, Any]:
        """
        Run Order Block analysis on the stock universe.

        Args:
            max_symbols (int): Maximum number of symbols to scan (None for all)
            refresh_data (bool): Whether to refresh stock data before scanning

        Returns:
            Dict: Order Block scan results summary
        """
        self.logger.info("Starting Order Block scan...")

        try:
            # Get symbols to scan
            all_symbols = self.stock_universe.get_all_nse_symbols()
            if max_symbols:
                all_symbols = all_symbols[:max_symbols]
                self.logger.info(f"Limited scan to {max_symbols} symbols")

            total_obs_found = 0
            symbols_with_obs = 0
            all_order_blocks = []

            # Analyze each symbol for Order Blocks
            for symbol in all_symbols:
                try:
                    # Get stock data
                    data = self._get_stock_data_for_ob(symbol, refresh_data)
                    if data is None:
                        continue

                    # Analyze for Order Blocks
                    order_blocks = self.orderblock_engine.analyze_price_data(symbol, data)

                    if order_blocks:
                        symbols_with_obs += 1
                        total_obs_found += len(order_blocks)
                        all_order_blocks.extend(order_blocks)

                        # Save Order Blocks for this symbol
                        self.orderblock_engine.save_order_blocks(symbol, order_blocks)

                        self.logger.debug(f"Found {len(order_blocks)} Order Blocks for {symbol}")

                except Exception as e:
                    self.logger.warning(f"Error analyzing {symbol} for Order Blocks: {e}")
                    continue

            # Prepare summary
            summary = {
                'scan_type': 'order_blocks',
                'scan_date': datetime.now().date(),
                'total_symbols_scanned': len(all_symbols),
                'symbols_with_obs': symbols_with_obs,
                'total_order_blocks': total_obs_found,
                'order_blocks': [ob.to_dict() for ob in all_order_blocks[:50]]  # Limit for summary
            }

            self.logger.info(f"Order Block scan completed. Found {total_obs_found} Order Blocks across {symbols_with_obs} symbols")
            return summary

        except Exception as e:
            self.logger.error(f"Error during Order Block scan: {e}")
            return {
                'scan_type': 'order_blocks',
                'error': str(e),
                'total_order_blocks': 0,
                'order_blocks': []
            }

    def monitor_orderblock_taps(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """
        Monitor and alert when Order Block zones are tapped.

        Args:
            symbol (str): Stock symbol to monitor
            current_price (float): Current market price

        Returns:
            List[Dict]: Tapped Order Blocks
        """
        try:
            # Load existing Order Blocks for this symbol
            order_blocks = self.orderblock_engine.load_order_blocks(symbol)

            if not order_blocks:
                return []

            # Check for tapped zones
            tapped_obs = self.orderblock_engine.check_tapped_zones(symbol, current_price, order_blocks)

            # Send alerts for newly tapped zones
            for ob in tapped_obs:
                if ob.tapped and ob.tapped_time:  # Newly tapped
                    self.telegram_bot.send_order_block_alert(symbol, ob, current_price)

            # Save updated Order Blocks
            self.orderblock_engine.save_order_blocks(symbol, order_blocks)

            return [ob.to_dict() for ob in tapped_obs]

        except Exception as e:
            self.logger.error(f"Error monitoring Order Block taps for {symbol}: {e}")
            return []

    def run_combined_analysis(self, symbol: str, current_price: float, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run combined Order Block + Price Action analysis.

        Signals fire only when:
        1. Order Block is tapped AND
        2. At least one Price Action condition is true

        Args:
            symbol: Stock symbol
            current_price: Current market price
            data: Recent OHLCV data for PA analysis

        Returns:
            Dict with analysis results and signals
        """
        try:
            results = {
                'symbol': symbol,
                'current_price': current_price,
                'ob_tapped': False,
                'pa_signals': [],
                'combined_signal': False,
                'signal_strength': 0,
                'description': ''
            }

            # 1. Check for Order Block taps
            tapped_obs = self.monitor_orderblock_taps(symbol, current_price)
            if tapped_obs:
                results['ob_tapped'] = True
                results['tapped_obs'] = tapped_obs

            # 2. Check Price Action conditions
            pa_signals = self.price_action_engine.analyze_price_action(data, symbol)
            if pa_signals:
                results['pa_signals'] = [s.__dict__ for s in pa_signals]

            # 3. Generate combined signal
            if results['ob_tapped'] and results['pa_signals']:
                # Calculate combined strength
                ob_strength = max([ob['strength'] for ob in tapped_obs]) if tapped_obs else 0
                pa_strength = max([s['strength'] for s in pa_signals]) if pa_signals else 0
                combined_strength = min(5, (ob_strength + pa_strength) // 2)

                results['combined_signal'] = True
                results['signal_strength'] = combined_strength

                # Create description
                ob_types = [ob['block_type'] for ob in tapped_obs]
                pa_types = list(set([s['pattern_type'] for s in pa_signals]))

                results['description'] = f"OB({'+'.join(ob_types)}) + PA({'+'.join(pa_types)}) - Strength: {combined_strength}/5"

                # Send combined alert
                self._send_combined_alert(symbol, current_price, tapped_obs, pa_signals)

            return results

        except Exception as e:
            self.logger.error(f"Error in combined analysis for {symbol}: {e}")
            return {'error': str(e)}

    def _send_combined_alert(self, symbol: str, current_price: float,
                           tapped_obs: list, pa_signals: list):
        """Send combined OB + PA alert."""
        try:
            # Get the strongest signals
            strongest_ob = max(tapped_obs, key=lambda x: x['strength'])
            strongest_pa = max(pa_signals, key=lambda x: x.strength)

            message = "🚨 *COMBINED SIGNAL ALERT*\n\n" \
                     f"📈 *{symbol}*\n" \
                     f"💰 Current Price: ₹{current_price:.2f}\n\n" \
                     f"🎯 *Order Block Tapped:*\n" \
                     f"• Type: {strongest_ob['block_type']}\n" \
                     f"• Zone: ₹{strongest_ob['low']:.2f} - ₹{strongest_ob['high']:.2f}\n" \
                     f"• Strength: {strongest_ob['strength']}/5\n\n" \
                     f"📊 *Price Action:*\n" \
                     f"• Pattern: {strongest_pa.pattern_type}\n" \
                     f"• Direction: {strongest_pa.direction}\n" \
                     f"• Strength: {strongest_pa.strength}/5\n\n" \
                     f"💪 *Combined Signal Strength: {min(5, (strongest_ob['strength'] + strongest_pa.strength) // 2)}/5*\n\n" \
                     f"[View Chart](https://in.tradingview.com/chart/?symbol=NSE:{symbol})"

            self.telegram_bot.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending combined alert: {e}")

    def get_orderblock_summary(self, symbol: str = None) -> Dict[str, Any]:
        """
        Get Order Block summary for a symbol or overall statistics.

        Args:
            symbol (str): Specific symbol to get summary for, or None for overall stats

        Returns:
            Dict: Order Block summary
        """
        if symbol:
            return self.orderblock_engine.get_order_block_summary(symbol)
        else:
            # Get overall statistics
            all_symbols = self.stock_universe.get_all_nse_symbols()
            total_obs = 0
            symbols_with_obs = 0

            for sym in all_symbols[:100]:  # Sample first 100 for performance
                summary = self.orderblock_engine.get_order_block_summary(sym)
                if summary.get('total_obs', 0) > 0:
                    symbols_with_obs += 1
                    total_obs += summary['total_obs']

            return {
                'total_symbols_analyzed': len(all_symbols),
                'symbols_with_obs': symbols_with_obs,
                'total_order_blocks': total_obs,
                'avg_obs_per_symbol': total_obs / symbols_with_obs if symbols_with_obs > 0 else 0
            }

    def _get_stock_data_for_ob(self, symbol: str, refresh_data: bool) -> Optional[pd.DataFrame]:
        """
        Get stock data specifically for Order Block analysis.

        Args:
            symbol (str): Stock symbol
            refresh_data (bool): Force fresh download

        Returns:
            pd.DataFrame or None: Stock data
        """
        if refresh_data:
            # Try to download fresh data
            data = self.data_fetcher.fetch_stock_data(symbol, period="1y")  # OB analysis needs less data
        else:
            # Try local data first
            data = self.data_fetcher.load_local_data(symbol)
            if data is None or len(data) < 100:  # Need minimum data for OB analysis
                data = self.data_fetcher.fetch_stock_data(symbol, period="1y")

        if data is None or len(data) < 100:
            return None

        # Ensure data is sorted
        data = data.sort_index()
        return data

    def scan_stocks(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Scan given stock symbols"""
        self.logger.info(f"Scanning {len(symbols)} symbols")
        # TODO: Implement stock scanning
        return []

    def get_scan_results(self) -> List[Dict[str, Any]]:
        """Get current scan results"""
        # TODO: Implement results retrieval
        return []

    def fetch_universe_data(self, max_symbols: int = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch the complete stock universe and download data for all symbols.

        Args:
            max_symbols (int): Maximum number of symbols to process (None for all)
            force_refresh (bool): Force refresh of symbol universe

        Returns:
            Dict: Summary of the data fetching operation
        """
        self.logger.info("Starting universe data fetch...")

        # Get all NSE symbols
        try:
            all_symbols = self.stock_universe.get_all_nse_symbols(force_refresh=force_refresh)
            self.logger.info(f"Retrieved {len(all_symbols)} NSE symbols")
        except Exception as e:
            self.logger.error(f"Failed to fetch symbol universe: {e}")
            return {'status': 'failed', 'error': str(e)}

        # Limit symbols if specified
        if max_symbols:
            all_symbols = all_symbols[:max_symbols]
            self.logger.info(f"Limited to {max_symbols} symbols for processing")

        # Download data for all symbols
        try:
            downloaded_data = self.data_fetcher.fetch_multiple_stocks(all_symbols)
            successful_downloads = len(downloaded_data)

            self.logger.info(f"Successfully downloaded data for {successful_downloads}/{len(all_symbols)} symbols")

            return {
                'status': 'completed',
                'total_symbols': len(all_symbols),
                'successful_downloads': successful_downloads,
                'failed_downloads': len(all_symbols) - successful_downloads,
                'data_summary': self.data_fetcher.get_data_summary()
            }

        except Exception as e:
            self.logger.error(f"Failed during data fetching: {e}")
            return {'status': 'failed', 'error': str(e)}

    def update_single_symbol(self, symbol: str) -> bool:
        """
        Update data for a single symbol.

        Args:
            symbol (str): Stock symbol to update

        Returns:
            bool: True if successful
        """
        self.logger.info(f"Updating data for {symbol}")

        try:
            data = self.data_fetcher.fetch_stock_data(symbol)
            return data is not None
        except Exception as e:
            self.logger.error(f"Failed to update {symbol}: {e}")
            return False

    def get_universe_info(self) -> Dict[str, Any]:
        """
        Get information about the current stock universe.

        Returns:
            Dict: Universe statistics
        """
        try:
            symbol_count = self.stock_universe.get_symbol_count()
            downloaded_symbols = self.data_fetcher.get_downloaded_symbols()
            data_summary = self.data_fetcher.get_data_summary()

            return {
                'total_universe_symbols': symbol_count,
                'downloaded_symbols': len(downloaded_symbols),
                'download_percentage': (len(downloaded_symbols) / symbol_count * 100) if symbol_count > 0 else 0,
                'data_summary': data_summary
            }
        except Exception as e:
            self.logger.error(f"Failed to get universe info: {e}")
            return {'error': str(e)}