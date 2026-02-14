"""
Utility functions and helpers
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str, log_file: Path) -> None:
    """Setup logging configuration"""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_config() -> bool:
    """Validate configuration settings"""
    # TODO: Implement config validation
    return True


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"₹{amount:,.2f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100