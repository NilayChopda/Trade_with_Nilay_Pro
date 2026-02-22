
import logging
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_provider import DataProvider
from indicators import get_technical_summary, calculate_wma, calculate_rsi
from database import get_db, save_dashboard_cache, log_alert, is_already_alerted
from telegram_bot import send_telegram_alert

# Institutional Logic Imports
from backend.strategy.smc import SMCEngine
from backend.strategy.pattern_detector import PatternDetector
from backend.scanner.chartink_scanner import ChartinkScanner

logger = logging.getLogger(__name__)

class MarketScanner:
    def __init__(self):
        self.data_provider = DataProvider()
        self.symbols_equity = self._load_symbols()
        # F&O filtered subset (Top 200 most liquid)
        self.symbols_fno = self.symbols_equity[:200] if len(self.symbols_equity) > 200 else self.symbols_equity
        
        # Institutional Engines
        self.smc_engine = SMCEngine()
        self.pattern_detector = PatternDetector()
        self.is_scanning = False
        
        # Chartink Scanners
        self.chartink_scanners = [
            ChartinkScanner("https://chartink.com/screener/nilay-swing-pick-algo", "Swing Pick Algo"),
            ChartinkScanner("https://chartink.com/screener/nilay-swing-pick-2-0", "Swing Pick 2.0"),
            ChartinkScanner("https://chartink.com/screener/nilay-fno-autopick-scanner", "FnO Autopick")
        ]

    def _load_symbols(self):
        """Loads all 2600+ NSE symbols for broad market coverage."""
        try:
            # 1. Try to get all listed stocks from NSE directly
            symbols = self.data_provider.get_all_nse_symbols()
            if symbols and len(symbols) > 500:
                logger.info(f"Loaded {len(symbols)} symbols from NSE.")
                return symbols
                
            # 2. Fallback to local data
            path = Path(__file__).parent / "data" / "symbols.json"
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Broad symbol load failed: {e}")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "AXISBANK", "SBIN", "BHARTIARTL"]

    def check_swing_criteria(self, symbol, override_df=None):
        """Standard Nilay Swing Pick Logic."""
        try:
            if override_df is not None:
                df = override_df
            else:
                df = self.data_provider.get_historical_data(symbol, period="1y")
            
            if df.empty or len(df) < 50: return None
            
            # Simple EMA + RSI + Pattern logic
            df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Criteria: Above EMA 20/50 + Bullish Change (0-4%)
            if curr['Close'] > curr['ema20'] and curr['Close'] > curr['ema50']:
                change = ((curr['Close'] - prev['Close'])/prev['Close'])*100
                if 0 <= change <= 4.0:
                    summary = get_technical_summary(df)
                    return {
                        "symbol": symbol,
                        "price": round(float(curr['Close']), 2),
                        "change_pct": round(float(change), 2),
                        "volume": int(curr['Volume']),
                        "patterns": " | ".join(summary['patterns']),
                        "indicators": " | ".join(summary['signals']),
                        "scan_type": "swing"
                    }
        except Exception as e:
            logger.error(f"Swing check failed for {symbol}: {e}")
            return None
        return None

    def check_smc_criteria(self, symbol, override_df=None):
        """Institutional Order Block check."""
        try:
            if override_df is not None:
                df = override_df
            else:
                df = self.data_provider.get_historical_data(symbol, period="6mo")
            
            if df.empty or len(df) < 50: return None
            
            df.columns = [c.lower() for c in df.columns]
            df['timestamp'] = df.index
            
            setup = self.smc_engine.check_setup(df)
            if setup and setup['score'] >= 7:
                close = df['close'].iloc[-1]
                prev_close = df['close'].iloc[-2]
                change = ((close - prev_close)/prev_close)*100
                return {
                    "symbol": symbol,
                    "price": round(float(close), 2),
                    "change_pct": round(float(change), 2),
                    "volume": int(df['volume'].iloc[-1]),
                    "patterns": f"SMC: {setup['signal']}",
                    "indicators": " | ".join(setup['reasons']),
                    "scan_type": "smc"
                }
        except: return None
        return None

    def run_scan(self):
        """High-speed parallel scan across 2600+ stocks."""
        if self.is_scanning:
            logger.warning("Scan already in progress...")
            return []
            
        self.is_scanning = True
        logger.info(f"Starting lightning scan for {len(self.symbols_equity)} stocks...")
        results = []
        
        def process_symbol(symbol):
            symbol_results = []
            # 1. SMC Order Blocks
            try:
                smc = self.check_smc_criteria(symbol)
                if smc: symbol_results.append(smc)
            except: pass
            
            # 2. Swing Pick
            try:
                swing = self.check_swing_criteria(symbol)
                if swing: symbol_results.append(swing)
            except: pass
            
            return symbol_results

        try:
            # Parallel internal scanning (50 threads)
            with ThreadPoolExecutor(max_workers=50) as executor:
                # 1. Internal logic
                future_to_sym = {executor.submit(process_symbol, sym): sym for sym in self.symbols_equity}
                
                # 2. Chartink logic
                future_to_chartink = {executor.submit(c.fetch_results): c.scanner_name for c in self.chartink_scanners}
                
                for future in as_completed(future_to_sym):
                    res_list = future.result()
                    if res_list: results.extend(res_list)
                
                for future in as_completed(future_to_chartink):
                    c_name = future_to_chartink[future]
                    c_stocks = future.result()
                    for s in (c_stocks or []):
                        results.append({
                            "symbol": s['symbol'],
                            "price": s['price'],
                            "change_pct": s['change_pct'],
                            "volume": s.get('volume', 0),
                            "patterns": f"Chartink: {c_name}",
                            "indicators": "Live Institutional Alert",
                            "scan_type": "chartink"
                        })

            # Filter for 0-4% range for Dashboard
            dashboard_results = []
            seen = set()
            for r in results:
                if r['symbol'] not in seen and 0 <= r.get('change_pct', 0) <= 4.0:
                    dashboard_results.append(r)
                    seen.add(r['symbol'])
            
            save_dashboard_cache(dashboard_results)
            
            # Immediate Telegram Alerts
            for r in dashboard_results:
                if not is_already_alerted(r['symbol']):
                    alert_msg = f"🚀 *{r['symbol']}* ({r['change_pct']:+.2f}%)\nPrice: ₹{r['price']}\nPatterns: {r['patterns']}"
                    if send_telegram_alert(alert_msg):
                        log_alert(r['symbol'], r['price'], r['change_pct'], r['scan_type'], alert_msg)
            
            return dashboard_results
        except Exception as e:
            logger.error(f"Global lightning scan failed: {e}")
            return []
        finally:
            self.is_scanning = False

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_scan()
