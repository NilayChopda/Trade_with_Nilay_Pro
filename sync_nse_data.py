
import logging
import pandas as pd
from datetime import datetime, timedelta
import time
from database import get_db, init_db
from kite_provider import download_bhavcopy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twn.sync_nse")

def sync_historical_data(days=30):
    """Syncs historical data from NSE Bhavcopy for the last N days."""
    init_db()
    today = datetime.now()
    
    for i in range(days):
        date = today - timedelta(days=i)
        # Skip weekends
        if date.weekday() >= 5:
            continue
            
        logger.info(f"Syncing data for {date.strftime('%Y-%m-%d')}...")
        
        try:
            df = download_bhavcopy(date)
            if df is not None and not df.empty:
                # NSE Bhavcopy columns often vary, we need to map them
                # Standard: SYMBOL, OPEN, HIGH, LOW, CLOSE, TOTTRDQTY, DATE1
                # Check column names
                cols = {c.upper(): c for c in df.columns}
                
                with get_db() as conn:
                    for _, row in df.iterrows():
                        symbol = str(row[cols.get('SYMBOL', 'SYMBOL')]).strip()
                        # Only equity
                        series = str(row.get('SERIES', 'EQ')).strip()
                        if series != 'EQ': continue
                        
                        try:
                            conn.execute("""
                                INSERT OR REPLACE INTO historical_prices (symbol, date, open, high, low, close, volume)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                symbol,
                                date.strftime('%Y-%m-%d'),
                                float(row[cols.get('OPEN', 'OPEN')]),
                                float(row[cols.get('HIGH', 'HIGH')]),
                                float(row[cols.get('LOW', 'LOW')]),
                                float(row[cols.get('CLOSE', 'CLOSE')]),
                                int(row[cols.get('TOTTRDQTY', cols.get('VOLUME', 'VOLUME'))])
                            ))
                        except Exception as e:
                            logger.debug(f"Row insert fail: {e}")
                    conn.commit()
                logger.info(f"Successfully synced {len(df)} stocks for {date.strftime('%Y-%m-%d')}")
            else:
                logger.warning(f"No data for {date.strftime('%Y-%m-%d')}")
        except Exception as e:
            logger.error(f"Error syncing {date}: {e}")
            
        time.sleep(1) # Avoid rate limits

if __name__ == "__main__":
    sync_historical_data(5) # Sync last 5 days
