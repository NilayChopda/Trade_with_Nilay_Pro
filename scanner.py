
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
        self.scan_patterns = [p.strip().upper() for p in os.getenv("SCAN_PATTERNS", "CONSOLIDATION,VCP,ORDER_BLOCK,BREAKOUT,HIGH_RS").split(",") if p.strip()]
        
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

    def run_scan(self):
        """High-speed parallel scan across 2600+ stocks."""
        if self.is_scanning:
            logger.warning("Scan already in progress...")
            return []
            
        self.is_scanning = True
        logger.info(f"Starting lightning scan for {len(self.symbols_equity)} stocks...")
        results = []
        
        # Pre-fetch Nifty 50 data for RS comparison
        nifty_df = self.data_provider.get_historical_data("NIFTY 50", period="1y")

        def process_symbol(symbol):
            try:
                df = self.data_provider.get_historical_data(symbol, period="1y")
                if df.empty or len(df) < 2:
                    return []
                    
                pdinfo = self.pattern_detector.analyze(df, symbol, nifty_df=nifty_df)

                primary = pdinfo.get('primary_pattern')
                live = self.data_provider.fetch_nse_quote(symbol)
                
                # Weekend Fallback Logic
                # If market is closed (ch close to 0 or it's Sat/Sun), 
                # use the change from the last available trading candle (Friday vs Thursday)
                is_weekend = datetime.now().weekday() in [5, 6] or (datetime.now().weekday() == 0 and datetime.now().hour < 9)
                
                price = float(live.get('price', 0)) if live else df['close'].iloc[-1]
                ch = float(live.get('change_pct', 0)) if live else 0
                
                if (is_weekend or ch == 0) and len(df) >= 2:
                    # Daily change of the last candle
                    prev_close = df['close'].iloc[-2]
                    curr_close = df['close'].iloc[-1]
                    ch = ((curr_close - prev_close) / prev_close) * 100
                    price = curr_close

                if not primary:
                    if pdinfo.get('rs_score', 0) > 95:
                        primary = "HIGH_RS"
                    else:
                        return []
                
                # Setup prioritization: Elite setups are ALWAYS kept for study
                elite_patterns = ["VCP", "HIGH_TIGHT_FLAG", "BLUE_SKY", "HIGH_RS"]
                is_elite = any(p in (primary or '') for p in elite_patterns)
                
                if not is_elite:
                    if primary.upper() not in self.scan_patterns:
                        return []
                    # Standard filters for non-elite
                    if not (self.min_change <= ch <= self.max_change):
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
                    "price": round(price, 2),
                    "change_pct": round(ch, 2),
                    "volume": int(live.get('volume', 0)) if live else int(df['volume'].iloc[-1]),
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
                    
                    s_type = "swing"
                    if "fno" in c_name.lower():
                        s_type = "fno"
                    elif "vcp" in c_name.lower():
                        s_type = "vcp"
                    
                    for s in (c_stocks or []):
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

            # Filter and cache results
            dashboard_results = []
            seen = set()
            index_keywords = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'CNX', 'INDIA VIX', 'SENSEX']
            
            is_weekend = datetime.now().weekday() in [5, 6] or (datetime.now().weekday() == 0 and datetime.now().hour < 9)
            elite_patterns = ["VCP", "HIGH_TIGHT_FLAG", "BLUE_SKY", "HIGH_RS"]

            for r in results:
                symbol = r['symbol'].upper()
                if symbol in seen or any(k in symbol for k in index_keywords):
                    continue
                
                price = r.get('price', 0)
                ch = r.get('change_pct', 0)
                setup = r.get('patterns', '')
                is_elite = any(p in setup for p in elite_patterns)

                # Relax filters for Elite setups or Weekend study
                if not is_elite:
                    if not (self.min_price <= price <= self.max_price):
                        continue
                    if not (self.min_change <= ch <= self.max_change):
                        continue
                else:
                    # For elite, just ensure price is reasonable
                    if not (self.min_price <= price):
                        continue

                dashboard_results.append(r)
                seen.add(symbol)

            dashboard_results.sort(key=lambda x: x['change_pct'], reverse=True)
            dashboard_results = dashboard_results[:30]
            
            logger.info(f"Scan complete. Total raw: {len(results)}, Valid stocks: {len(dashboard_results)}")
            save_dashboard_cache(dashboard_results)

            # --- REFINED TELEGRAM ALERTS (Professional Conditions) ---
            elite_patterns = ["VCP", "HIGH_TIGHT_FLAG", "BLUE_SKY", "HIGH_RS"]
            allowed_candles = ["Doji", "Hammer", "Bullish Engulfing", "Bullish Harami", "Inside Bar"]
            
            for r in results:
                sym = r['symbol']
                if is_already_alerted(sym):
                    continue
                    
                ch = r.get('change_pct', 0)
                setup = r.get('patterns', '')
                is_elite = any(p in setup for p in elite_patterns)
                
                # Condition 1: Elite Pattern (VCP, HTF, RS > 95)
                # Condition 2: Price Action (-1% to +3%) + Candlestick
                trigger_alert = False
                alert_reason = ""
                
                # We already have pdinfo from the scan phase, but let's re-verify for the message
                df_hist = self.data_provider.get_historical_data(sym, period="1y")
                pdinfo = self.pattern_detector.analyze(df_hist, sym, nifty_df=nifty_df)
                candle = pdinfo.get('candlestick')
                
                if is_elite:
                    trigger_alert = True
                    alert_reason = "ELITE SETUP"
                elif -1.0 <= ch <= 3.0 and candle in allowed_candles:
                    trigger_alert = True
                    alert_reason = "PATTERN ALERT"
                
                if trigger_alert:
                    note = r.get('pattern_note') or ''
                    tv_link = os.getenv('TRADINGVIEW_BASE', '').strip()
                    tv_md = f"\n🔗 [Chart]({tv_link.format(symbol=sym)})" if tv_link else ""
                    
                    target_str = f"\n🎯 Target: ₹{r['target']} ({r['target_pct']:+.1f}%)" if r.get('target') else ''
                    rs_val = pdinfo.get('rs_score', 0)
                    rs_str = f"\n📊 RS Rating: {rs_val}" if rs_val > 0 else ""
                    
                    msg = (
                        f"🚀 *{alert_reason}* {sym}\n"
                        f"Price: ₹{r.get('price')} ({ch:+.2f}%)\n"
                        f"Setup: *{setup}*\n"
                        f"Candle: {candle or 'Normal'}"
                        f"{rs_str}"
                        f"{target_str}\n"
                        f"{note}"
                        f"{tv_md}"
                    )
                    if send_telegram_alert(msg):
                        log_alert(sym, r.get('price'), ch, r.get('scan_type', 'alert'), msg)
            
            return dashboard_results
        except Exception as e:
            logger.error(f"Global lightning scan failed: {e}")
            return []
        finally:
            self.is_scanning = False

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_scan()
