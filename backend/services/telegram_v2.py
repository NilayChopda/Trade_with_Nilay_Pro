"""
Enhanced Telegram Notification System for Trade With Nilay
Sends beautifully formatted alerts with stock scanner results

Features:
- Rich message formatting (Markdown)
- Rate limiting (max 1 msg per 3 seconds)
- Retry logic for failed sends
- Multiple message types (scanner alerts, EOD reports, errors)
- Alert deduplication
- Uses synchronous requests for simplicity and reliability
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import pytz
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import mark_scanner_alerted

load_dotenv(Path(__file__).resolve().parent.parent / "config" / "keys.env")

logger = logging.getLogger("twn.telegram")

# Get credentials from env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_API")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Rate limiting
LAST_SEND_TIME = 0
MIN_SEND_INTERVAL = 3  # seconds


class TelegramNotifier:
    """Enhanced Telegram notification system using requests"""
    
    def __init__(self):
        if not BOT_TOKEN or not CHAT_ID:
            logger.warning("Telegram credentials not configured!")
            self.enabled = False
            return
        
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.enabled = True
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        logger.info("Telegram notifier initialized (sync mode)")
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        global LAST_SEND_TIME
        
        now = time.time()
        time_since_last = now - LAST_SEND_TIME
        
        if time_since_last < MIN_SEND_INTERVAL:
            sleep_time = MIN_SEND_INTERVAL - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        LAST_SEND_TIME = time.time()
    
    def send_message(self, text: str, parse_mode: str = 'Markdown', retry: int = 3) -> bool:
        """
        Send a message with retries using requests
        
        Args:
            text: Message text (supports Markdown)
            parse_mode: 'Markdown' or 'HTML'
            retry: Number of retries on failure
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram not configured, skipping message")
            return False
        
        self._rate_limit()
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        for attempt in range(retry):
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                
                logger.info("Message sent successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to send message (attempt {attempt+1}/{retry}): {e}")
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def send_scanner_alert(self, scanner_name: str, stocks: List[Dict]) -> bool:
        """
        Send formatted scanner alert
        
        Expected format:
        🔔 NILAY SWING PICK ALERT
        
        RELIANCE | ₹2,450.50 | +1.25% | Vol: 1.2M | 10:30 AM
        TCS | ₹3,890.00 | +2.80% | Vol: 850K | 10:30 AM
        
        ---
        Scanner: nilay-swing-pick-algo
        Time: 2026-02-07 10:30:15 IST
        """
        if not stocks:
            logger.info("No stocks to alert")
            return False
        
        # Build message
        lines = []
        lines.append("🔔 *STOCK ALERT*")
        lines.append("")
        
        # Add each stock
        for stock in stocks:
            symbol = stock.get('symbol', 'N/A')
            price = stock.get('price', 0)
            change_pct = stock.get('change_pct', 0)
            volume = stock.get('volume', 0)
            
            # Format volume (M for millions, K for thousands)
            if volume >= 1_000_000:
                vol_str = f"{volume/1_000_000:.1f}M"
            elif volume >= 1_000:
                vol_str = f"{volume/1_000:.0f}K"
            else:
                vol_str = f"{volume:,.0f}"
            
            # Current time
            now = datetime.now(IST)
            time_str = now.strftime('%I:%M %p')
            
            # Format: SYMBOL | PRICE | %CHANGE | VOLUME | TIME
            line = f"*{symbol}* | ₹{price:,.2f} | {change_pct:+.2f}% | Vol: {vol_str} | {time_str}"
            lines.append(line)
        
        lines.append("")
        lines.append("---")
        lines.append(f"Scanner: `{scanner_name}`")
        lines.append(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        message = "\n".join(lines)
        
        return self.send_message(message)
    
    def send_equity_filter_alert(self, stocks: List[Dict], min_change: float = 0.0, max_change: float = 3.0) -> bool:
        """
        Send alert for stocks within equity filter range (0% to +3%)
        
        Args:
            stocks: List of stock dicts
            min_change: Minimum % change
            max_change: Maximum % change
        """
        # Filter stocks within range
        filtered = [
            s for s in stocks
            if s.get('change_pct') is not None
            and min_change <= s['change_pct'] <= max_change
        ]
        
        if not filtered:
            logger.info(f"No stocks in range {min_change}% to {max_change}%")
            return False
        
        # Build message
        lines = []
        lines.append("🎯 *EQUITY FILTER ALERT*")
        lines.append(f"*Range:* {min_change:+.1f}% to {max_change:+.1f}%")
        lines.append("")
        
        # Sort by change percentage
        sorted_stocks = sorted(filtered, key=lambda x: x.get('change_pct', 0), reverse=True)
        
        for stock in sorted_stocks[:10]:  # Limit to 10 stocks
            symbol = stock.get('symbol', 'N/A')
            price = stock.get('price', 0)
            change_pct = stock.get('change_pct', 0)
            volume = stock.get('volume', 0)
            
            # Format volume
            if volume >= 1_000_000:
                vol_str = f"{volume/1_000_000:.1f}M"
            elif volume >= 1_000:
                vol_str = f"{volume/1_000:.0f}K"
            else:
                vol_str = f"{volume:,.0f}" if volume else "N/A"
            
            line = f"*{symbol}* | ₹{price:,.2f} | {change_pct:+.2f}% | Vol: {vol_str}"
            lines.append(line)
        
        if len(filtered) > 10:
            lines.append(f"\n_...and {len(filtered)-10} more stocks_")
        
        lines.append("")
        lines.append(f"Total: {len(filtered)} stocks")
        lines.append(f"Time: {datetime.now(IST).strftime('%H:%M:%S IST')}")
        
        message = "\n".join(lines)
        
        return self.send_message(message)
    
    def send_error_alert(self, component: str, error_msg: str) -> bool:
        """Send error notification"""
        message = f"⚠️ *ERROR ALERT*\n\nComponent: `{component}`\nError: {error_msg}\n\nTime: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}"
        return self.send_message(message)
    
    def send_eod_report(self, report_data: Dict) -> bool:
        """Send End of Day report"""
        lines = []
        lines.append("📊 *END OF DAY REPORT*")
        lines.append("")
        lines.append(f"Date: {report_data.get('date', datetime.now(IST).strftime('%Y-%m-%d'))}")
        lines.append(f"Total Stocks: {report_data.get('total_stocks', 0):,}")
        lines.append(f"Gainers: {report_data.get('gainers', 0):,}")
        lines.append(f"Losers: {report_data.get('losers', 0):,}")
        lines.append(f"Unchanged: {report_data.get('unchanged', 0):,}")
        lines.append("")
        
        if 'top_gainer' in report_data:
            lines.append(f"🔥 Top Gainer: *{report_data['top_gainer']}* ({report_data.get('top_gainer_pct', 0):+.2f}%)")
        
        if 'top_loser' in report_data:
            lines.append(f"❄️ Top Loser: *{report_data['top_loser']}* ({report_data.get('top_loser_pct', 0):+.2f}%)")
        
        lines.append("")
        lines.append(f"Market Sentiment: {report_data.get('market_sentiment', 'Neutral').upper()}")
        
        message = "\n".join(lines)
        
        return self.send_message(message)
    
    def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        message = (
            "✅ *Test Message*\n\n"
            "Trade With Nilay Telegram Bot is working!\n\n"
            f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}"
        )
        return self.send_message(message)


# Global instance
_notifier = None

def get_notifier() -> TelegramNotifier:
    """Get global Telegram notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


# Convenience functions
def send_scanner_alert(scanner_name: str, stocks: List[Dict]) -> bool:
    """Send scanner alert"""
    return get_notifier().send_scanner_alert(scanner_name, stocks)


def send_equity_filter_alert(stocks: List[Dict], min_change: float = 0.0, max_change: float = 3.0) -> bool:
    """Send equity filter alert"""
    return get_notifier().send_equity_filter_alert(stocks, min_change, max_change)


def send_test_message() -> bool:
    """Send test message"""
    return get_notifier().send_test_message()


if __name__ == "__main__":
    # Test the Telegram notifier
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Testing Telegram notifier...")
    
    # Test 1: Simple test message
    logger.info("\n1. Sending test message...")
    success = send_test_message()
    logger.info(f"  Result: {'✓ Success' if success else '✗ Failed'}")
    
    time.sleep(4)
    
    # Test 2: Scanner alert
    logger.info("\n2. Sending scanner alert...")
    test_stocks = [
        {'symbol': 'RELIANCE', 'price': 2450.50, 'change_pct': 1.25, 'volume': 1200000},
        {'symbol': 'TCS', 'price': 3890.00, 'change_pct': 2.80, 'volume': 850000},
        {'symbol': 'INFY', 'price': 1567.80, 'change_pct': 0.95, 'volume': 2100000}
    ]
    success = send_scanner_alert('nilay-swing-pick-algo', test_stocks)
    logger.info(f"  Result: {'✓ Success' if success else '✗ Failed'}")
    
    time.sleep(4)
    
    # Test 3: Equity filter alert
    logger.info("\n3. Sending equity filter alert...")
    success = send_equity_filter_alert(test_stocks, min_change=0.0, max_change=3.0)
    logger.info(f"  Result: {'✓ Success' if success else '✗ Failed'}")
    
    logger.info("\nAll tests complete!")
