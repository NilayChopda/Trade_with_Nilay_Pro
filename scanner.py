
import os
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
        
        # Configurable price / change filters (environment override)
        self.min_price = float(os.getenv("MIN_PRICE", 100))
        self.max_price = float(os.getenv("MAX_PRICE", 1e9))
        self.min_change = float(os.getenv("MIN_CHANGE", 0))
        self.max_change = float(os.getenv("MAX_CHANGE", 20))
        # which pattern types to keep (comma separated)
        self.scan_patterns = [p.strip().upper() for p in os.getenv("SCAN_PATTERNS", "CONSOLIDATION,VCP,ORDER_BLOCK,BREAKOUT").split(",") if p.strip()]
        
        # Institutional Engines
        self.smc_engine = SMCEngine()
        self.pattern_detector = PatternDetector()
        self.is_scanning = False
        
        # Chartink Scanners (user can add/remove URLs)
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
        """High-speed parallel scan across 2600+ stocks.
        Uses pattern detector to focus on tight/consolidation/VCP type setups and
        supplements with Chartink scanners. Results include primary pattern and
        optional candlestick name for alerts/UI.
        """
        if self.is_scanning:
            logger.warning("Scan already in progress...")
            return []
            
        self.is_scanning = True
        logger.info(f"Starting lightning scan for {len(self.symbols_equity)} stocks...")
        results = []
        
        def process_symbol(symbol):
            # Analyze historical data for patterns
            try:
                df = self.data_provider.get_historical_data(symbol, period="1y")
                pdinfo = self.pattern_detector.analyze(df, symbol)

                # if no primary pattern or not in desired list, skip
                primary = pdinfo.get('primary_pattern')
                if not primary or primary.upper() not in self.scan_patterns:
                    return []

                # fetch live quote to get price/change/volume
                live = self.data_provider.fetch_nse_quote(symbol)
                if not live:
                    return []

                pat_label = primary
                primary_note = ''
                for p in pdinfo.get('patterns', []):
                    if p['type'] == primary and 'note' in p:
                        primary_note = p['note']
                        break

                if pdinfo.get('candlestick'):
                    pat_label += f" | {pdinfo['candlestick']}"

                badge_html = self.pattern_detector.get_pattern_badge(primary, pdinfo.get('confidence',0)) if primary else ''
                return [{
                    "symbol": symbol,
                    "price": round(float(live.get('price', 0)), 2),
                    "change_pct": round(float(live.get('change_pct', 0)), 2),
                    "volume": int(live.get('volume', 0)),
                    "patterns": pat_label,
                    "pattern_note": primary_note,
                    "pattern_badge": badge_html,
                    "target": pdinfo.get('target'),
                    "target_pct": pdinfo.get('target_pct'),
                    "indicators": " | ".join([p['type'] for p in pdinfo.get('patterns', [])]),
                    "scan_type": "pattern"
                }]
            except Exception as ex:
                logger.debug(f"Pattern check failed for {symbol}: {ex}")
                return []

        try:
            # Parallel internal scanning (50 threads)
            with ThreadPoolExecutor(max_workers=50) as executor:
                future_to_sym = {executor.submit(process_symbol, sym): sym for sym in self.symbols_equity}
                
                for future in as_completed(future_to_sym):
                    res_list = future.result()
                    if res_list: results.extend(res_list)

                # Chartink logic
                future_to_chartink = {executor.submit(c.fetch_results): c.scanner_name for c in self.chartink_scanners}
                
                for future in as_completed(future_to_chartink):
                    c_name = future_to_chartink[future]
                    c_stocks = future.result()
                    
                    # Determine scan type based on name
                    s_type = "swing"
                    if "fno" in c_name.lower():
                        s_type = "fno"
                    elif "vcp" in c_name.lower():
                        s_type = "vcp"
                    
                    for s in (c_stocks or []):
                        # run pattern detection on chartink result as well for extra context
                        pdinfo = self.pattern_detector.analyze(
                            self.data_provider.get_historical_data(s['symbol'], period="1y"),
                            s['symbol']
                        )
                        pat_label = f"Chartink: {c_name}"
                        if pdinfo.get('primary_pattern'):
                            pat_label += f" | {pdinfo['primary_pattern']}"
                        if pdinfo.get('candlestick'):
                            pat_label += f" | {pdinfo['candlestick']}"

                        badge_html = self.pattern_detector.get_pattern_badge(pdinfo.get('primary_pattern'), pdinfo.get('confidence',0)) if pdinfo.get('primary_pattern') else ''
                        note = ''
                        for p in pdinfo.get('patterns', []):
                            if p['type'] == pdinfo.get('primary_pattern') and 'note' in p:
                                note = p['note']
                                break
                        results.append({
                            "symbol": s['symbol'],
                            "price": s['price'],
                            "change_pct": s['change_pct'],
                            "volume": s.get('volume', 0),
                            "patterns": pat_label,
                            "pattern_note": note,
                            "pattern_badge": badge_html,
                            "target": pdinfo.get('target'),
                            "target_pct": pdinfo.get('target_pct'),
                            "indicators": "Live Institutional Alert",
                            "scan_type": s_type
                        })

            # Filter and cache results using configurable ranges
            dashboard_results = []
            seen = set()
            index_keywords = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'CNX', 'INDIA VIX', 'SENSEX']
            
            for r in results:
                symbol = r['symbol'].upper()
                if symbol in seen or any(k in symbol for k in index_keywords):
                    continue
                price = r.get('price', 0)
                ch = r.get('change_pct', 0)
                if not (self.min_price <= price <= self.max_price):
                    continue
                if not (self.min_change <= ch <= self.max_change):
                    continue
                dashboard_results.append(r)
                seen.add(symbol)

            # Sort by change % descending and pick top 30
            dashboard_results.sort(key=lambda x: x['change_pct'], reverse=True)
            dashboard_results = dashboard_results[:30]
            
            logger.info(f"Scan complete. Total raw: {len(results)}, Valid stocks: {len(dashboard_results)}")
            save_dashboard_cache(dashboard_results)

            # --- REFINED TELEGRAM ALERTS (User Condition: -1% to +3% + Candlestick) ---
            allowed_candles = ["Doji", "Hammer", "Bullish Engulfing", "Bullish Harami", "Inside Bar"]
            
            for r in results:
                ch = r.get('change_pct', 0)
                if -1.0 <= ch <= 3.0:
                    sym = r['symbol']
                    if not is_already_alerted(sym):
                        # Detect candle on last 5 days
                        df_hist = self.data_provider.get_historical_data(sym, period="5d")
                        pdinfo = self.pattern_detector.analyze(df_hist, sym)
                        candle = pdinfo.get('candlestick')
                        
                        if candle and candle in allowed_candles:
                            note = r.get('pattern_note') or ''
                            tv_link = os.getenv('TRADINGVIEW_BASE', '').strip()
                            tv_md = f"\n🔗 [Chart]({tv_link.format(symbol=sym)})" if tv_link else ''
                            
                            target_str = f"\n🎯 Target: ₹{r['target']} ({r['target_pct']:+.1f}%)" if r.get('target') else ''
                            msg = (
                                f"⭐ *PATTERN ALERT* {sym} {ch:+.2f}% – ₹{r.get('price')}\n"
                                f"Candle: *{candle}*\n"
                                f"Setup: {r.get('patterns','')}"
                                f"{(' \n'+note) if note else ''}"
                                f"{target_str}"
                                f"{tv_md}"
                            )
                            if send_telegram_alert(msg):
                                log_alert(sym, r.get('price'), ch, r.get('scan_type','alert'), msg)
            
            return dashboard_results
        except Exception as e:
            logger.error(f"Global lightning scan failed: {e}")
            return []
        finally:
            self.is_scanning = False

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_scan()
