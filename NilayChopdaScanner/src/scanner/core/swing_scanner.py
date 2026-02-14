"""
Swing Scanner Module

This module implements a swing trading scanner that identifies stocks meeting specific
technical analysis criteria using Weighted Moving Averages (WMA) across multiple timeframes.

Scanner Logic:
1. Daily WMA(1) > Monthly WMA(2) + 1
2. Monthly WMA(2) > Monthly WMA(4) + 2
3. Daily WMA(1) > Weekly WMA(6) + 2
4. Weekly WMA(6) > Weekly WMA(12) + 2
5. Daily WMA(1) > 4 days ago WMA(12) + 2
6. Daily WMA(1) > 2 days ago WMA(20) + 2
7. Daily Close > 20

Timeframes Used:
- Daily: Daily price data
- Weekly: Weekly aggregated data
- Monthly: Monthly aggregated data

WMA Calculation:
- WMA(n) uses linear weights: 1, 2, 3, ..., n
- Formula: WMA = Σ(Pi * wi) / Σ(wi) for i=1 to n
- Most recent price gets highest weight (n)
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from scanner.data.data_fetcher import DataFetcher


class SwingScanner:
    """
    Swing trading scanner using WMA-based technical analysis.

    This scanner evaluates stocks against a set of technical criteria
    designed to identify potential swing trading opportunities.
    """

    def __init__(self, data_fetcher: Optional[DataFetcher] = None):
        """
        Initialize the swing scanner.

        Args:
            data_fetcher (DataFetcher): Data fetching component
        """
        self.data_fetcher = data_fetcher or DataFetcher()
        self.logger = logging.getLogger(__name__)

        # Minimum data requirements (in days)
        self.MIN_DATA_DAYS = 100  # Need at least 100 days of data for reliable calculations

        self.logger.info("SwingScanner initialized")

    def scan_symbols(self, symbols: List[str], refresh_data: bool = False) -> List[Dict[str, Any]]:
        """
        Scan a list of symbols and return those meeting all swing criteria.

        Args:
            symbols (List[str]): List of stock symbols to scan
            refresh_data (bool): Whether to refresh local data before scanning

        Returns:
            List[Dict]: List of dictionaries containing scan results for qualifying stocks
        """
        self.logger.info(f"Starting swing scan for {len(symbols)} symbols")

        qualifying_stocks = []
        total_processed = 0
        total_qualifying = 0

        for symbol in symbols:
            try:
                # Get stock data
                data = self._get_stock_data(symbol, refresh_data)
                if data is None:
                    continue

                total_processed += 1

                # Check if stock meets all criteria
                if self._meets_swing_criteria(data):
                    # Calculate additional metrics for the result
                    metrics = self._calculate_scan_metrics(data)

                    result = {
                        'symbol': symbol,
                        'scan_date': datetime.now().date(),
                        'qualifies': True,
                        'close_price': data['Close'].iloc[-1],
                        'volume': data['Volume'].iloc[-1],
                        **metrics
                    }

                    qualifying_stocks.append(result)
                    total_qualifying += 1

                    self.logger.debug(f"{symbol} qualifies for swing trading")

            except Exception as e:
                self.logger.warning(f"Error scanning {symbol}: {e}")
                continue

        self.logger.info(f"Swing scan completed. Processed: {total_processed}, Qualifying: {total_qualifying}")
        return qualifying_stocks

    def scan_single_symbol(self, symbol: str, refresh_data: bool = False) -> Optional[Dict[str, Any]]:
        """
        Scan a single symbol and return detailed analysis.

        Args:
            symbol (str): Stock symbol to scan
            refresh_data (bool): Whether to refresh data

        Returns:
            Dict or None: Detailed scan result or None if data unavailable
        """
        self.logger.info(f"Detailed scan for {symbol}")

        try:
            data = self._get_stock_data(symbol, refresh_data)
            if data is None:
                return None

            # Check each criterion individually
            criteria_results = self._check_all_criteria(data)
            qualifies = all(criteria_results.values())

            # Calculate metrics
            metrics = self._calculate_scan_metrics(data)

            result = {
                'symbol': symbol,
                'scan_date': datetime.now().date(),
                'qualifies': qualifies,
                'close_price': data['Close'].iloc[-1],
                'volume': data['Volume'].iloc[-1],
                'data_points': len(data),
                'date_range': f"{data.index.min().date()} to {data.index.max().date()}",
                'criteria_results': criteria_results,
                **metrics
            }

            return result

        except Exception as e:
            self.logger.error(f"Error in detailed scan for {symbol}: {e}")
            return None

    def _get_stock_data(self, symbol: str, refresh_data: bool) -> Optional[pd.DataFrame]:
        """
        Get stock data, either from local cache or fresh download.

        Args:
            symbol (str): Stock symbol
            refresh_data (bool): Force fresh download

        Returns:
            pd.DataFrame or None: Stock data with OHLCV columns
        """
        if refresh_data:
            # Download fresh data
            data = self.data_fetcher.fetch_stock_data(symbol, period="2y")
        else:
            # Try local data first
            data = self.data_fetcher.load_local_data(symbol)
            if data is None or len(data) < self.MIN_DATA_DAYS:
                # Download if no local data or insufficient
                data = self.data_fetcher.fetch_stock_data(symbol, period="2y")

        if data is None or len(data) < self.MIN_DATA_DAYS:
            self.logger.debug(f"Insufficient data for {symbol}")
            return None

        # Ensure data is sorted by date
        data = data.sort_index()

        return data

    def _meets_swing_criteria(self, data: pd.DataFrame) -> bool:
        """
        Check if stock data meets all swing trading criteria.

        Args:
            data (pd.DataFrame): Stock OHLCV data

        Returns:
            bool: True if all criteria are met
        """
        try:
            criteria_results = self._check_all_criteria(data)
            return all(criteria_results.values())
        except Exception as e:
            self.logger.warning(f"Error checking criteria: {e}")
            return False

    def _check_all_criteria(self, data: pd.DataFrame) -> Dict[str, bool]:
        """
        Check each swing criterion individually.

        Args:
            data (pd.DataFrame): Stock OHLCV data

        Returns:
            Dict[str, bool]: Results for each criterion
        """
        results = {}

        try:
            # Calculate required timeframes
            daily_data = data.copy()
            weekly_data = self._resample_to_weekly(data)
            monthly_data = self._resample_to_monthly(data)

            # Criterion 1: Daily WMA(1) > Monthly WMA(2) + 1
            daily_wma1 = self._calculate_wma(daily_data['Close'], 1).iloc[-1]
            monthly_wma2 = self._calculate_wma(monthly_data['Close'], 2).iloc[-1]
            results['daily_wma1_gt_monthly_wma2_plus_1'] = daily_wma1 > (monthly_wma2 + 1)

            # Criterion 2: Monthly WMA(2) > Monthly WMA(4) + 2
            monthly_wma4 = self._calculate_wma(monthly_data['Close'], 4).iloc[-1]
            results['monthly_wma2_gt_monthly_wma4_plus_2'] = monthly_wma2 > (monthly_wma4 + 2)

            # Criterion 3: Daily WMA(1) > Weekly WMA(6) + 2
            weekly_wma6 = self._calculate_wma(weekly_data['Close'], 6).iloc[-1]
            results['daily_wma1_gt_weekly_wma6_plus_2'] = daily_wma1 > (weekly_wma6 + 2)

            # Criterion 4: Weekly WMA(6) > Weekly WMA(12) + 2
            weekly_wma12 = self._calculate_wma(weekly_data['Close'], 12).iloc[-1]
            results['weekly_wma6_gt_weekly_wma12_plus_2'] = weekly_wma6 > (weekly_wma12 + 2)

            # Criterion 5: Daily WMA(1) > 4 days ago WMA(12) + 2
            if len(daily_data) >= 16:  # Need at least 16 days for WMA(12) 4 days ago
                wma12_4days_ago = self._calculate_wma(daily_data['Close'][:-4], 12).iloc[-1]
                results['daily_wma1_gt_4day_ago_wma12_plus_2'] = daily_wma1 > (wma12_4days_ago + 2)
            else:
                results['daily_wma1_gt_4day_ago_wma12_plus_2'] = False

            # Criterion 6: Daily WMA(1) > 2 days ago WMA(20) + 2
            if len(daily_data) >= 22:  # Need at least 22 days for WMA(20) 2 days ago
                wma20_2days_ago = self._calculate_wma(daily_data['Close'][:-2], 20).iloc[-1]
                results['daily_wma1_gt_2day_ago_wma20_plus_2'] = daily_wma1 > (wma20_2days_ago + 2)
            else:
                results['daily_wma1_gt_2day_ago_wma20_plus_2'] = False

            # Criterion 7: Daily Close > 20
            daily_close = daily_data['Close'].iloc[-1]
            results['daily_close_gt_20'] = daily_close > 20

        except Exception as e:
            self.logger.warning(f"Error calculating criteria: {e}")
            # Set all criteria to False on error
            results = {key: False for key in [
                'daily_wma1_gt_monthly_wma2_plus_1',
                'monthly_wma2_gt_monthly_wma4_plus_2',
                'daily_wma1_gt_weekly_wma6_plus_2',
                'weekly_wma6_gt_weekly_wma12_plus_2',
                'daily_wma1_gt_4day_ago_wma12_plus_2',
                'daily_wma1_gt_2day_ago_wma20_plus_2',
                'daily_close_gt_20'
            ]}

        return results

    def _calculate_wma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Weighted Moving Average with linear weights.

        Args:
            prices (pd.Series): Price series
            period (int): WMA period

        Returns:
            pd.Series: WMA values
        """
        if len(prices) < period:
            return pd.Series([np.nan] * len(prices), index=prices.index)

        # Create weights: 1, 2, 3, ..., period
        weights = np.arange(1, period + 1)

        # Calculate WMA using rolling window
        def weighted_avg(window):
            if len(window) < period:
                return np.nan
            return np.sum(window * weights[-len(window):]) / np.sum(weights[-len(window):])

        return prices.rolling(window=period).apply(weighted_avg, raw=False)

    def _resample_to_weekly(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily data to weekly data.

        Args:
            daily_data (pd.DataFrame): Daily OHLCV data

        Returns:
            pd.DataFrame: Weekly OHLCV data
        """
        # Resample to weekly (W-Fri means week ending Friday)
        weekly = daily_data.resample('W-FRI').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        return weekly

    def _resample_to_monthly(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily data to monthly data.

        Args:
            daily_data (pd.DataFrame): Daily OHLCV data

        Returns:
            pd.DataFrame: Monthly OHLCV data
        """
        # Resample to monthly end
        monthly = daily_data.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        return monthly

    def _calculate_scan_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate additional metrics for scan results.

        Args:
            data (pd.DataFrame): Stock data

        Returns:
            Dict: Additional metrics
        """
        try:
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price

            # Calculate returns
            daily_return = ((current_price - prev_close) / prev_close) * 100

            # Calculate volatility (20-day standard deviation of returns)
            returns = data['Close'].pct_change().dropna()
            volatility = returns.tail(20).std() * np.sqrt(252) * 100  # Annualized

            # Calculate volume metrics
            avg_volume_20 = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

            return {
                'daily_return_pct': round(daily_return, 2),
                'volatility_pct': round(volatility, 2) if not np.isnan(volatility) else 0,
                'avg_volume_20d': int(avg_volume_20),
                'volume_ratio': round(volume_ratio, 2),
                'price_change_5d': self._calculate_price_change(data, 5),
                'price_change_20d': self._calculate_price_change(data, 20),
                'price_change_60d': self._calculate_price_change(data, 60)
            }

        except Exception as e:
            self.logger.warning(f"Error calculating metrics: {e}")
            return {
                'daily_return_pct': 0,
                'volatility_pct': 0,
                'avg_volume_20d': 0,
                'volume_ratio': 1,
                'price_change_5d': 0,
                'price_change_20d': 0,
                'price_change_60d': 0
            }

    def _calculate_price_change(self, data: pd.DataFrame, days: int) -> float:
        """
        Calculate price change over specified number of days.

        Args:
            data (pd.DataFrame): Stock data
            days (int): Number of days to look back

        Returns:
            float: Percentage price change
        """
        if len(data) <= days:
            return 0

        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-days-1]

        if past_price == 0:
            return 0

        return round(((current_price - past_price) / past_price) * 100, 2)