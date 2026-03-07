
import logging
import sys
from scanner import MarketScanner
from database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_scanner")

def test_scan():
    init_db()
    scanner = MarketScanner()
    # Test only 5 symbols to avoid long wait
    scanner.symbols_equity = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    print(f"Starting test scan for symbols: {scanner.symbols_equity}")
    results = scanner.run_scan()
    print(f"Scan completed. Found {len(results)} results.")
    for res in results:
        print(f"Symbol: {res['symbol']}, Price: {res['price']}, Change: {res['change_pct']}%, Type: {res['scan_type']}")

if __name__ == "__main__":
    test_scan()
