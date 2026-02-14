# Trade With Nilay - Professional Trading Platform

![Status](https://img.shields.io/badge/status-active-success.svg)
![Version](https://img.shields.io/badge/version-2.0-blue.svg)

Professional Indian equity quantitative analysis system with real-time scanning, AI analysis, and pattern detection.

## 🚀 Features

- **Real-Time Stock Scanning** - Chartink integration with 5-minute auto-refresh
- **AI Technical Analysis** - Intelligent scoring and pattern recognition
- **Pattern Detection** - Breakout, Order Block, Support/Resistance, Consolidation
- **Telegram Alerts** - Real-time notifications for 0-3% setups
- **FnO Analysis** - Dedicated F&O stock scanner with live prices
- **Mobile PWA** - Install on phone like a native app

## 📱 Access

**Live Dashboard:** [https://trade-with-nilay.streamlit.app](https://trade-with-nilay.streamlit.app)

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- Chrome/Chromium (for Selenium)
- Node.js (for mobile tunneling)

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run frontend/app.py
```

### 24/7 Background Mode
```batch
# Windows
start_all_24x7.bat

# This starts:
# - Scanner Engine (Chartink scraping)
# - Alert Monitor (Telegram notifications)
# - Dashboard (Web interface)
```

## 📊 Architecture

```
Trade_with_Nilay/
├── backend/
│   ├── scanner/          # Chartink integration
│   ├── services/         # Alert monitor, Telegram
│   ├── strategy/         # Pattern detection
│   └── database/         # SQLite data layer
├── frontend/
│   ├── app.py           # Streamlit dashboard
│   └── static/          # PWA assets
└── .streamlit/          # Cloud config
```

## 🔐 Environment Variables

Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 📈 Deployment

### Streamlit Cloud (Recommended)
1. Push to GitHub
2. Connect at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Add secrets in dashboard
4. Deploy!

### Railway.app
```bash
railway login
railway init
railway up
```

## 🤝 Contributing

This is a personal trading tool. For suggestions, contact via Telegram.

## 📄 License

Private - All Rights Reserved

---

**Built with ❤️ for Indian Stock Market Traders**
