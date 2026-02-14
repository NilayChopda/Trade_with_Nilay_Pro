import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
import yfinance as yf
from ..database.db import init_db, insert_minute, bulk_insert
from ..services.telegram import alert_if_in_range

load_dotenv(Path(__file__).resolve().parent.parent / "config" / "keys.env")

ROOT = Path(__file__).resolve().parent.parent
SYMBOLS_FILE = ROOT / "database" / "symbols.txt"

logger = logging.getLogger("twn.fetcher")


def load_symbols():
    if SYMBOLS_FILE.exists():
        with open(SYMBOLS_FILE, "r", encoding="utf-8") as f:
            syms = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return syms
    # fallback small set for first-run testing
    return ["TCS.NS", "INFY.NS"]


class YahooFetcher:
    """Simple pluggable connector using yfinance. For production add exchange-specific connectors."""

    def __init__(self, batch_size=50):
        init_db()
        self.batch_size = batch_size

    def fetch_latest_for(self, symbol: str):
        try:
            # yfinance ticker with Indian suffix .NS for NSE
            df = yf.download(tickers=symbol, period="1d", interval="1m", progress=False)
            if df.empty:
                return None
            # keep last row
            row = df.iloc[-1]
            ts = int(pd.Timestamp(row.name).timestamp())
            return (symbol, ts, float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"]), float(row["Volume"]))
        except Exception as e:
            logger.exception("fetch error %s %s", symbol, e)
            return None

    def fetch_all(self, symbols):
        rows = []
        for symbol in symbols:
            r = self.fetch_latest_for(symbol)
            if r:
                rows.append(r)
            time.sleep(0.1)
        if rows:
            bulk_insert(rows)
        return len(rows)


def run_once():
    fetcher = YahooFetcher()
    syms = load_symbols()
    logger.info("Starting fetch cycle for %d symbols", len(syms))
    count = fetcher.fetch_all(syms)
    logger.info("Inserted/updated %d rows", count)
    # basic alert: check recent percent change and notify if within 0%% - 3%%
    try:
        for s in syms:
            try:
                alerted = alert_if_in_range(s, low=0.0, high=3.0)
                if alerted:
                    logger.info("Alert sent for %s", s)
            except Exception:
                logger.exception("Error checking alert for %s", s)
    except Exception:
        logger.exception("Error running alerts loop")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_once()