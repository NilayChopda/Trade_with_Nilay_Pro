"""
NilayChopdaScanner - Daily Auto-Scheduler
Runs automatically every day at 9:15 AM IST without manual intervention
"""

import schedule
import time
from datetime import datetime
import subprocess
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [AUTO-SCHEDULER] - %(message)s',
    handlers=[
        logging.FileHandler('nilaychopda_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyAutoScheduler:
    """Automatically runs NilayChopdaScanner at set times"""
    
    def __init__(self):
        self.scanner_path = os.path.join(os.path.dirname(__file__), 'nilaychopda_live_scanner.py')
        self.python_exe = sys.executable
        
    def run_scanner(self):
        """Execute scanner"""
        try:
            logger.info("="*70)
            logger.info("STARTING DAILY SCAN")
            logger.info("="*70)
            
            # Run the scanner
            subprocess.Popen([self.python_exe, self.scanner_path])
            
            logger.info("Scanner started successfully")
            logger.info("Monitoring will continue for next 6 hours until 3:30 PM")
            
        except Exception as e:
            logger.error(f"Failed to start scanner: {e}")
    
    def schedule_daily_scans(self):
        """Schedule scanner to run at specific times"""
        
        # Run at 9:15 AM
        schedule.every().day.at("09:15").do(self.run_scanner)
        logger.info("Scheduled scanner at 09:15 AM IST")
        
        logger.info("\n" + "="*70)
        logger.info("NILAYCHOPDASCANNER - AUTO-SCHEDULER ACTIVE")
        logger.info("="*70)
        logger.info("Scanner will run EVERY DAY at 09:15 AM IST")
        logger.info("No manual intervention needed!")
        logger.info("Keep this window/process running in background")
        logger.info("="*70 + "\n")
    
    def start_scheduler(self):
        """Keep scheduler running"""
        self.schedule_daily_scans()
        
        logger.info("Scheduler started. Waiting for scheduled time...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")


def main():
    scheduler = DailyAutoScheduler()
    scheduler.start_scheduler()


if __name__ == '__main__':
    main()
