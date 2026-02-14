"""
Manual Test Script for EOD Analytics
Generates and sends the daily report immediately (for testing)
"""

import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.eod_analytics import run_eod_process

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("MANUAL EOD REPORT EXECUTION")
    print("=" * 60)
    print("Generating report based on available data...")
    
    try:
        run_eod_process()
        print("\n[SUCCESS] Report generated and sent successfully!")
    except Exception as e:
        print(f"\n[ERROR] Error generating report: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
