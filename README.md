
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
-   **Data Sources**: NSE Unofficial APIs, Kite API (no Yahoo/YFinance required)

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

#### 📦 Environment variables
Add the following settings (via Render dashboard or `.env`) to control filtering and pattern scanning:

You can also adjust filters live from the dashboard using the checkboxes above the
main table.  Select any combination of patterns (Consolidation, VCP, Order Block,
Breakout, etc.) and click **Apply** – the server will re‑run the scan with those
patterns and display only matching stocks.


- `MIN_PRICE` – minimum stock price to include (default `100`).
- `MAX_PRICE` – maximum price; leave blank or large number for "no limit".
- `MIN_CHANGE` – minimum percent move (default `0`).
- `MAX_CHANGE` – maximum percent move (default `20`).
- `SCAN_PATTERNS` – comma‑separated list of pattern codes to scan for. Defaults to
  `CONSOLIDATION,VCP,ORDER_BLOCK,BREAKOUT` but you can add `IPO_BASE`,
  `ROCKET_BASE`, etc.
- `ALERT_PCT` – send extra Telegram alerts for any symbol whose price change is
  greater than or equal to this percentage (default `5.0`). Useful for
  tagging large breakouts even if they fall outside the regular filter.

The application will automatically label results with the detected pattern and
any recognised candlestick (bullish engulfing, hammer, doji, etc.).
4.  Ensure a Persistent Disk is attached at `/data` if `DATABASE_URL` is configured to point there.

---

## ⚙️ Configuration (Environment Variables)

-   `KITE_API_KEY`: `927xjtvndq82vjc3`
-   `TELEGRAM_BOT_TOKEN`: `8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs`
-   `TELEGRAM_CHAT_ID`: `810052560`
-   `TRADINGVIEW_BASE` *(optional)*: link template for chart previews. use `{symbol}` placeholder, e.g. `https://in.tradingview.com/symbols/NSE-{symbol}/`.

---

## 🛡 License
Private and Confidential. (c) 2026 Nilay Chopda.
