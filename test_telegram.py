
import os
import logging
from telegram_bot import send_telegram_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bot():
    print("Testing Telegram Bot Connection...")
    sample_msg = "🔔 *SYSTEM TEST* 🔔\n\nYour Trade with Nilay Terminal is LIVE!\nThis is a sample alert message from your deployment.\n\nHappy Trading! 🚀"
    success = send_telegram_alert(sample_msg)
    if success:
        print("✅ Telegram alert sent successfully!")
    else:
        print("❌ Failed to send Telegram alert. Check your Token/ChatID.")

if __name__ == "__main__":
    test_bot()
