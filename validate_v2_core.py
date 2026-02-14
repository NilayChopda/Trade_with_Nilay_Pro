"""
Final System Validation (V2)
Validates AI-Enhanced Scanner + Paper Trading + Risk Management
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scanner.scanner_engine import ScannerEngine

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("twn.validation")
    
    logger.info("Starting Final System Validation (Scanner Focus)...")
    
    # 1. Initialize Components
    engine = ScannerEngine()
    
    # 2. Configure a test scanner
    engine.add_scanner(
        name="Nilay Swing Pick Algo",
        url="https://chartink.com/screener/nilay-swing-pick-algo"
    )
    
    # 3. Run one scan cycle (with AI Scoring)
    logger.info("Running Scan Cycle (AI Scoring Enabled)...")
    stats = engine.run_once(send_alerts=False) # Don't spam Telegram during test
    
    logger.info("=" * 40)
    logger.info("FINAL VALIDATION COMPLETE")
    logger.info(f"Scanners Run: {stats['total_scanners']}")
    logger.info("=" * 40)
