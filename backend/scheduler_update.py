from datetime import datetime
import logging
from .services.eod_analytics import run_eod_process

# ... inside setup_schedule() ...

def setup_schedule():
    """Set up scheduled jobs"""
    # ... existing jobs ...
    
    # EOD Report: Daily at 3:35 PM
    schedule.every().day.at("15:35").do(run_eod_process)
    logger.info("  - EOD Report: Daily at 15:35 IST")
