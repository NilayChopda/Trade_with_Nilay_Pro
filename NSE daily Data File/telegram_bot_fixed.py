import requests
from datetime import datetime

BOT_TOKEN = "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs"

# Test different chat ID formats
chat_ids = [
    "810052560",       # Your ID
    "-100810052560",   # Group format
    "@810052560",      # Username format
]

print("Testing Telegram connection...")

for chat_id in chat_ids:
    print(f"\nTrying Chat ID: {chat_id}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🔔 Test from NSE Scanner\nChat ID: {chat_id}\nTime: {datetime.now().strftime('%H:%M:%S')}",
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response: {response.status_code} - {response.text[:100]}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS with Chat ID: {chat_id}")
            break
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🔍 Try this: Open Telegram, message @userinfobot, it will give your correct ID")