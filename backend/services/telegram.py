import os
import logging
import requests
from dotenv import load_dotenv
from pathlib import Path
from ..database.db import get_conn

load_dotenv(Path(__file__).resolve().parent.parent / "config" / "keys.env")

LOG = logging.getLogger("twn.telegram")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_API") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        LOG.warning("Telegram bot not configured; skipping message: %s", text)
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        LOG.exception("Failed to send telegram message: %s", e)
        return False


def percent_change_from_prev(symbol: str):
    """Return percent change between latest close and previous close, and latest volume.
    If insufficient data, return (None, None).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT close, ts FROM minute_data WHERE symbol=? ORDER BY ts DESC LIMIT 2",
            (symbol,)
        )
        rows = cur.fetchall()
        if len(rows) < 2:
            return None, None
        latest_close, latest_ts = rows[0]
        prev_close, prev_ts = rows[1]
        try:
            pct = (latest_close - prev_close) / prev_close * 100.0 if prev_close and prev_close != 0 else None
        except Exception:
            pct = None
        # fetch latest volume
        cur.execute("SELECT volume FROM minute_data WHERE symbol=? AND ts=?", (symbol, latest_ts))
        vol_row = cur.fetchone()
        volume = vol_row[0] if vol_row else None
        return pct, volume
    finally:
        conn.close()


def alert_if_in_range(symbol: str, low: float = 0.0, high: float = 3.0):
    pct, volume = percent_change_from_prev(symbol)
    if pct is None:
        return False
    if pct >= low and pct <= high:
        msg = f"{symbol} | {pct:.2f}% | vol={volume}"
        send_message(msg)
        return True
    return False


if __name__ == "__main__":
    # quick manual test (requires DB and symbols)
    print(percent_change_from_prev("TCS.NS"))