"""
Telegram Bot for Scanner Alerts

This module handles Telegram notifications for the stock scanner,
including Order Block alerts and general scanner notifications.
"""

import telebot
import os
import logging
from typing import Dict, Any
import sys
from pathlib import Path

# Add src to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from config import TG_BOT_TOKEN, TG_CHAT_ID
except ImportError:
    TG_BOT_TOKEN = None
    TG_CHAT_ID = None

logger = logging.getLogger(__name__)


class ScannerBot:
    """
    Telegram bot for sending scanner alerts and notifications.

    Handles various types of messages:
    - Order Block tap alerts
    - Swing scan results
    - General scanner notifications
    """

    def __init__(self, token=None, chat_id=None):
        """
        Initialize the Telegram bot.

        Args:
            token: Telegram bot token (from @BotFather)
            chat_id: Telegram chat ID to send messages to
        """
        self.token = token or os.getenv('TG_BOT_TOKEN') or TG_BOT_TOKEN
        self.chat_id = chat_id or os.getenv('TG_CHAT_ID') or TG_CHAT_ID

        if self.token and self.chat_id:
            self.bot = telebot.TeleBot(self.token)
            logger.info("Telegram bot initialized successfully")
        else:
            self.bot = None
            logger.warning("Telegram Token or Chat ID not provided. Bot functionality disabled.")

    def send_message(self, message: str) -> None:
        """
        Send a message to the configured Telegram chat.

        Args:
            message: Message to send (supports Markdown formatting)
        """
        if not self.bot or not self.chat_id:
            logger.warning("Bot or Chat ID missing. Skipping message.")
            print(f"DEBUG: Would send Telegram message:\n{message}")
            return

        try:
            self.bot.send_message(self.chat_id, message, parse_mode='Markdown')
            logger.info("Telegram message sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def send_order_block_alert(self, symbol: str, order_block: Any, current_price: float) -> None:
        """
        Send an alert when an Order Block is tapped.

        Args:
            symbol: Stock symbol
            order_block: OrderBlock object that was tapped
            current_price: Current market price
        """
        message = self._format_order_block_message(symbol, order_block, current_price)
        self.send_message(message)

    def send_swing_scan_results(self, results: Dict[str, Any]) -> None:
        """
        Send swing scan results summary.

        Args:
            results: Swing scan results dictionary
        """
        message = self._format_swing_scan_message(results)
        self.send_message(message)

    def send_scanner_notification(self, message: str) -> None:
        """
        Send a general scanner notification.

        Args:
            message: Notification message
        """
        self.send_message(f"📊 *Scanner Notification*\n\n{message}")

    def _format_order_block_message(self, symbol: str, order_block: Any, current_price: float) -> str:
        """
        Format an Order Block alert message.

        Args:
            symbol: Stock symbol
            order_block: OrderBlock object
            current_price: Current market price

        Returns:
            str: Formatted message
        """
        ob_type = order_block.block_type
        zone_high = order_block.high
        zone_low = order_block.low
        strength = order_block.strength
        entry_time = order_block.entry_time.strftime('%Y-%m-%d')

        # Determine alert type and emoji
        if ob_type == 'BULLISH_OB':
            emoji = "🟢"
            alert_type = "Demand Zone Tapped"
            direction = "Potential Bounce Up"
        else:
            emoji = "🔴"
            alert_type = "Supply Zone Tapped"
            direction = "Potential Drop Down"

        message = (
            f"{emoji} *ORDER BLOCK ALERT*\n\n"
            f"📈 *{symbol}*\n"
            f"💰 Current Price: ₹{current_price:.2f}\n\n"
            f"🎯 *{alert_type}*\n"
            f"📊 Zone: ₹{zone_low:.2f} - ₹{zone_high:.2f}\n"
            f"💪 Strength: {strength}/5\n"
            f"📅 Formed: {entry_time}\n\n"
            f"🎲 *Expected Move:*\n{direction}\n\n"
            f"[View Chart](https://in.tradingview.com/chart/?symbol=NSE:{symbol})"
        )

        return message

    def _format_swing_scan_message(self, results: Dict[str, Any]) -> str:
        """
        Format swing scan results message.

        Args:
            results: Swing scan results dictionary

        Returns:
            str: Formatted message
        """
        scan_date = results.get('scan_date', 'N/A')
        total_scanned = results.get('total_symbols_scanned', 0)
        qualifying = results.get('qualifying_stocks', 0)
        success_rate = results.get('success_rate', 0)

        message = (
            f"📊 *Swing Scan Complete*\n\n"
            f"📅 Date: {scan_date}\n"
            f"🔍 Symbols Scanned: {total_scanned}\n"
            f"✅ Qualifying Stocks: {qualifying}\n"
            f"📈 Success Rate: {success_rate:.1f}%\n\n"
        )

        # Add top qualifying stocks if any
        if qualifying > 0 and 'results' in results:
            message += "*Top Results:*\n"
            for i, stock in enumerate(results['results'][:5]):  # Show top 5
                symbol = stock.get('symbol', 'N/A')
                price = stock.get('close_price', 0)
                ret = stock.get('daily_return_pct', 0)
                message += f"{i+1}. {symbol}: ₹{price:.2f} ({ret:+.1f}%)\n"

        return message

    def test_connection(self) -> bool:
        """
        Test the Telegram bot connection.

        Returns:
            bool: True if connection is working
        """
        if not self.bot or not self.chat_id:
            logger.warning("Bot not configured for testing")
            return False

        try:
            test_message = "🤖 *Bot Test*\n\nConnection test successful!"
            self.send_message(test_message)
            return True
        except Exception as e:
            logger.error(f"Bot connection test failed: {e}")
            return False