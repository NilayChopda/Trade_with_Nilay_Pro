"""
Order Block Engine

This module implements Order Block detection based on Smart Money Concepts (SMC).
Order Blocks are key areas where institutional traders (smart money) place their orders.

Key Concepts:
- Order Blocks are zones where large players accumulate or distribute positions
- They form after a Break of Structure (BOS) following an impulse move
- Demand Order Blocks (bullish) form on pullbacks in uptrends
- Supply Order Blocks (bearish) form on rallies in downtrends

Detection Process:
1. Identify impulse moves (strong directional price action)
2. Detect Break of Structure (BOS) - price breaking recent highs/lows
3. Find the last opposite candle before the BOS
4. Create Order Block zone using that candle's high-low range
5. Monitor for price tapping into these zones

Order Block Types:
- BULLISH_OB (Demand Zone): Formed after bullish BOS, price may bounce up
- BEARISH_OB (Supply Zone): Formed after bearish BOS, price may drop down
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import DATA_DIR


@dataclass
class OrderBlock:
    """
    Represents an Order Block zone.

    An Order Block is a price zone where smart money has placed significant orders.
    """
    block_type: str  # 'BULLISH_OB' or 'BEARISH_OB'
    high: float      # Upper boundary of the zone
    low: float       # Lower boundary of the zone
    entry_time: pd.Timestamp  # When the OB was formed
    strength: int    # Strength rating (1-5, based on impulse size)
    symbol: str      # Stock symbol
    tapped: bool = False  # Whether price has tapped this zone
    tapped_time: Optional[pd.Timestamp] = None  # When it was tapped

    def __post_init__(self):
        """Validate the Order Block data"""
        if self.block_type not in ['BULLISH_OB', 'BEARISH_OB']:
            raise ValueError(f"Invalid block_type: {self.block_type}")
        if self.high <= self.low:
            raise ValueError("High must be greater than low")
        if self.strength < 1 or self.strength > 5:
            raise ValueError("Strength must be between 1 and 5")

    def is_tapped(self, current_price: float) -> bool:
        """
        Check if the current price is tapping this Order Block zone.

        For bullish OBs (demand zones), we check if price drops into the zone.
        For bearish OBs (supply zones), we check if price rises into the zone.

        Args:
            current_price: Current market price

        Returns:
            bool: True if price is within the OB zone
        """
        return self.low <= current_price <= self.high

    def get_zone_size(self) -> float:
        """Get the size of the Order Block zone"""
        return self.high - self.low

    def get_zone_midpoint(self) -> float:
        """Get the midpoint of the Order Block zone"""
        return (self.high + self.low) / 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert Order Block to dictionary for serialization"""
        return {
            'block_type': self.block_type,
            'high': self.high,
            'low': self.low,
            'entry_time': self.entry_time.isoformat(),
            'strength': self.strength,
            'symbol': self.symbol,
            'tapped': self.tapped,
            'tapped_time': self.tapped_time.isoformat() if self.tapped_time else None
        }


class OrderBlockEngine:
    """
    Engine for detecting and managing Order Blocks using Smart Money Concepts.

    This engine analyzes price action to identify:
    1. Impulse moves (strong directional price action)
    2. Break of Structure (BOS) events
    3. Order Block formations
    4. Zone tapping events

    The engine maintains historical Order Blocks and can detect when
    current price action interacts with these zones.
    """

    def __init__(self):
        """
        Initialize the Order Block Engine.

        Sets up logging and data storage paths.
        """
        self.logger = logging.getLogger(__name__)

        # Data storage
        self.OB_DATA_DIR = DATA_DIR / "order_blocks"
        self.OB_DATA_DIR.mkdir(exist_ok=True)

        # Parameters for OB detection (aligned with Pine Script)
        self.MIN_IMPULSE_CANDLES = 3  # Minimum candles for impulse move
        self.BOS_LOOKBACK = 10        # Candles to look back for BOS detection
        self.OB_MIN_STRENGTH = 2      # Minimum strength for valid OB
        self.INTERNAL_SWING_LENGTH = 5  # Length for internal structure (Pine Script default)
        self.SWING_LENGTH = 50         # Length for swing structure (Pine Script default)

        # Volatility settings (from Pine Script)
        self.VOLATILITY_MULTIPLIER = 2.0  # Multiplier for high volatility detection
        self.OB_MITIGATION_SOURCE = 'highlow'  # 'close' or 'highlow'
        self.OB_FILTER_METHOD = 'atr'  # 'atr' or 'range'

        self.logger.info("OrderBlockEngine initialized")

    def analyze_price_data(self, symbol: str, data: pd.DataFrame) -> List[OrderBlock]:
        """
        Analyze price data and return all detected Order Blocks.

        This is the main entry point for Order Block detection. The method:
        1. Validates input data
        2. Scans for impulse moves
        3. Detects BOS events
        4. Creates Order Block zones
        5. Returns list of valid Order Blocks

        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame with datetime index

        Returns:
            List[OrderBlock]: All detected Order Blocks
        """
        self.logger.info(f"Analyzing {symbol} for Order Blocks")

        if not self._validate_data(data):
            self.logger.warning(f"Invalid data for {symbol}")
            return []

        # Calculate parsed highs/lows (Pine Script approach)
        parsed_highs, parsed_lows = self._calculate_parsed_highs_lows(data)

        order_blocks = []

        try:
            # Scan for internal Order Blocks (smaller structures)
            internal_obs = self._scan_for_order_blocks(data, parsed_highs, parsed_lows,
                                                      self.INTERNAL_SWING_LENGTH, symbol, "internal")
            order_blocks.extend(internal_obs)

            # Scan for swing Order Blocks (larger structures)
            swing_obs = self._scan_for_order_blocks(data, parsed_highs, parsed_lows,
                                                   self.SWING_LENGTH, symbol, "swing")
            order_blocks.extend(swing_obs)

            # Filter and validate Order Blocks
            valid_obs = self._filter_valid_order_blocks(order_blocks)

            self.logger.info(f"Found {len(valid_obs)} valid Order Blocks for {symbol}")
            return valid_obs

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return []

    def _scan_for_order_blocks(self, data: pd.DataFrame, parsed_highs: pd.Series,
                              parsed_lows: pd.Series, swing_length: int,
                              symbol: str, ob_type: str) -> List[OrderBlock]:
        """
        Scan for Order Blocks using parsed highs/lows, following Pine Script logic.

        This method detects swing points and creates Order Blocks after BOS events
        using the parsed high/low values for more accurate OB levels.

        Args:
            data: OHLCV DataFrame
            parsed_highs: Parsed high values (swapped on volatile bars)
            parsed_lows: Parsed low values (swapped on volatile bars)
            swing_length: Length for swing detection
            symbol: Stock symbol
            ob_type: "internal" or "swing" for OB classification

        Returns:
            List of detected OrderBlocks
        """
        order_blocks = []

        # Get swing points using the specified length
        swing_highs, swing_lows = self._detect_swing_points(data, swing_length)

        # Scan for BOS events and create OBs
        for i in range(swing_length, len(data) - 1):
            # Check for BOS at this index
            bos_result = self._detect_break_of_structure(data, i)
            if not bos_result:
                continue

            bos_type, bos_index = bos_result

            # For bearish OB (after bullish BOS), find the highest parsed high after BOS
            if bos_type == 'BULLISH_BOS':
                # Look for bearish OB: find max parsed high from BOS to current
                range_highs = parsed_highs.iloc[bos_index:i+1]
                if len(range_highs) > 0:
                    # Find the position of the maximum value
                    max_pos = range_highs.argmax()
                    # Convert back to original index position
                    max_idx = bos_index + max_pos
                    ob_high = parsed_highs.iloc[max_idx]
                    ob_low = parsed_lows.iloc[max_idx]

                    # Create bearish OB
                    ob = OrderBlock(
                        block_type='BEARISH_OB',
                        high=ob_high,
                        low=ob_low,
                        entry_time=data.index[max_idx],
                        strength=3,  # Default strength
                        symbol=symbol
                    )
                    order_blocks.append(ob)

            # For bullish OB (after bearish BOS), find the lowest parsed low after BOS
            elif bos_type == 'BEARISH_BOS':
                # Look for bullish OB: find min parsed low from BOS to current
                range_lows = parsed_lows.iloc[bos_index:i+1]
                if len(range_lows) > 0:
                    # Find the position of the minimum value
                    min_pos = range_lows.argmin()
                    # Convert back to original index position
                    min_idx = bos_index + min_pos
                    ob_high = parsed_highs.iloc[min_idx]
                    ob_low = parsed_lows.iloc[min_idx]

                    # Create bullish OB
                    ob = OrderBlock(
                        block_type='BULLISH_OB',
                        high=ob_high,
                        low=ob_low,
                        entry_time=data.index[min_idx],
                        strength=3,  # Default strength
                        symbol=symbol
                    )
                    order_blocks.append(ob)

        return order_blocks

    def _detect_swing_points(self, data: pd.DataFrame, length: int) -> Tuple[pd.Series, pd.Series]:
        """
        Detect swing highs and lows using the specified length.

        Args:
            data: OHLCV DataFrame
            length: Swing detection length

        Returns:
            Tuple of (swing_highs, swing_lows) Series
        """
        swing_highs = pd.Series(index=data.index, dtype=float)
        swing_lows = pd.Series(index=data.index, dtype=float)

        for i in range(length, len(data) - length):
            # Check for swing high
            if data['High'].iloc[i] == data['High'].iloc[i-length:i+length+1].max():
                swing_highs.iloc[i] = data['High'].iloc[i]

            # Check for swing low
            if data['Low'].iloc[i] == data['Low'].iloc[i-length:i+length+1].min():
                swing_lows.iloc[i] = data['Low'].iloc[i]

        return swing_highs, swing_lows

    def _detect_break_of_structure(self, data: pd.DataFrame, current_index: int) -> Optional[Tuple[str, int]]:
        """
        Detect Break of Structure (BOS) at the current index.

        BOS occurs when price breaks above a recent swing high (bullish BOS)
        or below a recent swing low (bearish BOS).

        Args:
            data: OHLCV DataFrame
            current_index: Index to check for BOS

        Returns:
            Tuple[str, int] or None: (bos_type, bos_index) or None
        """
        if current_index < self.BOS_LOOKBACK:
            return None

        current_high = data.iloc[current_index]['High']
        current_low = data.iloc[current_index]['Low']

        # Look back for swing points
        lookback_data = data.iloc[current_index - self.BOS_LOOKBACK:current_index]

        # Check for bullish BOS (breaking above recent highs)
        recent_high = lookback_data['High'].max()
        if current_high > recent_high:
            return ('BULLISH_BOS', current_index)

        # Check for bearish BOS (breaking below recent lows)
        recent_low = lookback_data['Low'].min()
        if current_low < recent_low:
            return ('BEARISH_BOS', current_index)

        return None

    def _detect_impulse_move(self, data: pd.DataFrame, bos_index: int, bos_type: str) -> Optional[Tuple[int, int]]:
        """
        Detect impulse move leading up to the BOS.

        An impulse move is a strong directional move consisting of multiple
        consecutive candles moving in the same direction.

        Args:
            data: OHLCV DataFrame
            bos_index: Index where BOS occurred
            bos_type: Type of BOS ('BULLISH_BOS' or 'BEARISH_BOS')

        Returns:
            Tuple[int, int] or None: (impulse_start_index, strength) or None
        """
        if bos_type == 'BULLISH_BOS':
            # For bullish BOS, look for downward impulse before it
            direction = 'down'
        else:
            # For bearish BOS, look for upward impulse before it
            direction = 'up'

        # Scan backwards from BOS to find impulse
        impulse_length = 0
        max_lookback = min(20, bos_index)  # Don't look back more than 20 candles

        for i in range(bos_index - 1, max(bos_index - max_lookback, 0), -1):
            if self._is_candle_in_direction(data, i, direction):
                impulse_length += 1
            else:
                break

        if impulse_length >= self.MIN_IMPULSE_CANDLES:
            impulse_start = bos_index - impulse_length
            strength = min(5, impulse_length // 2)  # Strength based on impulse length
            return (impulse_start, strength)

        return None

    def _is_candle_in_direction(self, data: pd.DataFrame, index: int, direction: str) -> bool:
        """
        Check if a candle is moving in the specified direction.

        Args:
            data: OHLCV DataFrame
            index: Candle index
            direction: 'up' or 'down'

        Returns:
            bool: True if candle matches direction
        """
        candle = data.iloc[index]
        body_size = abs(candle['Close'] - candle['Open'])
        total_range = candle['High'] - candle['Low']

        if direction == 'up':
            # Bullish candle: close > open and body > 60% of range
            return candle['Close'] > candle['Open'] and body_size > total_range * 0.6
        else:
            # Bearish candle: close < open and body > 60% of range
            return candle['Close'] < candle['Open'] and body_size > total_range * 0.6

    def _find_last_opposite_candle(self, data: pd.DataFrame, impulse_start: int,
                                 bos_index: int, bos_type: str) -> Optional[int]:
        """
        Find the last candle that was opposite to the impulse direction.

        This candle's high-low range becomes the Order Block zone.

        Args:
            data: OHLCV DataFrame
            impulse_start: Start index of impulse move
            bos_index: Index of BOS
            bos_type: Type of BOS

        Returns:
            int or None: Index of last opposite candle
        """
        if bos_type == 'BULLISH_BOS':
            # After downward impulse, BOS up - look for last bearish candle
            opposite_direction = 'down'
        else:
            # After upward impulse, BOS down - look for last bullish candle
            opposite_direction = 'up'

        # Scan from impulse start to BOS index
        for i in range(impulse_start, bos_index):
            if self._is_candle_in_direction(data, i, opposite_direction):
                return i  # Return the last opposite candle found

        return None

    def _create_order_block_zone(self, data: pd.DataFrame, candle_index: int,
                               bos_type: str, strength: int, symbol: str) -> OrderBlock:
        """
        Create an Order Block zone from the specified candle.

        Args:
            data: OHLCV DataFrame
            candle_index: Index of the candle defining the zone
            bos_type: Type of BOS that created this OB
            strength: Strength rating of the OB
            symbol: Stock symbol

        Returns:
            OrderBlock: The created Order Block
        """
        candle = data.iloc[candle_index]

        # Order Block zone uses the high-low range of the opposite candle
        ob_high = candle['High']
        ob_low = candle['Low']

        # Determine OB type based on BOS
        if bos_type == 'BULLISH_BOS':
            ob_type = 'BULLISH_OB'  # Demand zone
        else:
            ob_type = 'BEARISH_OB'  # Supply zone

        return OrderBlock(
            block_type=ob_type,
            high=ob_high,
            low=ob_low,
            entry_time=data.index[candle_index],
            strength=strength,
            symbol=symbol
        )

    def _filter_valid_order_blocks(self, order_blocks: List[OrderBlock]) -> List[OrderBlock]:
        """
        Filter and validate Order Blocks.

        Removes duplicates, invalid zones, and low-strength OBs.

        Args:
            order_blocks: List of detected Order Blocks

        Returns:
            List[OrderBlock]: Filtered valid Order Blocks
        """
        if not order_blocks:
            return []

        # Remove low strength OBs
        valid_obs = [ob for ob in order_blocks if ob.strength >= self.OB_MIN_STRENGTH]

        # Sort by entry time (most recent first)
        valid_obs.sort(key=lambda x: x.entry_time, reverse=True)

        # Remove overlapping OBs of the same type (keep the stronger one)
        filtered_obs = []
        for ob in valid_obs:
            # Check if this OB overlaps significantly with existing ones
            overlaps = False
            for existing_ob in filtered_obs:
                if (existing_ob.block_type == ob.block_type and
                    self._zones_overlap_significantly(ob, existing_ob)):
                    overlaps = True
                    break

            if not overlaps:
                filtered_obs.append(ob)

        return filtered_obs

    def _zones_overlap_significantly(self, ob1: OrderBlock, ob2: OrderBlock) -> bool:
        """
        Check if two Order Block zones overlap significantly.

        Args:
            ob1, ob2: Order Blocks to compare

        Returns:
            bool: True if zones overlap by more than 50%
        """
        # Calculate overlap
        overlap_start = max(ob1.low, ob2.low)
        overlap_end = min(ob1.high, ob2.high)

        if overlap_end <= overlap_start:
            return False  # No overlap

        overlap_size = overlap_end - overlap_start
        zone1_size = ob1.high - ob1.low
        zone2_size = ob2.high - ob2.low

        # Significant overlap if overlap > 50% of either zone
        return (overlap_size > zone1_size * 0.5 or
                overlap_size > zone2_size * 0.5)

    def check_tapped_zones(self, symbol: str, current_price: float,
                          order_blocks: List[OrderBlock]) -> List[OrderBlock]:
        """
        Check which Order Block zones are currently being tapped by price.

        Args:
            symbol: Stock symbol
            current_price: Current market price
            order_blocks: List of Order Blocks to check

        Returns:
            List[OrderBlock]: Order Blocks that are tapped
        """
        tapped_obs = []

        for ob in order_blocks:
            if ob.symbol == symbol and ob.is_tapped(current_price):
                if not ob.tapped:  # First time being tapped
                    ob.tapped = True
                    ob.tapped_time = pd.Timestamp.now()
                    self.logger.info(f"Order Block tapped: {symbol} {ob.block_type} at {current_price}")

                tapped_obs.append(ob)

        return tapped_obs

    def save_order_blocks(self, symbol: str, order_blocks: List[OrderBlock]) -> None:
        """
        Save Order Blocks to disk for historical tracking.

        Args:
            symbol: Stock symbol
            order_blocks: List of Order Blocks to save
        """
        try:
            file_path = self.OB_DATA_DIR / f"{symbol}_order_blocks.json"

            # Convert to dictionaries
            ob_data = [ob.to_dict() for ob in order_blocks]

            # Save to JSON
            import json
            with open(file_path, 'w') as f:
                json.dump({
                    'symbol': symbol,
                    'last_updated': datetime.now().isoformat(),
                    'order_blocks': ob_data
                }, f, indent=2)

            self.logger.debug(f"Saved {len(order_blocks)} Order Blocks for {symbol}")

        except Exception as e:
            self.logger.error(f"Failed to save Order Blocks for {symbol}: {e}")

    def load_order_blocks(self, symbol: str) -> List[OrderBlock]:
        """
        Load historical Order Blocks from disk.

        Args:
            symbol: Stock symbol

        Returns:
            List[OrderBlock]: Loaded Order Blocks
        """
        try:
            file_path = self.OB_DATA_DIR / f"{symbol}_order_blocks.json"

            if not file_path.exists():
                return []

            import json
            with open(file_path, 'r') as f:
                data = json.load(f)

            order_blocks = []
            for ob_data in data.get('order_blocks', []):
                # Convert back to OrderBlock
                ob = OrderBlock(
                    block_type=ob_data['block_type'],
                    high=ob_data['high'],
                    low=ob_data['low'],
                    entry_time=pd.Timestamp(ob_data['entry_time']),
                    strength=ob_data['strength'],
                    symbol=ob_data['symbol'],
                    tapped=ob_data.get('tapped', False),
                    tapped_time=pd.Timestamp(ob_data['tapped_time']) if ob_data.get('tapped_time') else None
                )
                order_blocks.append(ob)

            self.logger.debug(f"Loaded {len(order_blocks)} Order Blocks for {symbol}")
            return order_blocks

        except Exception as e:
            self.logger.error(f"Failed to load Order Blocks for {symbol}: {e}")
            return []

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data for Order Block analysis.

        Args:
            data: OHLCV DataFrame to validate

        Returns:
            bool: True if data is valid
        """
        if data is None or data.empty:
            return False

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            return False

        if len(data) < self.BOS_LOOKBACK * 3:  # Need minimum data for analysis
            return False

        return True

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

    def _calculate_parsed_highs_lows(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate parsed highs and lows based on volatility, following Pine Script logic.

        In volatile bars (high-low >= 2 * volatility_measure), swap high/low values
        to get more accurate Order Block levels.

        Args:
            data: OHLCV DataFrame

        Returns:
            Tuple of (parsed_highs, parsed_lows) Series
        """
        # Calculate volatility measure (ATR or cumulative range)
        if self.OB_FILTER_METHOD == 'atr':
            # Use ATR(200) as in Pine Script
            atr = self._calculate_atr(data, 200)
            volatility_measure = atr
        else:
            # Use cumulative mean range
            tr = self._calculate_true_range(data)
            volatility_measure = tr.cumsum() / (data.index.astype(int) // 10**9 + 1)  # Approximate bar_index

        # Detect high volatility bars
        high_volatility = (data['High'] - data['Low']) >= self.VOLATILITY_MULTIPLIER * volatility_measure

        # Create parsed highs/lows
        parsed_highs = pd.Series(index=data.index, dtype=float)
        parsed_lows = pd.Series(index=data.index, dtype=float)

        for i in range(len(data)):
            if high_volatility.iloc[i]:
                # Swap high/low on volatile bars
                parsed_highs.iloc[i] = data['Low'].iloc[i]
                parsed_lows.iloc[i] = data['High'].iloc[i]
            else:
                parsed_highs.iloc[i] = data['High'].iloc[i]
                parsed_lows.iloc[i] = data['Low'].iloc[i]

        return parsed_highs, parsed_lows

    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            data: OHLCV DataFrame
            period: ATR period

        Returns:
            ATR values
        """
        high = data['High']
        low = data['Low']
        close = data['Close'].shift(1)

        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)

        return tr.rolling(window=period).mean()

    def _calculate_true_range(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate True Range.

        Args:
            data: OHLCV DataFrame

        Returns:
            True Range values
        """
        high = data['High']
        low = data['Low']
        close = data['Close'].shift(1)

        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)

        return tr

    def get_order_block_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get a summary of Order Blocks for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dict: Summary statistics
        """
        order_blocks = self.load_order_blocks(symbol)

        if not order_blocks:
            return {'symbol': symbol, 'total_obs': 0}

        bullish_obs = [ob for ob in order_blocks if ob.block_type == 'BULLISH_OB']
        bearish_obs = [ob for ob in order_blocks if ob.block_type == 'BEARISH_OB']
        tapped_obs = [ob for ob in order_blocks if ob.tapped]

        return {
            'symbol': symbol,
            'total_obs': len(order_blocks),
            'bullish_obs': len(bullish_obs),
            'bearish_obs': len(bearish_obs),
            'tapped_obs': len(tapped_obs),
            'avg_strength': sum(ob.strength for ob in order_blocks) / len(order_blocks),
            'most_recent_ob': max(order_blocks, key=lambda x: x.entry_time).entry_time.date() if order_blocks else None
        }