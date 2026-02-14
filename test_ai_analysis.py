import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scanner.scanner_engine import ScannerEngine

def test_ai_analysis():
    logging.basicConfig(level=logging.INFO)
    engine = ScannerEngine()
    
    # Mock stock data (e.g. RELIANCE)
    stock_data = {
        'symbol': 'RELIANCE',
        'price': 2500.0,
        'change_pct': 1.5,
        'volume': 5000000
    }
    
    print("Testing AI Analysis for RELIANCE...")
    try:
        analysis = engine.get_ai_analysis(stock_data)
        print(f"Score: {analysis['score']}/10")
        print(f"Rating: {analysis['rating']}")
        print("Reasons:")
        for r in analysis['reasons']:
            print(f"- {r}")
        print(f"Explanation: {analysis.get('explanation', 'None')}")
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analysis()
