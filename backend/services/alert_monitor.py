"""
Real-Time Alert Monitor for Trade With Nilay
Monitors scanner results and sends Telegram alerts for new stocks in 0-3% range
"""

import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import get_conn
from backend.services.telegram import send_telegram_message

logger = logging.getLogger("twn.alert_monitor")

class AlertMonitor:
    """Monitors scanner results and sends real-time alerts"""
    
    def __init__(self, check_interval=60):
        """
        Initialize alert monitor
        
        Args:
            check_interval: Seconds between checks (default: 60)
        """
        self.check_interval = check_interval
        self.alerted_stocks = set()  # Track already alerted stocks
        self.last_check = datetime.now()
        logger.info("Alert Monitor initialized")
    
    def check_for_new_stocks(self):
        """Check for new stocks in 0-3% range and send alerts"""
        try:
            conn = get_conn()
            
            # Get unalerted results
            query = """
                SELECT sr.symbol, sr.price, sr.change_pct, sr.volume, sr.timestamp, s.name, s.scanner_type
                FROM scanner_results sr
                JOIN scanners s ON sr.scanner_id = s.id
                WHERE sr.alerted = 0
                ORDER BY sr.timestamp DESC
                LIMIT 50
            """
            
            cursor = conn.execute(query)
            new_stocks = cursor.fetchall()
            conn.close()
            
            if new_stocks:
                logger.info(f"Found {len(new_stocks)} unalerted stocks")
                
                for stock in new_stocks:
                    symbol, price, change_pct, volume, timestamp, scanner_name, scanner_type = stock
                    
                    # Skip if already alerted in this session (double check)
                    if symbol in self.alerted_stocks:
                        continue

                    # Filter Logic
                    should_alert = False
                    
                    if "SMC" in scanner_name or "SMC" in str(scanner_type):
                        should_alert = True
                    elif 0 <= change_pct <= 3.5:
                        should_alert = True
                        
                    if not should_alert:
                        # Mark as alerted to avoid reprocessing
                        self.mark_as_alerted(symbol, timestamp) 
                        continue
                    
                    # Check timestamp age (don't alert on very old scans if restarting)
                    try:
                        ts = int(timestamp)
                    except:
                        # Handle string timestamp (legacy)
                        try:
                            dt = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
                            ts = int(dt.timestamp())
                        except:
                            ts = int(time.time()) # Fallback
                            
                    if time.time() - ts > 3600 * 4: # Older than 4 hours
                         self.mark_as_alerted(symbol, timestamp)
                         continue
                    
                    # Send Telegram alert
                    self.send_stock_alert(symbol, price, change_pct, volume, timestamp, scanner_name)
                    
                    # Mark as alerted in database
                    self.mark_as_alerted(symbol, timestamp)
                    
                    # Add to session cache
                    self.alerted_stocks.add(symbol)
                    
                    # Small delay
                    time.sleep(0.5)
            
            # Update last check time
            self.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking for new stocks: {e}", exc_info=True)
    
    def send_stock_alert(self, symbol, price, change_pct, volume, timestamp, scanner_name="Scanner"):
        """Send formatted Telegram alert for a stock"""
        try:
            # Format timestamp
            try:
                dt = datetime.fromtimestamp(int(timestamp))
            except:
                dt = datetime.now()
                
            time_str = dt.strftime("%H:%M:%S")
            
            # Create alert message
            message = f"""
🎯 *{scanner_name.upper()} ALERT*

📊 *{symbol}*
💰 Price: ₹{price:.2f}
📈 Change: +{change_pct:.2f}%
📊 Volume: {volume:,}
🕐 Time: {time_str}

🚀 *Setup Detected*
            """.strip()
            
            # Send to Telegram
            send_telegram_message(message)
            logger.info(f"Alert sent for {symbol}")
            
        except Exception as e:
            logger.error(f"Error sending alert for {symbol}: {e}")
    
    def mark_as_alerted(self, symbol, timestamp):
        """Mark stock as alerted in database"""
        try:
            conn = get_conn()
            conn.execute(
                """
                UPDATE scanner_results 
                SET alerted = 1, alert_sent_at = ?
                WHERE symbol = ? AND timestamp = ?
                """,
                (int(datetime.now().timestamp()), symbol, timestamp)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error marking {symbol} as alerted: {e}")
    
    def run(self):
        """Run continuous monitoring loop"""
        logger.info(f"Starting alert monitor (check every {self.check_interval}s)")
        
        while True:
            try:
                self.check_for_new_stocks()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Alert monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.check_interval)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run monitor
    monitor = AlertMonitor(check_interval=60)
    monitor.run()
