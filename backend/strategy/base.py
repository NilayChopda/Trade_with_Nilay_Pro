"""
Strategy Base Class
Abstract base class for all trading strategies
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Any
import logging

class Strategy(ABC):
    """
    Abstract Base Class for Trading Strategies
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"twn.strategy.{name}")

    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze the dataframe and return a list of signals/setups.
        
        Args:
            df: OHLCV DataFrame with datetime index
            
        Returns:
            List of dictionaries, each representing a signal.
            Example:
            [
                {
                    "symbol": "RELIANCE",
                    "signal": "BUY",
                    "price": 2500.0,
                    "stop_loss": 2450.0,
                    "target": 2600.0,
                    "confidence": 0.8,
                    "timestamp": "2024-02-07 10:30:00"
                }
            ]
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Check if dataframe has enough data"""
        if df.empty:
            return False
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            self.logger.warning(f"Missing columns. Required: {required_cols}")
            return False
        return True
