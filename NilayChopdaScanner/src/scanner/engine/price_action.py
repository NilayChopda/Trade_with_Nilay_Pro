"""
Price Action Engine

This module implements price action pattern detection for technical analysis.
Price action patterns help identify potential turning points and continuation signals.

Supported Patterns:
- Doji: Indecision candle with small body
- Long Wick Rejection: Price rejection with long wick
- Inside Bar: Bar contained within previous bar's range
- ATR-based Consolidation: Low volatility consolidation zones
- Simple Breakout: Break above resistance or below support

Integration:
- Works with Order Block and Swing scanners
- Signals fire only when OB is tapped AND price action condition is met
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from config import DATA_DIR


@dataclass
class PriceActionSignal:
    """
    Represents a detected price action signal.
    """
    pattern_type: str  # 'DOJI', 'REJECTION', 'INSIDE_BAR', 'CONSOLIDATION', 'BREAKOUT'
    direction: str     # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: int      # Signal strength (1-5)
    bar_index: int     # Index of the signal bar
    bar_time: pd.Timestamp  # Time of the signal bar
    price: float       # Price at signal
    description: str   # Human-readable description


class PriceActionEngine:
    """
    Engine for detecting price action patterns and generating signals.

    This engine analyzes candlestick patterns and price behavior to identify
    potential trading opportunities, especially when combined with Order Blocks.
    """

    def __init__(self):
        """
        Initialize the Price Action Engine.
        """
        self.logger = logging.getLogger(__name__)

        # Pattern detection parameters
        self.DOJI_BODY_RATIO = 0.1  # Max body size as % of total range for doji
        self.REJECTION_WICK_RATIO = 0.6  # Min wick size as % of total range
        self.INSIDE_BAR_RATIO = 0.8  # Min containment ratio for inside bars
        self.CONSOLIDATION_ATR_RATIO = 0.5  # Max ATR ratio for consolidation
        self.CONSOLIDATION_PERIOD = 10  # Lookback period for consolidation
        self.BREAKOUT_STRENGTH = 1.5  # Min breakout strength multiplier

        self.logger.info("PriceActionEngine initialized")

    def analyze_price_action(self, data: pd.DataFrame, symbol: str = "") -> List[PriceActionSignal]:
        """
        Analyze price data for all supported price action patterns.

        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol (for logging)

        Returns:
            List of detected PriceActionSignal objects
        """
        if not self._validate_data(data):
            self.logger.warning(f"Invalid data for price action analysis: {symbol}")
            return []

        signals = []

        try:
            # Detect each pattern type
            doji_signals = self._detect_doji_patterns(data)
            rejection_signals = self._detect_rejection_patterns(data)
            inside_bar_signals = self._detect_inside_bar_patterns(data)
            consolidation_signals = self._detect_consolidation_patterns(data)
            breakout_signals = self._detect_breakout_patterns(data)

            # Combine all signals
            signals.extend(doji_signals)
            signals.extend(rejection_signals)
            signals.extend(inside_bar_signals)
            signals.extend(consolidation_signals)
            signals.extend(breakout_signals)

            # Sort by bar index (most recent first)
            signals.sort(key=lambda x: x.bar_index, reverse=True)

            self.logger.info(f"Found {len(signals)} price action signals for {symbol}")
            return signals

        except Exception as e:
            self.logger.error(f"Error analyzing price action for {symbol}: {e}")
            return []

    def is_doji(self, data: pd.DataFrame, lookback: int = 1) -> bool:
        """
        Check if the most recent candle(s) form a doji pattern.

        Args:
            data: OHLCV DataFrame
            lookback: Number of recent candles to check

        Returns:
            True if doji pattern detected
        """
        if len(data) < lookback:
            return False

        recent_data = data.tail(lookback)
        doji_signals = self._detect_doji_patterns(recent_data)

        return len(doji_signals) > 0

    def is_consolidation(self, data: pd.DataFrame, lookback: int = 10) -> bool:
        """
        Check if price is in a consolidation phase.

        Args:
            data: OHLCV DataFrame
            lookback: Number of candles to analyze

        Returns:
            True if consolidation detected
        """
        if len(data) < lookback:
            return False

        recent_data = data.tail(lookback)
        consolidation_signals = self._detect_consolidation_patterns(recent_data)

        return len(consolidation_signals) > 0

    def is_rejection(self, data: pd.DataFrame, lookback: int = 1) -> bool:
        """
        Check if the most recent candle(s) show rejection patterns.

        Args:
            data: OHLCV DataFrame
            lookback: Number of recent candles to check

        Returns:
            True if rejection pattern detected
        """
        if len(data) < lookback:
            return False

        recent_data = data.tail(lookback)
        rejection_signals = self._detect_rejection_patterns(recent_data)

        return len(rejection_signals) > 0

    def _detect_doji_patterns(self, data: pd.DataFrame) -> List[PriceActionSignal]:
        """Detect doji candlestick patterns."""
        signals = []

        for i in range(len(data)):
            high = data.iloc[i]['High']
            low = data.iloc[i]['Low']
            open_price = data.iloc[i]['Open']
            close_price = data.iloc[i]['Close']

            # Calculate body and total range
            body_size = abs(close_price - open_price)
            total_range = high - low

            if total_range == 0:
                continue

            body_ratio = body_size / total_range

            # Doji has very small body relative to total range
            if body_ratio <= self.DOJI_BODY_RATIO:
                # Determine direction based on wick sizes
                upper_wick = high - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low

                if upper_wick > lower_wick * 1.5:
                    direction = 'BEARISH'  # More rejection at top
                    strength = 3
                elif lower_wick > upper_wick * 1.5:
                    direction = 'BULLISH'  # More rejection at bottom
                    strength = 3
                else:
                    direction = 'NEUTRAL'  # Balanced doji
                    strength = 2

                signal = PriceActionSignal(
                    pattern_type='DOJI',
                    direction=direction,
                    strength=strength,
                    bar_index=i,
                    bar_time=data.index[i],
                    price=close_price,
                    description=f"Doji pattern detected ({direction.lower()})"
                )
                signals.append(signal)

        return signals

    def _detect_rejection_patterns(self, data: pd.DataFrame) -> List[PriceActionSignal]:
        """Detect long wick rejection patterns."""
        signals = []

        for i in range(len(data)):
            high = data.iloc[i]['High']
            low = data.iloc[i]['Low']
            open_price = data.iloc[i]['Open']
            close_price = data.iloc[i]['Close']

            total_range = high - low
            if total_range == 0:
                continue

            # Calculate wick sizes
            upper_wick = high - max(open_price, close_price)
            lower_wick = min(open_price, close_price) - low
            body_high = max(open_price, close_price)
            body_low = min(open_price, close_price)

            # Check for long upper wick rejection (bearish)
            if upper_wick >= total_range * self.REJECTION_WICK_RATIO:
                # Body should be in lower portion
                if body_high <= (high + low) / 2:
                    signal = PriceActionSignal(
                        pattern_type='REJECTION',
                        direction='BEARISH',
                        strength=4,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=close_price,
                        description="Long upper wick rejection (bearish)"
                    )
                    signals.append(signal)

            # Check for long lower wick rejection (bullish)
            if lower_wick >= total_range * self.REJECTION_WICK_RATIO:
                # Body should be in upper portion
                if body_low >= (high + low) / 2:
                    signal = PriceActionSignal(
                        pattern_type='REJECTION',
                        direction='BULLISH',
                        strength=4,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=close_price,
                        description="Long lower wick rejection (bullish)"
                    )
                    signals.append(signal)

        return signals

    def _detect_inside_bar_patterns(self, data: pd.DataFrame) -> List[PriceActionSignal]:
        """Detect inside bar patterns."""
        signals = []

        for i in range(1, len(data)):
            current_high = data.iloc[i]['High']
            current_low = data.iloc[i]['Low']
            current_range = current_high - current_low

            prev_high = data.iloc[i-1]['High']
            prev_low = data.iloc[i-1]['Low']
            prev_range = prev_high - prev_low

            if prev_range == 0:
                continue

            # Check if current bar is inside previous bar
            high_contained = current_high <= prev_high
            low_contained = current_low >= prev_low

            if high_contained and low_contained:
                # Calculate containment ratio
                containment_ratio = current_range / prev_range

                if containment_ratio <= self.INSIDE_BAR_RATIO:
                    # Determine direction based on position within previous bar
                    prev_mid = (prev_high + prev_low) / 2
                    current_mid = (current_high + current_low) / 2

                    if current_mid > prev_mid:
                        direction = 'BULLISH'
                        strength = 3
                    else:
                        direction = 'BEARISH'
                        strength = 3

                    signal = PriceActionSignal(
                        pattern_type='INSIDE_BAR',
                        direction=direction,
                        strength=strength,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=data.iloc[i]['Close'],
                        description=f"Inside bar pattern ({direction.lower()})"
                    )
                    signals.append(signal)

        return signals

    def _detect_consolidation_patterns(self, data: pd.DataFrame) -> List[PriceActionSignal]:
        """Detect ATR-based consolidation patterns."""
        signals = []

        if len(data) < self.CONSOLIDATION_PERIOD:
            return signals

        # Calculate ATR for the period
        atr_values = self._calculate_atr(data, self.CONSOLIDATION_PERIOD)

        for i in range(self.CONSOLIDATION_PERIOD, len(data)):
            # Check if recent ATR is below threshold
            recent_atr = atr_values.iloc[i] if i < len(atr_values) else atr_values.iloc[-1]
            avg_atr = atr_values.tail(self.CONSOLIDATION_PERIOD).mean()

            if recent_atr <= avg_atr * self.CONSOLIDATION_ATR_RATIO:
                # Additional check: range contraction
                recent_ranges = (data['High'] - data['Low']).tail(self.CONSOLIDATION_PERIOD)
                current_range = recent_ranges.iloc[-1]
                avg_range = recent_ranges.mean()

                if current_range <= avg_range * self.CONSOLIDATION_ATR_RATIO:
                    signal = PriceActionSignal(
                        pattern_type='CONSOLIDATION',
                        direction='NEUTRAL',
                        strength=2,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=data.iloc[i]['Close'],
                        description="ATR-based consolidation detected"
                    )
                    signals.append(signal)

        return signals

    def _detect_breakout_patterns(self, data: pd.DataFrame) -> List[PriceActionSignal]:
        """Detect simple breakout patterns."""
        signals = []

        for i in range(5, len(data)):  # Need some history
            current_high = data.iloc[i]['High']
            current_low = data.iloc[i]['Low']
            current_close = data.iloc[i]['Close']

            # Look at recent highs/lows
            recent_highs = data['High'].iloc[i-5:i]
            recent_lows = data['Low'].iloc[i-5:i]

            resistance_level = recent_highs.max()
            support_level = recent_lows.min()

            # Bullish breakout
            if current_close > resistance_level * self.BREAKOUT_STRENGTH:
                # Confirm with volume if available
                volume_check = True
                if 'Volume' in data.columns:
                    recent_volume = data['Volume'].iloc[i-5:i].mean()
                    current_volume = data.iloc[i]['Volume']
                    volume_check = current_volume > recent_volume

                if volume_check:
                    signal = PriceActionSignal(
                        pattern_type='BREAKOUT',
                        direction='BULLISH',
                        strength=4,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=current_close,
                        description="Bullish breakout above resistance"
                    )
                    signals.append(signal)

            # Bearish breakdown
            elif current_close < support_level / self.BREAKOUT_STRENGTH:
                # Confirm with volume if available
                volume_check = True
                if 'Volume' in data.columns:
                    recent_volume = data['Volume'].iloc[i-5:i].mean()
                    current_volume = data.iloc[i]['Volume']
                    volume_check = current_volume > recent_volume

                if volume_check:
                    signal = PriceActionSignal(
                        pattern_type='BREAKOUT',
                        direction='BEARISH',
                        strength=4,
                        bar_index=i,
                        bar_time=data.index[i],
                        price=current_close,
                        description="Bearish breakdown below support"
                    )
                    signals.append(signal)

        return signals

    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high = data['High']
        low = data['Low']
        close = data['Close'].shift(1)

        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)

        return tr.rolling(window=period).mean()

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data for price action analysis."""
        if data is None or data.empty:
            return False

        required_columns = ['Open', 'High', 'Low', 'Close']
        if not all(col in data.columns for col in required_columns):
            return False

        if len(data) < 5:  # Minimum data for pattern detection
            return False

        return True

    def get_price_action_summary(self, signals: List[PriceActionSignal]) -> Dict[str, Any]:
        """Get summary statistics of price action signals."""
        if not signals:
            return {'total_signals': 0}

        pattern_counts = {}
        direction_counts = {}

        for signal in signals:
            pattern_counts[signal.pattern_type] = pattern_counts.get(signal.pattern_type, 0) + 1
            direction_counts[signal.direction] = direction_counts.get(signal.direction, 0) + 1

        return {
            'total_signals': len(signals),
            'patterns': pattern_counts,
            'directions': direction_counts,
            'avg_strength': sum(s.strength for s in signals) / len(signals),
            'most_recent': signals[0].bar_time.date() if signals else None
        }