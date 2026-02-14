# 🚀 Trade With Nilay - Quick Reference Card

## ⚡ Quick Commands (v1.3)

### 1. Start the Scanner (Signals)
```powershell
# Runs Chartink Scanners + AI Scorer + Telegram Alerts
.\run_scanner.bat
```

### 2. Start the Website (Local Dashboard)
```powershell
# Runs Nilay's Scanner & Analytics Dashboard
.\run_dashboard.bat
```

### 3. Professional 24/7 Deployment (Docker)
```powershell
# Runs EVERYTHING in the background + Public Access
# This ensures latest code is active and runs 24/7
.\deploy_24x7.bat
```

### 4. Manual Dashboard (One-time)
```powershell
.\run_dashboard.bat
```

---

## 📊 Phase 7 System Status: ✅ COMPLETE

| Component | Status | Feature |
|-----------|--------|---------|
| **Chartink Scanners** | ✅ Active | Triple scanner monitoring |
| **Breakout Engine** | ✅ Active | 20-Day High + Volume detection |
| **AI Technical Scorer**| ✅ Active | 0-10 Score + English Explanation |
| **Pro Dashboard** | ✅ Ready | TradingView charts + Auto-refresh |
| **Telegram Alerts** | ✅ Live | Professional Signal Formatting |
| **Auto-Recovery** | ✅ Ready | Docker-compose auto-restart |

---

## 🕒 Workflow Schedule

| Task | Time | Frequency |
|------|------|-----------|
| **Market Scanner** | 9:15 AM - 3:30 PM | Every 5 minutes (Real-time) |
| **AI Analysis** | On-Demand | Immediate on new signal |
| **Dashboard Refresh** | Live | Every 1-5 minutes |
| **EOD Reports** | 3:35 PM | Daily Recap |

---

## 📁 Critical Files & Paths

- `backend/scanner/scanner_engine.py` : Core Signal Logic
- `backend/strategy/breakout.py` : Custom Breakout Logic
- `frontend/app.py` : Dashboard Code
- `backend/database/trade_with_nilay.db` : Your Live Data

---

## 🔧 Troubleshooting (Website Errors)

- **"ModuleNotFoundError"**: Run `pip install -r requirements.txt`
- **"DatabaseError"**: Ensure you have run the scanner at least once to populate data.
- **Charts not loading?**: Check your internet connection for TradingView scripts.

---

**🚀 System is stable and ready for live trading!**
