# NSE Scanner KITE Integration - Setup Guide

## Overview

This guide explains how to set up the NSE scanner to use **Zerodha KITE API** for real-time prices instead of Yahoo Finance.

### Key Improvements
- ✅ **Real-time Prices**: Live prices from Zerodha (official NSE data)
- ✅ **All 2700+ Symbols**: Scans complete NSE universe, not just top 50
- ✅ **Telegram Alerts**: Instant Telegram notifications for each signal
- ✅ **Higher Accuracy**: Direct market data vs. delayed web scraping

---

## Step 1: Get Zerodha KITE API Credentials

### Option A: Using Zerodha Console (Recommended)

1. Go to https://console.zerodha.com
2. Log in with your Zerodha account
3. Navigate to **API Console** → **My Apps**
4. Click **Create New App**
5. Fill in details:
   - **App Name**: NSE Scanner
   - **Description**: Real-time NSE scanner
   - **Redirect URL**: `http://localhost:8080`
   - **Permissions**: Check "Read" and "Basket Orders"

6. You'll get:
   - **API Key**: Keep this safe
   - **API Secret**: Keep this very safe

### Getting Access Token

After creating the app:

1. Go to https://kite.zerodha.com/connect/{API_KEY}
2. Log in with your trading credentials
3. Authorize the app
4. You'll be redirected with `request_token` in URL
5. Use this to generate `access_token` (valid for 24 hours)

---

## Step 2: Install Required Libraries

```bash
# Install KITE API library
pip install kiteconnect

# Install Telegram bot
pip install pyTelegramBotAPI

# Other dependencies
pip install pandas numpy
```

---

## Step 3: Configure Environment Variables

### Create `.env` file in `tv_scanner` directory:

```bash
# Zerodha KITE API Credentials
KITE_API_KEY=your_api_key_here
KITE_ACCESS_TOKEN=your_access_token_here

# Telegram Bot Configuration
TG_BOT_TOKEN=your_telegram_bot_token
TG_CHAT_ID=your_telegram_chat_id
```

### Or set as system environment variables:

**Windows (PowerShell):**
```powershell
$env:KITE_API_KEY = "your_api_key_here"
$env:KITE_ACCESS_TOKEN = "your_access_token_here"
$env:TG_BOT_TOKEN = "your_telegram_bot_token"
$env:TG_CHAT_ID = "your_telegram_chat_id"
```

**Linux/Mac (Terminal):**
```bash
export KITE_API_KEY="your_api_key_here"
export KITE_ACCESS_TOKEN="your_access_token_here"
export TG_BOT_TOKEN="your_telegram_bot_token"
export TG_CHAT_ID="your_telegram_chat_id"
```

---

## Step 4: Get Telegram Bot Token & Chat ID

### Create Telegram Bot

1. Open Telegram
2. Search for **@BotFather**
3. Click Start
4. Send `/newbot`
5. Enter bot name and username
6. You'll get: **API Token**
7. Copy and save the token

### Get Your Chat ID

1. Search for **@userinfobot** in Telegram
2. Click Start
3. Your Chat ID will be displayed
4. Save this ID

---

## Step 5: Run the Scanner

### Scan All NSE Securities (2700+)

```bash
python main_kite.py --all
```

### Scan with Limit (for testing)

```bash
python main_kite.py --all --limit 100
```

### Scan Specific Symbols

```bash
python main_kite.py --symbols INFY TCS WIPRO RELIANCE
```

---

## File Structure

```
tv_scanner/
├── core/
│   └── kite_fetcher.py          # KITE API data fetcher
├── scanner_kite_enhanced.py     # Enhanced scanner for KITE
├── main_kite.py                 # Main entry point
├── bot/
│   └── telegram_bot.py          # Updated Telegram bot
├── .env                         # Configuration file (not in git)
└── scanner_kite.log            # Logs
```

---

## Key Features

### 1. Real-time Price Updates

```python
# Fetch live prices
from core.kite_fetcher import KITEDataFetcher

fetcher = KITEDataFetcher(api_key, access_token)
prices = fetcher.fetch_ltp(['INFY', 'TCS'])
# {'INFY': {'ltp': 1500.5, 'bid': 1500.0, 'ask': 1501.0, ...}}
```

### 2. All NSE Securities

```python
# Get all 2700+ symbols
symbols = fetcher.get_all_nse_symbols()
# Returns: ['INFY', 'TCS', 'WIPRO', ..., (2700+ total)]
```

### 3. Historical Data

```python
# Fetch 50 days of OHLC
df = fetcher.fetch_daily_ohlc('INFY', days=50)
# Returns: DataFrame with OHLC data
```

### 4. Real-time Telegram Alerts

```python
# Signal immediately alerts Telegram
Scanner detects signal → 
  ↓
Send to Telegram bot instantly →
  ↓
You get notification with:
  - Stock name & LTP
  - Current price
  - OB zones
  - Risk/Reward setup
```

---

## Important Notes

### Access Token Expiry

⚠️ **IMPORTANT**: KITE access tokens expire every 24 hours!

You need to regenerate daily:

```python
# Regenerate token daily
from kiteconnect import KiteConnect

kite = KiteConnect(api_key=api_key)
# Visit: https://kite.zerodha.com/connect/{api_key}
# Get new request_token
# Use it to generate new access_token
```

### Rate Limits

KITE API has rate limits:
- 100 requests per second
- Don't exceed this in scanner

Current scanner uses:
- 15 concurrent workers
- Minimal API calls per symbol
- Should handle 2700+ symbols in ~30 minutes

### Price Accuracy

- ✅ Real-time (within seconds of market)
- ✅ Official NSE data
- ✅ No delays like Yahoo Finance
- ✅ Accurate for live trading

---

## Troubleshooting

### Error: "KITE_API_KEY not found"
**Solution**: Check environment variables are set correctly
```bash
# Verify on Windows
Get-Item env:KITE_API_KEY
```

### Error: "Invalid access token"
**Solution**: Generate new access token (expires in 24 hours)

### Error: "Symbol not found"
**Solution**: Use exact NSE symbol format (e.g., "INFY", not "INFY.NS")

### No Telegram alerts
**Solution**: Check bot token and chat ID are correct

### Scan too slow
**Solution**: Increase max_workers (default: 15)
```bash
python main_kite.py --all  # Uses 15 workers by default
```

---

## Data Comparison

### Yahoo Finance (Old)
```
- Delayed (15-20 minutes)
- Incomplete data for small caps
- Limited symbols
- Unreliable for some stocks
- No volume data during market hours
```

### Zerodha KITE API (New)
```
✓ Real-time (live prices)
✓ All NSE symbols (2700+)
✓ Official market data
✓ Accurate volume & OI
✓ Best for intraday trading
```

---

## Example Output

When you run the scanner:

```
2026-01-29 10:30:45 - INFO - NSE SCANNER WITH KITE API - SCAN ALL SECURITIES
2026-01-29 10:30:45 - INFO - ✓ KITE API connection established
2026-01-29 10:30:45 - INFO - ✓ Scanner initialized
2026-01-29 10:30:45 - INFO - ✓ Telegram bot connected for real-time alerts
2026-01-29 10:30:50 - INFO - Fetching all NSE securities...
2026-01-29 10:30:55 - INFO - Fetched 2734 NSE securities
2026-01-29 10:30:55 - INFO - Starting scan for 2734 NSE securities...
2026-01-29 10:31:05 - INFO - Progress: 50/2734 | Signals found: 3
2026-01-29 10:31:15 - INFO - Progress: 100/2734 | Signals found: 5
...
2026-01-29 11:00:00 - INFO - Scan complete. Found 47 signals.

[Real-time Telegram alerts sent for each signal]

======================================================================
TOP 20 SIGNALS
======================================================================
  symbol  score  close  current_ltp  ob_low  ob_high    volume
0   INFY     14   1500    1500.5     1450    1550    1000000
1    TCS     12   3200    3205.0     3150    3250     500000
...
```

---

## Advanced Usage

### Schedule Daily Scans

**Create `run_scanner_daily.ps1`:**
```powershell
# Run scanner daily at market open
$time = [DateTime]::ParseExact("09:30", "HH:mm", $null)
while ($true) {
    $now = Get-Date
    if ($now.TimeOfDay -ge $time.TimeOfDay -and $now.DayOfWeek -ne "Saturday" -and $now.DayOfWeek -ne "Sunday") {
        python main_kite.py --all
        Start-Sleep -Seconds 86400  # Wait 24 hours
    }
    Start-Sleep -Seconds 60
}
```

### Custom Filters

```python
from scanner_kite_enhanced import KITEScannerEnhanced

scanner = KITEScannerEnhanced(fetcher)

# Scan only specific symbols
symbols = ['INFY', 'TCS', 'WIPRO', 'RELIANCE']
results = scanner.run_scan(symbols)

# Or scan all and filter
all_results = scanner.run_scan_all_nse()
high_volume = all_results[all_results['volume'] > 1000000]
```

---

## Support & Issues

### Check Logs

```bash
tail -f scanner_kite.log  # On Mac/Linux
Get-Content scanner_kite.log -Tail 50  # On Windows
```

### Test KITE Connection

```python
python -c "
from core.kite_fetcher import KITEDataFetcher
import os

api_key = os.getenv('KITE_API_KEY')
token = os.getenv('KITE_ACCESS_TOKEN')
fetcher = KITEDataFetcher(api_key, token)
symbols = fetcher.get_all_nse_symbols()
print(f'✓ Connected! Found {len(symbols)} NSE symbols')
"
```

---

## Next Steps

1. ✅ Set up environment variables
2. ✅ Get KITE API credentials
3. ✅ Set up Telegram bot
4. ✅ Run first scan: `python main_kite.py --all --limit 100`
5. ✅ Check Telegram for alerts
6. ✅ Schedule daily runs

---

**Happy Scanning! 🚀**

All prices are now LIVE from Zerodha KITE API
All 2700+ NSE securities are scanned
All signals alert you on Telegram instantly
