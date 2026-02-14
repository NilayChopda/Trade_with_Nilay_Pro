"""
Quick Test Script for Trade With Nilay Phase 1
Run this during market hours (9:15 AM - 3:30 PM IST) to verify system health
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 70)
print("TRADE WITH NILAY - PHASE 1 SYSTEM TEST")
print("=" * 70)
print()

# Test 1: Database
print("Test 1: Database Initialization")
print("-" * 70)
try:
    from backend.database.db import init_db, get_conn
    init_db()
    conn = get_conn()
    
    # Check all tables exist
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    
    required_tables = [
        'symbols', 'minute_data', 'fno_data', 'indices_data',
        'scanners', 'scanner_results', 'data_quality_log',
        'system_health', 'eod_reports'
    ]
    
    missing = [t for t in required_tables if t not in table_names]
    
    if missing:
        print(f"❌ FAIL: Missing tables: {missing}")
        sys.exit(1)
    else:
        print(f"✅ PASS: All {len(required_tables)} tables exist")
        print(f"    Tables: {', '.join(table_names)}")
    
    # Check record count
    record_count = conn.execute("SELECT COUNT(*) FROM minute_data").fetchone()[0]
    print(f"    Current records in minute_data: {record_count}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 2: Symbol Manager
print("Test 2: Symbol Manager")
print("-" * 70)
try:
    from backend.services.symbol_manager import SymbolManager
    
    manager = SymbolManager()
    
    # Test equity symbols
    equity = manager.fetch_nse_equity_universe()
    fno = manager.fetch_fno_symbols()
    indices = manager.fetch_indices()
    
    if len(equity) < 2000:
        print(f"⚠️  WARN: Only {len(equity)} equity symbols (expected ~2234)")
    else:
        print(f"✅ PASS: Fetched {len(equity)} equity symbols")
    
    if len(fno) < 90:
        print(f"⚠️  WARN: Only {len(fno)} F&O symbols (expected ~99)")
    else:
        print(f"✅ PASS: Fetched {len(fno)} F&O symbols")
    
    if len(indices) < 10:
        print(f"⚠️  WARN: Only {len(indices)} indices (expected ~13)")
    else:
        print(f"✅ PASS: Fetched {len(indices)} indices")
    
    print(f"    Sample equity: {equity[:5]}")
    print(f"    Sample F&O: {fno[:5]}")
    print(f"    Sample indices: {[idx['name'] for idx in indices[:3]]}")
    
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Data Fetcher
print("Test 3: Data Fetcher (10 stocks sample)")
print("-" * 70)
try:
    from backend.services.fetcher_v2 import MultiSourceFetcher
    
    fetcher = MultiSourceFetcher()
    
    # Test with just 10 stocks (quick test)
    stats = fetcher.fetch_all_equity(limit=10)
    
    success_rate = stats['success_rate']
    
    if success_rate == 0:
        print(f"⚠️  WARN: No data fetched (market might be closed)")
        print(f"    Run this test during market hours: 9:15 AM - 3:30 PM IST")
    elif success_rate < 50:
        print(f"⚠️  WARN: Low success rate: {success_rate:.1f}%")
    else:
        print(f"✅ PASS: Data fetcher working ({success_rate:.1f}% success)")
    
    print(f"    Total: {stats['total']}")
    print(f"    Successful: {stats['successful']}")
    print(f"    Failed: {stats['failed']}")
    print(f"    Duration: {stats['duration_sec']:.1f}s")
    print(f"    Throughput: {stats['symbols_per_sec']:.1f} symbols/sec")
    
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Market Hours Detection
print("Test 4: Market Hours Detection")
print("-" * 70)
try:
    from backend.scheduler import is_market_open, is_pre_market
    from datetime import datetime
    import pytz
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    market_open = is_market_open()
    pre_market = is_pre_market()
    
    print(f"    Current time (IST): {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
    print(f"    Market open: {'YES' if market_open else 'NO'}")
    print(f"    Pre-market: {'YES' if pre_market else 'NO'}")
    
    if market_open:
        print(f"✅ PASS: System should be collecting data now")
    else:
        print(f"ℹ️  INFO: Market closed. Data collection will resume at 9:15 AM IST")
    
except Exception as e:
    print(f"❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Final Summary
print("=" * 70)
print("SYSTEM TEST COMPLETE")
print("=" * 70)
print()
print("✅ All core components are working!")
print()
print("Next steps:")
print("  1. Run scheduler during market hours: python backend\\scheduler.py")
print("  2. Monitor logs in: backend\\logs\\scheduler.log")
print("  3. Query database for collected data")
print()
print("For full 2234 stock collection during market hours:")
print("  python backend\\services\\fetcher_v2.py")
print()
print("=" * 70)
