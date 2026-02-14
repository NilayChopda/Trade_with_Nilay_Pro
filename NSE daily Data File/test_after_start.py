import requests
import time

BOT_TOKEN = "8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs"

print("🔍 Waiting for you to start chat with bot...")
print("1. Open Telegram")
print("2. Find: @Nilay_Swing_Scanner_bot")
print("3. Click START or send /start")
print("4. Wait 10 seconds")
print("\n⏳ I'll wait 30 seconds for you...")

time.sleep(30)  # Wait 30 seconds for you to start chat

print("\n🎯 Testing after you started chat...")

# Now try sending
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": "810052560",  # Your ID
    "text": "🎉 CONGRATULATIONS! Your NSE Scanner Bot is WORKING!\n\nNow we can build the complete system!\n\n✅ Next: Scanner logic\n✅ Next: Real stock data\n✅ Next: Daily alerts",
    "parse_mode": "HTML"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Bot can now send you messages!")
        print("🎯 Telegram connection is READY for Feb 6th!")
    else:
        print(f"❌ Still failing: {response.text}")
        print("👉 Make sure you clicked START on the bot!")
        
except Exception as e:
    print(f"❌ Error: {e}")