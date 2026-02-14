import telebot
import os
import logging
from typing import Optional, List
import time

logger = logging.getLogger(__name__)

class ScannerBot:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.getenv('TG_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TG_CHAT_ID')
        
        if self.token:
            self.bot = telebot.TeleBot(self.token)
            logger.info(f"Telegram Bot initialized. Chat ID: {self.chat_id}")
        else:
            self.bot = None
            logger.warning("Telegram Token not provided. Bot functionality disabled.")
        
        # Rate limiting to avoid spam
        self.last_alert_time = {}
        self.alert_cooldown = 60  # 1 minute between same symbol alerts

    def send_message(self, message: str, silent: bool = False):
        """Send message to Telegram with error handling"""
        if not self.bot or not self.chat_id:
            logger.warning("Bot or Chat ID missing. Would send:\n" + message)
            return False

        try:
            self.bot.send_message(
                self.chat_id, 
                message, 
                parse_mode='HTML',
                disable_notification=silent
            )
            logger.debug(f"Message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def send_results(self, results_df):
        if results_df is None or results_df.empty:
            self.send_message("✅ Scanner Run Complete. No stocks found matching criteria.")
            return

        for _, row in results_df.iterrows():
            msg = self.format_stock_message(row)
            self.send_message(msg)
            time.sleep(0.5)  # Avoid rate limiting
    
    def send_signal_alert(self, symbol: str, signal_data: dict, **kwargs):
        """
        Send real-time signal alert
        Used for immediate notifications when signal is detected
        """
        # Check cooldown
        current_time = time.time()
        if symbol in self.last_alert_time:
            if current_time - self.last_alert_time[symbol] < self.alert_cooldown:
                logger.debug(f"Signal alert for {symbol} on cooldown")
                return False
        
        self.last_alert_time[symbol] = current_time
        
        msg = self.format_signal_alert(symbol, signal_data, **kwargs)
        return self.send_message(msg)
    
    def format_signal_alert(self, symbol: str, signal_data: dict, **kwargs) -> str:
        """Format signal alert message"""
        try:
            ltp = signal_data.get('current_ltp', signal_data.get('close', 0))
            close = signal_data.get('close', 0)
            ob_low = signal_data.get('ob_low', 0)
            ob_high = signal_data.get('ob_high', 0)
            volume = signal_data.get('live_volume', signal_data.get('volume', 0))
            
            # Calculate risk/reward
            if ob_low > 0 and ltp > ob_low:
                risk = ltp - ob_low
                target = ltp + (risk * 2)  # 2R
            else:
                risk = 0
                target = 0
            
            message = (
                f"🎯 <b>SIGNAL DETECTED!</b>\n\n"
                f"<b>Stock:</b> {symbol}\n"
                f"💰 <b>LTP:</b> ₹{ltp:.2f}\n"
                f"📊 <b>Close:</b> ₹{close:.2f}\n"
                f"📈 <b>Volume:</b> {volume:,.0f}\n\n"
                f"<b>OB ZONE:</b>\n"
                f"🔲 Low: ₹{ob_low:.2f}\n"
                f"🔲 High: ₹{ob_high:.2f}\n\n"
                f"<b>R:R SETUP:</b>\n"
                f"🎯 Risk: ₹{risk:.2f}\n"
                f"🎯 Target (2R): ₹{target:.2f}\n"
                f"⏱️ SL: ₹{ob_low:.2f}\n\n"
                f"⚡ Time: {time.strftime('%H:%M:%S')}"
            )
            return message
        except Exception as e:
            logger.error(f"Error formatting signal alert: {e}")
            return f"🎯 Signal: {symbol} | LTP: ₹{signal_data.get('close', 0):.2f}"
            
    def format_stock_message(self, row):
        """
        Formats the message as per user requirement:
        Stock Name, CMP, Percent Change, Volume, All WMA values
        """
        symbol = row.get('symbol', 'UNKNOWN')
        cmp_price = row.get('close', 0)
        pct = row.get('pct_change', 0)
        vol = row.get('volume', 0)
        
        # WMA Values
        d_wma1 = row.get('d_wma1', 0)
        m_wma2 = row.get('m_wma2', 0)
        
        msg = (
            f"*{symbol}*\n"
            f"CMP: {cmp_price:.2f}\n"
            f"Change: {pct:.2f}%\n"
            f"Volume: {vol}\n\n"
            f"*Logic Values:*\n"
            f"Daily WMA(1): {d_wma1:.2f}\n"
            f"Monthly WMA(2): {m_wma2:.2f}\n"
            f"[TradingView Chart](https://in.tradingview.com/chart/?symbol=NSE:{symbol})"
        )
        return msg
