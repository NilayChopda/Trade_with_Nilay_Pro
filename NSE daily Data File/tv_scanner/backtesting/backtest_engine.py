"""
Phase 9: Backtesting Module
Simulate trades based on signals with entry, SL, target logic.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    symbol: str
    entry_price: float
    entry_date: datetime
    stop_loss: float
    target_price: float
    risk: float = field(default=0.0, init=False)
    reward: float = field(default=0.0, init=False)
    exit_price: float = 0.0
    exit_date: datetime = None
    exit_type: str = ""  # "SL", "TARGET", "TIMEOUT"
    pnl: float = 0.0
    pnl_percent: float = 0.0
    result: str = ""  # "WIN", "LOSS", "OPEN"
    
    def __post_init__(self):
        self.risk = self.entry_price - self.stop_loss
        self.reward = self.target_price - self.entry_price
        if self.risk <= 0:
            raise ValueError(f"Invalid risk: {self.risk}")
    
    def close_trade(self, exit_price: float, exit_date: datetime, exit_type: str):
        """Close trade and calculate PnL"""
        self.exit_price = exit_price
        self.exit_date = exit_date
        self.exit_type = exit_type
        
        self.pnl = exit_price - self.entry_price
        self.pnl_percent = (self.pnl / self.entry_price) * 100
        
        if exit_type == "SL":
            self.result = "LOSS"
        elif exit_type == "TARGET":
            self.result = "WIN"
        else:
            self.result = "LOSS" if self.pnl < 0 else "WIN"
    
    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio"""
        if self.risk == 0:
            return 0
        return self.reward / self.risk
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary"""
        return {
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'entry_date': self.entry_date.strftime('%Y-%m-%d %H:%M:%S'),
            'stop_loss': self.stop_loss,
            'target_price': self.target_price,
            'risk': round(self.risk, 2),
            'reward': round(self.reward, 2),
            'exit_price': round(self.exit_price, 2),
            'exit_date': self.exit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_date else "",
            'exit_type': self.exit_type,
            'pnl': round(self.pnl, 2),
            'pnl_percent': round(self.pnl_percent, 2),
            'result': self.result,
            'r_ratio': round(self.risk_reward_ratio, 2),
        }


class BacktestEngine:
    """
    Backtesting engine for trading signals.
    
    Entry: Signal close price
    Stop Loss: OB low
    Target: Entry + 2 * Risk (2R)
    """
    
    def __init__(self, slippage_percent: float = 0.1):
        """
        Initialize backtesting engine.
        
        Args:
            slippage_percent: Slippage percentage for realistic simulation
        """
        self.slippage_percent = slippage_percent
        self.trades: List[Trade] = []
        self.logger = logger
    
    def create_trade(self,
                    symbol: str,
                    entry_price: float,
                    entry_date: datetime,
                    ob_low: float,
                    risk_multiplier: float = 2.0) -> Trade:
        """
        Create a trade based on signal.
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price (signal close)
            entry_date: Entry date/time
            ob_low: Order block low (for stop loss)
            risk_multiplier: Target multiplier (default 2R)
        
        Returns:
            Trade object
        """
        # Apply slippage to entry
        entry_with_slippage = entry_price * (1 + self.slippage_percent / 100)
        
        # Stop loss at OB low
        stop_loss = ob_low
        
        # Risk calculation
        risk = entry_with_slippage - stop_loss
        
        # Target at 2R (or configured multiplier)
        target_price = entry_with_slippage + (risk * risk_multiplier)
        
        trade = Trade(
            symbol=symbol,
            entry_price=entry_with_slippage,
            entry_date=entry_date,
            stop_loss=stop_loss,
            target_price=target_price,
        )
        
        return trade
    
    def simulate_trade(self,
                      trade: Trade,
                      ohlcv_data: pd.DataFrame,
                      lookback_bars: int = 20) -> bool:
        """
        Simulate trade on historical data.
        
        Args:
            trade: Trade object to simulate
            ohlcv_data: OHLCV DataFrame with 'high', 'low', 'close'
            lookback_bars: Number of bars to simulate (default 20)
        
        Returns:
            True if trade closed, False if still open
        """
        if len(ohlcv_data) < lookback_bars:
            lookback_bars = len(ohlcv_data)
        
        entry_index = max(0, len(ohlcv_data) - lookback_bars)
        
        for i in range(entry_index, len(ohlcv_data)):
            bar = ohlcv_data.iloc[i]
            bar_high = bar['high']
            bar_low = bar['low']
            bar_close = bar['close']
            bar_date = bar.name if hasattr(bar.name, 'to_pydatetime') else datetime.now()
            
            # Check if stop loss hit
            if bar_low <= trade.stop_loss:
                trade.close_trade(trade.stop_loss, bar_date, "SL")
                return True
            
            # Check if target hit
            if bar_high >= trade.target_price:
                trade.close_trade(trade.target_price, bar_date, "TARGET")
                return True
        
        # Trade didn't close within lookback period
        last_bar = ohlcv_data.iloc[-1]
        last_date = last_bar.name if hasattr(last_bar.name, 'to_pydatetime') else datetime.now()
        trade.close_trade(last_bar['close'], last_date, "TIMEOUT")
        return False
    
    def backtest_signals(self,
                        signals_df: pd.DataFrame,
                        price_data: Dict[str, pd.DataFrame],
                        ob_data: Dict[str, Dict]) -> List[Trade]:
        """
        Backtest multiple signals.
        
        Args:
            signals_df: DataFrame with signals (columns: symbol, close, entry_date)
            price_data: Dict of {symbol: OHLCV DataFrame}
            ob_data: Dict of {symbol: {'low': price, ...}}
        
        Returns:
            List of Trade objects
        """
        trades = []
        
        for idx, row in signals_df.iterrows():
            try:
                symbol = row['symbol']
                entry_price = row['close']
                entry_date = row.get('entry_date', datetime.now())
                ob_low = ob_data.get(symbol, {}).get('low', entry_price * 0.95)
                
                # Create trade
                trade = self.create_trade(
                    symbol=symbol,
                    entry_price=entry_price,
                    entry_date=entry_date,
                    ob_low=ob_low,
                )
                
                # Simulate trade
                if symbol in price_data:
                    self.simulate_trade(trade, price_data[symbol])
                else:
                    self.logger.warning(f"No price data for {symbol}")
                
                trades.append(trade)
                
            except Exception as e:
                self.logger.error(f"Error backtesting signal {idx}: {e}")
                continue
        
        self.trades = trades
        return trades
    
    def calculate_metrics(self) -> Dict:
        """
        Calculate backtest metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.trades:
            return {}
        
        trades_df = pd.DataFrame([t.to_dict() for t in self.trades])
        
        # Basic stats
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.result == "WIN")
        losing_trades = sum(1 for t in self.trades if t.result == "LOSS")
        
        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # PnL stats
        total_pnl = sum(t.pnl for t in self.trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        avg_return_percent = sum(t.pnl_percent for t in self.trades) / total_trades if total_trades > 0 else 0
        
        # Winning and losing trades stats
        winning_trades_list = [t for t in self.trades if t.result == "WIN"]
        losing_trades_list = [t for t in self.trades if t.result == "LOSS"]
        
        avg_win = sum(t.pnl for t in winning_trades_list) / len(winning_trades_list) if winning_trades_list else 0
        avg_loss = sum(t.pnl for t in losing_trades_list) / len(losing_trades_list) if losing_trades_list else 0
        
        # Max win/loss
        max_win = max((t.pnl for t in winning_trades_list), default=0)
        max_loss = min((t.pnl for t in losing_trades_list), default=0)
        
        # Drawdown calculation
        cumulative_pnl = np.cumsum([t.pnl for t in self.trades])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades_list)
        gross_loss = abs(sum(t.pnl for t in losing_trades_list))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Risk/Reward
        avg_risk_reward = np.mean([t.risk_reward_ratio for t in self.trades if t.risk_reward_ratio > 0])
        
        # Expectancy (average profit per trade)
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(avg_pnl, 2),
            'avg_return_percent': round(avg_return_percent, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_win': round(max_win, 2),
            'max_loss': round(max_loss, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_risk_reward': round(avg_risk_reward, 2),
            'expectancy': round(expectancy, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
        }
    
    def get_trades_dataframe(self) -> pd.DataFrame:
        """
        Get trades as pandas DataFrame.
        
        Returns:
            DataFrame with trade details
        """
        if not self.trades:
            return pd.DataFrame()
        
        return pd.DataFrame([t.to_dict() for t in self.trades])
    
    def filter_trades(self, result: str = None, symbol: str = None) -> List[Trade]:
        """
        Filter trades by result or symbol.
        
        Args:
            result: "WIN", "LOSS", or None (all)
            symbol: Symbol to filter, or None (all)
        
        Returns:
            Filtered list of trades
        """
        filtered = self.trades
        
        if result:
            filtered = [t for t in filtered if t.result == result]
        
        if symbol:
            filtered = [t for t in filtered if t.symbol == symbol]
        
        return filtered
