
import os
import requests
import logging

logger = logging.getLogger(__name__)

# Provided by USER
TELEGRAM_BOT_TOKEN = "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs"
TELEGRAM_CHAT_ID = "810052560"

def send_telegram_alert(message):
    """Sends a formatted message to the Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully.")
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False

if __name__ == "__main__":
    send_telegram_alert("🚀 *Trade with Nilay* Bot Started Successfully!")
