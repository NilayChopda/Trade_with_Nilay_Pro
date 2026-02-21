
import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

# Setup paths
base_dir = Path(__file__).resolve().parent
env_path = base_dir / "backend" / "config" / "keys.env"
load_dotenv(env_path)

def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print(f"Using Token: {token[:10]}...")
    print(f"Using Chat ID: {chat_id}")
    
    if not token or not chat_id:
        print("Error: Missing token or chat_id in keys.env")
        return

    message = "🚀 *Antigravity System Online*\nTelegram integration verified with new API keys.\nReady for trade alerts!"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        if response.status_code == 200:
            print("✅ Telegram Message Sent Successfully!")
        else:
            print("❌ Failed to send Telegram message.")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_telegram()
