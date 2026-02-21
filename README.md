
# 🚀 Trade With Nilay - Professional Stock Market Terminal

A production-ready quantitative analysis platform for the Indian stock market (NSE & BSE).

## 📡 Live URL: [Trade-with-nilay.com](http://Trade-with-nilay.com)

---

## 🛠 Features

-   **Scanner Engine**: Recreates "Nilay Swing Pick" and "FNO Autopick" logic using 7 technical criteria.
-   **Real-Time Dashboard**: Automatic updates every 5 minutes (Socket.IO).
-   **AI Reports**: Fundamental analysis and automated strategy insights.
-   **Telegram Alerts**: Instant notifications for stocks entering the 0% to +3% entry range.
-   **Announcements**: Centralized feed for NSE/BSE corporate filings.
-   **EOD Reports**: Automated daily performance summaries and archiving.

---

## 🏗 Technology Stack

-   **Backend**: Python / Flask / Flask-SocketIO
-   **Database**: SQLite (WAL Mode)
-   **Task Queue**: APScheduler
-   **Frontend**: Bootstrap 5 / Vanilla JS
-   **Data Sources**: yfinance, NSE Unofficial APIs, Kite API

---

## 📦 Local Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/nilaychopda/trade-with-nilay.git
    cd trade-with-nilay
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Initialize Database:
    ```bash
    python database.py
    ```

4.  Run Application:
    ```bash
    python app.py
    ```

---

## 🌐 Render Deployment (24/7)

1.  Connect this GitHub repository to [Render.com](https://render.com).
2.  Choose **Web Service**.
3.  Render will auto-detect `render.yaml` for configuration.
4.  Ensure a Persistent Disk is attached at `/data` if `DATABASE_URL` is configured to point there.

---

## ⚙️ Configuration (Environment Variables)

-   `KITE_API_KEY`: `927xjtvndq82vjc3`
-   `TELEGRAM_BOT_TOKEN`: `8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs`
-   `TELEGRAM_CHAT_ID`: `810052560`

---

## 🛡 License
Private and Confidential. (c) 2026 Nilay Chopda.
