"""
Backtesting Module
Trade simulation and performance analysis
"""

from .backtest_engine import BacktestEngine, Trade
from .backtest_report import BacktestReportGenerator

__all__ = [
    'BacktestEngine',
    'Trade',
    'BacktestReportGenerator',
]
