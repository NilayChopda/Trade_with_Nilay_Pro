"""
NilayChopdaScanner - Live Scanner with Telegram Alerts & Auto-Update
Real-time NSE scanning with instant Telegram notifications
"""

import os
import pandas as pd
import logging
from datetime import datetime, time
import time as time_module
import requests
from threading import Thread
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try importing optional libraries
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    from tvdatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    TV_AVAILABLE = False

# Configure logging with UTF-8 encoding
import io
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('nilaychopda_scanner.log', encoding='utf-8'),
        logging.StreamHandler(stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    ]
)
logger = logging.getLogger(__name__)


class TelegramAlertBot:
    """Send alerts via Telegram"""
    
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.last_alert_time = {}  # Rate limiting
    
    def send_alert(self, symbol, price, change, volume, signal_type="STRONG", **kwargs):
        """Send detailed signal alert to Telegram"""
        try:
            # Rate limiting: max 1 alert per symbol per 60 seconds
            current_time = time_module.time()
            if symbol in self.last_alert_time:
                if current_time - self.last_alert_time[symbol] < 60:
                    return  # Skip if alert sent recently
            
            self.last_alert_time[symbol] = current_time
            
            # Build detailed message
            status_emoji = "[DOWN]" if change < 0 else "[UP]" if change > 0 else "[FLAT]"
            strength_indicator = "[HOT]" if abs(change) > 5 else "[STRONG]" if abs(change) > 2 else "[OK]"
            
            message = f"""
===================================================
NilayChopdaScanner Live Alert

SIGNAL TYPE: {signal_type}
SYMBOL: {symbol}
CURRENT PRICE: Rs.{price:.2f}
CHANGE: {change:+.2f}% {status_emoji} {strength_indicator}
VOLUME: {int(volume):,} shares
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}

TRADING STATUS: LIVE
SCANNER: NilayChopdaScanner V2
ACTION: Ready to Trade
===================================================
"""
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✓ Telegram alert sent for {symbol}")
                return True
            else:
                logger.error(f"✗ Telegram alert failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    def send_summary(self, total_scanned, signals_found, top_signals, signals_df=None):
        """Send detailed scan summary"""
        try:
            # Calculate statistics
            top_5 = top_signals[:5] if len(top_signals) >= 5 else top_signals
            
            # Build top signals list with details
            top_signals_str = ""
            if signals_df is not None and len(signals_df) > 0:
                for idx, (_, row) in enumerate(signals_df.head(5).iterrows(), 1):
                    symbol = row['symbol']
                    price = row['price']
                    change = row['change']
                    top_signals_str += f"\n{idx}. {symbol} | Rs.{price:.2f} | {change:+.2f}%"
            else:
                for idx, symbol in enumerate(top_5, 1):
                    top_signals_str += f"\n{idx}. {symbol}"
            
            message = f"""
===================================================
NilayChopdaScanner Daily Summary

SCAN COMPLETE

SCAN STATISTICS:
- Total Symbols Scanned: {total_scanned}
- Signals Detected: {signals_found}
- Success Rate: {(signals_found/max(total_scanned,1)*100):.1f}%

TOP 5 SIGNALS:{top_signals_str}

SCAN TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
STATUS: LIVE Mode (Auto-update Enabled)
NEXT UPDATE: 5 minutes

---------------------------------------------------
FILTER: Rs.50-2000
UPDATE INTERVAL: 5 minutes
MARKET HOURS: 9:15 AM - 3:30 PM IST
===================================================
"""
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=5)
            logger.info("✓ Summary alert sent to Telegram")
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")


class NilayChopdaLiveScanner:
    """Live NSE scanner with continuous updates"""
    
    def __init__(self, telegram_token, telegram_chat_id):
        self.telegram = TelegramAlertBot(telegram_token, telegram_chat_id)
        self.is_running = False
        self.signals = []
        
    def is_market_open(self):
        """Check if NSE market is open"""
        current = datetime.now()
        current_time = current.time()
        current_day = current.weekday()  # 0=Monday, 4=Friday
        
        # NSE market hours: 9:15 AM - 3:30 PM (Monday-Friday)
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Check if today is weekday and within market hours
        if current_day < 5:  # Monday to Friday
            if market_open <= current_time <= market_close:
                return True
        
        return False
    
    def get_live_price(self, symbol):
        """Fetch live price from NSE API"""
        try:
            # Try NSE India's public API (most reliable)
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://www.nseindia.com'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'priceInfo' in data and data['priceInfo']:
                    info = data['priceInfo']
                    if 'lastPrice' in info:
                        live_price = float(info['lastPrice'])
                        return live_price
            
            logger.debug(f"NSE API no data for {symbol}")
            return None
            
        except requests.exceptions.Timeout:
            logger.debug(f"NSE API timeout for {symbol}")
            return None
        except Exception as e:
            logger.debug(f"NSE API error for {symbol}: {str(e)[:30]}")
            return None
    
    def load_scanner_results(self):
        """Load latest scanner results and fetch LIVE prices"""
        try:
            # Load the most recent scan results
            results_dir = '../scanner_results'
            csv_files = [f for f in os.listdir(results_dir) 
                        if f.startswith('results_') and f.endswith('.csv')]
            
            if not csv_files:
                logger.warning("No scanner results found")
                return None
            
            csv_files.sort()
            latest_file = os.path.join(results_dir, csv_files[-1])
            
            df = pd.read_csv(latest_file)
            df = df[df['passes_filter'] == True].copy()  # Only signals
            
            # FILTER: Price range 50-2000
            df = df[(df['price'] >= 50) & (df['price'] <= 2000)].copy()
            
            # FETCH LIVE PRICES
            logger.info("\n" + "="*70)
            logger.info("Fetching LIVE prices from NSE...")
            logger.info("="*70)
            
            prices_updated = 0
            for symbol in df['symbol'].unique():
                try:
                    live_price = self.get_live_price(symbol)
                    if live_price is not None:
                        # Calculate new change percentage
                        old_price = df[df['symbol'] == symbol]['price'].values[0]
                        new_change = ((live_price - old_price) / old_price) * 100
                        
                        df.loc[df['symbol'] == symbol, 'price'] = live_price
                        df.loc[df['symbol'] == symbol, 'change'] = new_change
                        
                        logger.info(f"[OK] {symbol}: Rs.{old_price:.2f} -> Rs.{live_price:.2f} ({new_change:+.2f}%)")
                        prices_updated += 1
                    else:
                        csv_price = df[df['symbol'] == symbol]['price'].values[0]
                        logger.warning(f"[WARN] No live data for {symbol}, using CSV price: Rs.{csv_price:.2f}")
                except Exception as e:
                    logger.warning(f"[ERROR] Failed to get live price for {symbol}: {str(e)[:50]}")
            
            df = df.sort_values('price', ascending=False)
            
            logger.info("="*70)
            logger.info(f"[DONE] Loaded {len(df)} signals with {prices_updated} LIVE prices updated")
            logger.info("="*70 + "\n")
            return df
            
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return None
    
    def monitor_and_alert(self):
        """Monitor signals and send alerts"""
        try:
            df = self.load_scanner_results()
            
            if df is None or len(df) == 0:
                logger.warning("No signals to monitor")
                return
            
            # Pretty header
            logger.info("\n" + "="*70)
            logger.info(">>> NILAYCHOPDASCANNER - LIVE ALERTS <<<")
            logger.info("="*70 + "\n")
            
            logger.info(f"[SIGNALS] Total Signals Found: {len(df)}")
            logger.info(f"[FILTER] Price Range: Rs.50 - Rs.2000")
            logger.info(f"[TIME] Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
            
            # Send alerts for top signals
            top_n = min(18, len(df))
            
            logger.info("="*70)
            logger.info(f"TOP {top_n} SIGNALS (By Price)")
            logger.info("="*70)
            logger.info(f"{'Rank':<6} {'Symbol':<15} {'Price':<15} {'Change':<12} {'Volume':<20}")
            logger.info("-"*70)
            
            top_signals = []
            for idx, (_, row) in enumerate(df.head(top_n).iterrows(), 1):
                symbol = row['symbol']
                price = row['price']
                change = row['change']
                volume = row['volume']
                
                top_signals.append(symbol)
                
                # Format change with indicators
                change_str = f"{change:+.2f}%"
                if change > 5:
                    change_indicator = "**HOT**"
                elif change > 2:
                    change_indicator = "STRONG"
                elif change > 0:
                    change_indicator = "POSITIVE"
                else:
                    change_indicator = "NEGATIVE"
                
                vol_str = f"{int(volume):,}" if volume >= 1000 else f"{volume:.0f}"
                logger.info(f"{idx:<6} {symbol:<15} Rs.{price:<14.2f} {change_indicator:<12} {vol_str:<20}")
                
                # Send individual alerts for top signals
                self.telegram.send_alert(symbol, price, change, volume, signal_type="TOP")
            
            logger.info("-"*70)
            logger.info("")
            
            # Send summary
            self.telegram.send_summary(len(df), len(df), top_signals, signals_df=df)
            
            # Save to local file
            self.save_session_results(df)
            
            logger.info("[SUCCESS] All alerts sent to Telegram")
            logger.info(f"[ALERTS] Total alerts sent: {top_n} signals + 1 summary")
            logger.info(f"[DESTINATION] @nilaychopda (Chat ID: 810052560)\n")
            
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
    
    def save_session_results(self, df):
        """Save current session results with detailed formatting"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save as CSV
            csv_filename = f"live_session_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            
            # Save as JSON
            json_filename = f"live_session_{timestamp}.json"
            df.to_json(json_filename, orient='records', indent=2)
            
            # Create summary HTML
            html_filename = f"live_session_{timestamp}.html"
            self.save_session_html(df, html_filename, timestamp)
            
            logger.info(f"✓ Session results saved:")
            logger.info(f"  • CSV: {csv_filename}")
            logger.info(f"  • JSON: {json_filename}")
            logger.info(f"  • HTML: {html_filename}")
            
        except Exception as e:
            logger.error(f"Error saving session results: {e}")
    
    def save_session_html(self, df, filename, timestamp):
        """Save session results as HTML report"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NilayChopdaScanner - Live Session Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-box h3 {{
            margin: 0;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .stat-box .value {{
            font-size: 2em;
            font-weight: bold;
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .symbol {{
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }}
        .price {{
            color: #667eea;
            font-weight: bold;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 NilayChopdaScanner</h1>
            <p>Live Trading Signal Analysis Report</p>
            <p style="color: #999; font-size: 0.9em;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>Total Signals</h3>
                <div class="value">{len(df)}</div>
            </div>
            <div class="stat-box">
                <h3>Avg Price</h3>
                <div class="value">₹{df['price'].mean():.0f}</div>
            </div>
            <div class="stat-box">
                <h3>Price Range</h3>
                <div class="value">₹{df['price'].min():.0f} - ₹{df['price'].max():.0f}</div>
            </div>
            <div class="stat-box">
                <h3>Total Volume</h3>
                <div class="value">{int(df['volume'].sum()):,}</div>
            </div>
        </div>
        
        <h2 style="color: #333;">📊 Signal Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Symbol</th>
                    <th>Price (₹)</th>
                    <th>Change</th>
                    <th>Volume</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for idx, (_, row) in enumerate(df.head(18).iterrows(), 1):
                symbol = row['symbol']
                price = row['price']
                change = row['change']
                volume = row['volume']
                
                change_class = "positive" if change > 0 else "negative"
                change_indicator = "🔥" if abs(change) > 5 else "⭐" if abs(change) > 2 else "✓"
                
                html_content += f"""
                <tr>
                    <td>{idx}</td>
                    <td class="symbol">{symbol}</td>
                    <td class="price">₹{price:.2f}</td>
                    <td class="{change_class}">{change_indicator} {change:+.2f}%</td>
                    <td>{int(volume):,}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>🔄 Scanner Status: LIVE</p>
            <p>📱 Alerts sent to: @nilaychopda</p>
            <p>⏰ Market Hours: 9:15 AM - 3:30 PM IST (Weekdays)</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def run_continuous(self):
        """Run continuous live scanning"""
        logger.info("\n" + "="*70)
        logger.info("NILAYCHOPDASCANNER - LIVE MODE")
        logger.info("="*70)
        logger.info("Scanner is running in LIVE mode with auto-updates")
        logger.info("Telegram alerts: ENABLED")
        logger.info("Market monitoring: ENABLED")
        logger.info("="*70 + "\n")
        
        self.is_running = True
        scan_interval = 300  # Scan every 5 minutes during market hours
        
        try:
            while self.is_running:
                if self.is_market_open():
                    logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Running live scan...")
                    self.monitor_and_alert()
                    logger.info(f"Next scan in {scan_interval} seconds...")
                    
                    # Sleep but check every 10 seconds if market closed
                    for _ in range(scan_interval // 10):
                        if not self.is_market_open():
                            break
                        time_module.sleep(10)
                else:
                    # Market closed
                    current_time = datetime.now().strftime('%H:%M:%S')
                    logger.info(f"[{current_time}] Market closed. Next scan at 9:15 AM IST")
                    time_module.sleep(60)  # Check every minute if market reopened
                    
        except KeyboardInterrupt:
            logger.info("\n✓ Scanner stopped by user")
            self.is_running = False


def main():
    """Main function"""
    
    # Get Telegram credentials (with hardcoded fallback)
    tg_token = os.getenv('TG_BOT_TOKEN') or "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs"
    tg_chat_id = os.getenv('TG_CHAT_ID') or "810052560"
    
    if not tg_token or not tg_chat_id:
        logger.error("Error: Telegram credentials not set!")
        logger.error("Set environment variables:")
        logger.error("  TG_BOT_TOKEN = Your bot token")
        logger.error("  TG_CHAT_ID = Your chat ID")
        return
    
    logger.info(f"Telegram Bot Connected: ✓")
    logger.info(f"Chat ID: {tg_chat_id}")
    
    # Initialize scanner
    scanner = NilayChopdaLiveScanner(tg_token, tg_chat_id)
    
    # Run initial scan
    scanner.monitor_and_alert()
    
    # Option to run continuous mode
    print("\n" + "="*70)
    print("NILAYCHOPDASCANNER - LIVE MODE")
    print("="*70)
    print("\nOptions:")
    print("1. Single scan (already completed)")
    print("2. Run continuous live mode (9:15 AM - 3:30 PM IST)")
    print("\nPress Ctrl+C to stop at any time")
    print("="*70)
    
    try:
        # Run continuous scanning
        print("\nStarting continuous live mode...")
        scanner.run_continuous()
    except KeyboardInterrupt:
        logger.info("\n✓ Scanner stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
