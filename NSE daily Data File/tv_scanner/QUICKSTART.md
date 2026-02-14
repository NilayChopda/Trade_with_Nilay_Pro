# Quick Start Guide

## ✅ What You Have
- **2,774 NSE Stock Symbols** loaded from `symbols.txt`
- **Scanner Logic**: 7 WMA conditions + Post Filter (-1% to +2%)
- **Telegram Bot** (when configured)
- **Web Dashboard** (Streamlit)
- **GitHub Actions** ready for cloud automation

## 🚀 Run Locally (Windows)

### Option 1: Double-Click Batch Files
1. **Run Scanner**: Double-click `run_scanner.bat`
2. **View Dashboard**: Double-click `run_dashboard.bat`

### Option 2: Command Line
```cmd
cd "g:\My Drive\Trade_with_Nilay\NSE daily Data File\tv_scanner"
python main.py
```

## ⚙️ Configure Telegram (Optional)
1. Get your Bot Token from @BotFather on Telegram
2. Get your Chat ID from @userinfobot
3. Set environment variables:
   - Windows (PowerShell): `$env:TG_BOT_TOKEN="your_token"`
   - Or edit `run_scanner.bat` to uncomment and set the variables

## 📊 View Results
- **CSV**: Open `results.csv` in Excel
- **Dashboard**: Run `streamlit run dashboard.py` and open http://localhost:8501

## 🔧 Current Status
⚠️ **Using Mock Data** - The scanner runs but generates random test data because:
- `tvdatafeed` library requires `git` to be installed
- This allows you to test the logic flow

## 🌐 Deploy to Cloud (GitHub Actions)
1. Install Git: https://git-scm.com/download/win
2. Initialize repo: `git init`
3. Push to GitHub
4. Add Secrets in GitHub Settings
5. The workflow in `.github/workflows/scanner.yml` will run automatically

## 📁 Files
- `main.py` - Main scanner script
- `scanner.py` - Core scanning engine
- `core/indicators.py` - WMA calculation logic
- `bot/telegram_bot.py` - Telegram integration
- `dashboard.py` - Web UI
- `symbols.txt` - Your 2774 NSE stocks
- `results.csv` - Output file
