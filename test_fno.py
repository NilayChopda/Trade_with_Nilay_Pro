"""
Test FnO Fetcher
"""

import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.fno_fetcher import FnoFetcher

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("twn.test_fno")
    
    logger.info("Initializing FnO Fetcher...")
    fno = FnoFetcher()
    
    logger.info("Fetching NIFTY Option Chain...")
    data = fno.get_analysis("NIFTY")
    
    if "error" in data:
        logger.error(f"Failed: {data['error']}")
    else:
        logger.info("Success!")
        print("-" * 40)
        print(f"Symbol: {data['symbol']}")
        print(f"Price:  {data['underlying_price']}")
        print(f"Expiry: {data['expiry']}")
        print("-" * 40)
        print(f"PCR:       {data['analytics']['pcr']}")
        print(f"Max Pain:  {data['analytics']['max_pain']}")
        print(f"Support:   {data['analytics']['support_strike']} (Max PE OI)")
        print(f"Resistance:{data['analytics']['resistance_strike']} (Max CE OI)")
        print("-" * 40)
