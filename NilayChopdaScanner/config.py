"""
Configuration settings for NilayChopdaScanner
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration (placeholders)
API_KEY = os.getenv("SCANNER_API_KEY", "")
API_SECRET = os.getenv("SCANNER_API_SECRET", "")

# Telegram Bot Configuration
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "810052560")

# Database Configuration (placeholder)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///scanner.db")

# Scanner Configuration
DEFAULT_SCAN_INTERVAL = 60  # seconds
MAX_CONCURRENT_SCANS = 10

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "scanner.log"

# Market Configuration
SUPPORTED_EXCHANGES = ["NSE", "BSE"]
DEFAULT_TIMEZONE = "Asia/Kolkata"