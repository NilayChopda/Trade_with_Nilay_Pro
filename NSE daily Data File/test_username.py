import requests
from datetime import datetime

BOT_TOKEN = "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs"

# Try sending to your username
targets = [
    "@nilaychopda",        # Your username
    "nilaychopda",         # Without @
    "810052560",           # Your ID (after you start chat)
]

print("🤖 Testing Telegram delivery...")

for target in targets:
    print(f"\n📨 Sending to: {target}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target,
        "text": f"🔔 Test from NSE Scanner Bot\nTarget: {target}\nTime: {datetime.now().strftime('%H:%M:%S')}\n\n👉 Please send /start to @Nilay_Swing_Scanner_bot",
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Message sent to {target}")
            break
        else:
            print(f"❌ Failed. Need to start chat with bot first.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🔑 SOLUTION: Go to Telegram, find @Nilay_Swing_Scanner_bot, send /start")