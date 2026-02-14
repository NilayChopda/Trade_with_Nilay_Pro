"""
Market Hours Scheduler for Trade With Nilay
Runs data collection every 1 minute during market hours (9:15 AM - 3:30 PM IST)

Production features:
- Market hours detection
- 1-minute data collection
- EOD processing at market close
- Symbol universe refresh at 8:00 AM
- Health monitoring
"""

import time
import logging
import schedule
import argparse
from datetime import datetime, time as dt_time
from pathlib import Path
import pytz

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from services.fetcher_v2 import MultiSourceFetcher
from services.symbol_manager import SymbolManager
from database.db import log_system_health

logger = logging.getLogger("twn.scheduler")

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Market hours (IST)
MARKET_OPEN_TIME = dt_time(9, 15)   # 9:15 AM
MARKET_CLOSE_TIME = dt_time(15, 30)  # 3:30 PM
PRE_MARKET_TIME = dt_time(8, 0)     # 8:00 AM for symbol refresh

# Days when market is open (Monday=0, Friday=4)
MARKET_DAYS = [0, 1, 2, 3, 4]  # Mon-Fri

def is_market_open() -> bool:
    """Check if market is currently open"""
    now = datetime.now(IST)
    
    # Check if it's a market day (Mon-Fri)
    if now.weekday() not in MARKET_DAYS:
        return False
    
    current_time = now.time()
    
    # Check if within market hours
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def is_pre_market() -> bool:
    """Check if it's pre-market time (for symbol refresh)"""
    now = datetime.now(IST)
    
    if now.weekday() not in MARKET_DAYS:
        return False
    
    current_time = now.time()
    return PRE_MARKET_TIME <= current_time < MARKET_OPEN_TIME


def run_data_collection():
    """Main data collection task - runs every 1 minute during market hours"""
    if not is_market_open():
        logger.info("Market is closed. Skipping data collection.")
        return
    
    try:
        logger.info("=" * 60)
        logger.info(f"Starting data collection cycle at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
        logger.info("=" * 60)
        
        fetcher = MultiSourceFetcher()
        
        # Fetch all equity data (full 2234 stocks in production)
        # For testing: use limit=100
        stats = fetcher.fetch_all_equity(limit=None)  # None = all stocks
        
        logger.info(f"✓ Data collection complete: {stats['successful']}/{stats['total']} symbols ({stats['success_rate']:.1f}%)")
        
        # Log health
        log_system_health(
            component='scheduler',
            status='healthy',
            message=f"Data collection successful: {stats['successful']}/{stats['total']} symbols"
        )
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        log_system_health(
            component='scheduler',
            status='down',
            error_count=1,
            message=f"Data collection failed: {str(e)}"
        )


def run_symbol_refresh():
    """Refresh symbol universe - runs daily at 8:00 AM"""
    if not is_pre_market():
        return
    
    try:
        logger.info("=" * 60)
        logger.info("Refreshing symbol universe...")
        logger.info("=" * 60)
        
        manager = SymbolManager()
        manager.update_all_caches()
        
        logger.info("✓ Symbol universe refreshed successfully")
        
    except Exception as e:
        logger.error(f"Symbol refresh failed: {e}", exc_info=True)


def run_eod_tasks():
    """End of day processing - runs at market close (3:30 PM)"""
    try:
        logger.info("=" * 60)
        logger.info("Running EOD (End of Day) tasks...")
        logger.info("=" * 60)
        
        # TODO: Phase 4 - Generate EOD reports
        # For now, just log
        logger.info("✓ EOD tasks complete (Phase 4 will add full reports)")
        
    except Exception as e:
        logger.error(f"EOD tasks failed: {e}", exc_info=True)


def health_check():
    """Regular health check - runs every 5 minutes"""
    try:
        from database.db import get_conn
        
        # Check database connectivity
        conn = get_conn()
        result = conn.execute("SELECT COUNT(*) FROM minute_data").fetchone()
        total_records = result[0] if result else 0
        conn.close()
        
        logger.info(f"Health check: OK (Database has {total_records} records)")
        
        log_system_health(
            component='scheduler',
            status='healthy',
            message=f"Database accessible with {total_records} records"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        log_system_health(
            component='scheduler',
            status='degraded',
            error_count=1,
            message=f"Health check failed: {str(e)}"
        )


def setup_schedule():
    """Set up scheduled jobs"""
    
    # Data collection: Every 1 minute during market hours
    schedule.every(1).minutes.do(run_data_collection)
    
    # Symbol refresh: Daily at 8:00 AM
    schedule.every().day.at("08:00").do(run_symbol_refresh)
    
    # EOD tasks: Daily at 3:35 PM (5 min after market close)
    schedule.every().day.at("15:35").do(run_eod_tasks)
    
    # Health check: Every 5 minutes
    schedule.every(5).minutes.do(health_check)
    
    logger.info("Scheduled jobs configured:")
    logger.info("  - Data collection: Every 1 minute (during market hours)")
    logger.info("  - Symbol refresh: Daily at 8:00 AM")
    logger.info("  - EOD tasks: Daily at 3:35 PM")
    logger.info("  - Health check: Every 5 minutes")


def main_loop():
    """Main scheduler loop"""
    logger.info("=" * 60)
    logger.info("TRADE WITH NILAY - Market Data Scheduler")
    logger.info("=" * 60)
    logger.info(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    logger.info(f"Market hours: {MARKET_OPEN_TIME.strftime('%H:%M')} - {MARKET_CLOSE_TIME.strftime('%H:%M')} IST (Mon-Fri)")
    logger.info("=" * 60)
    
    # Setup schedule
    setup_schedule()
    
    # Initial health check
    health_check()
    
    logger.info("\nScheduler started. Press Ctrl+C to stop.\n")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Check every second
            
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(5)


def run_once():
    """Run a single cycle of all relevant tasks and exit"""
    logger.info("=" * 60)
    logger.info("TRADE WITH NILAY - Single Cycle Execution")
    logger.info("=" * 60)
    logger.info(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # 1. Check for symbol refresh (8:00 AM)
    if is_pre_market():
        run_symbol_refresh()
    
    # 2. Check for market hours data collection
    if is_market_open():
        run_data_collection()
    
    # 3. Check for EOD tasks (after 3:35 PM)
    now = datetime.now(IST).time()
    if now >= dt_time(15, 35) and now <= dt_time(16, 0):
        run_eod_tasks()
    
    # 4. Health check
    health_check()
    
    logger.info("=" * 60)
    logger.info("Cycle complete. Exiting.")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(__file__).parent / "logs" / "scheduler.log"),
            logging.StreamHandler()
        ]
    )
    
    # Ensure logs directory exists
    (Path(__file__).parent / "logs").mkdir(exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Trade With Nilay - Market Data Scheduler")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        main_loop()
