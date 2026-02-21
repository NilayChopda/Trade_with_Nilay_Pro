
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
        # F&O filtered subset (Top 100 most liquid)
        self.symbols_fno = self.symbols_equity[:100] if len(self.symbols_equity) > 100 else self.symbols_equity
        
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
        """Loads symbols from local data/symbols.json."""
        try:
            path = Path(__file__).parent / "data" / "symbols.json"
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
        return ["RELIANCE", "TCS", "HDFCBANK", "INFY"]

    def resample_data(self, df, timeframe='W'):
        """Resamples daily data to Weekly or Monthly."""
        resampled = df.resample(timeframe).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        return resampled
    def check_swing_criteria(self, symbol, override_df=None):
        """Logic for NILAY SWING PICK - ALGO (Support backtest override)."""
        try:
            if override_df is not None:
                df_daily = override_df
            else:
                df_daily = self.data_provider.get_historical_data(symbol, period="1y")
            
            if len(df_daily) < 100: return None
            
            df_weekly = self.resample_data(df_daily, 'W')
            df_monthly = self.resample_data(df_daily, 'M')

            wma1_d = calculate_wma(df_daily, 1).iloc[-1]
            wma2_m = calculate_wma(df_monthly, 2).iloc[-1]
            wma4_m = calculate_wma(df_monthly, 4).iloc[-1]
            wma6_w = calculate_wma(df_weekly, 6).iloc[-1]
            wma12_w = calculate_wma(df_weekly, 12).iloc[-1]
            wma12_d_4ago = calculate_wma(df_daily, 12).iloc[-5] if len(df_daily) > 12 else 0
            wma20_d_2ago = calculate_wma(df_daily, 20).iloc[-3] if len(df_daily) > 20 else 0
            close = df_daily['Close'].iloc[-1]

            # 7 Criteria
            c1 = wma1_d > (wma2_m + 1)
            c2 = wma2_m > (wma4_m + 2)
            c3 = wma1_d > (wma6_w + 2)
            c4 = wma6_w > (wma12_w + 2)
            c5 = wma1_d > (wma12_d_4ago + 2)
            c6 = wma1_d > (wma20_d_2ago + 2)
            c7 = close > 20

            if all([c1, c2, c3, c4, c5, c6, c7]):
                tech = get_technical_summary(df_daily)
                return {
                    "symbol": symbol,
                    "price": round(close, 2),
                    "change_pct": round(((close - df_daily['Close'].iloc[-2])/df_daily['Close'].iloc[-2])*100, 2),
                    "volume": int(df_daily['Volume'].iloc[-1]),
                    "patterns": ", ".join(tech['patterns']),
                    "indicators": ", ".join(tech['signals']),
                    "scan_type": "swing"
                }
        except Exception as e:
            logger.error(f"Swing check failed for {symbol}: {e}")
            return None
        return None
        return None

    def check_vcp_criteria(self, symbol, override_df=None):
        """Logic for Special VCP / Breakout Watch Scanner."""
        try:
            if override_df is not None:
                df = override_df
            else:
                df = self.data_provider.get_historical_data(symbol, period="1y")
            
            if len(df) < 150: return None
            
            # Use PatternDetector for robust VCP detection
            df.columns = [c.lower() for c in df.columns]
            analysis = self.pattern_detector.analyze(df, symbol)
            
            is_vcp = any(p['type'] == 'VCP' for p in analysis['patterns'])
            is_breakout = any(p['type'] == 'BREAKOUT' for p in analysis['patterns'])
            
            if is_vcp or is_breakout:
                close = df['close'].iloc[-1]
                rsi = calculate_rsi(df).iloc[-1]
                patterns = [self.pattern_detector.get_pattern_badge(p['type'], p['confidence']) for p in analysis['patterns']]
                
                return {
                    "symbol": symbol,
                    "price": round(close, 2),
                    "change_pct": round(((close - df['close'].iloc[-2])/df['close'].iloc[-2])*100, 2),
                    "volume": int(df['volume'].iloc[-1]),
                    "patterns": " | ".join(patterns),
                    "indicators": f"RSI: {int(rsi)} | Confidence: {int(analysis['confidence']*100)}%",
                    "scan_type": "vcp"
                }
        except Exception as e:
            logger.error(f"VCP scan failed for {symbol}: {e}")
            return None
        return None

    def check_smc_criteria(self, symbol, override_df=None):
        """Logic for Smart Money Concepts (SMC) Demand Zones."""
        try:
            if override_df is not None:
                df = override_df
            else:
                df = self.data_provider.get_historical_data(symbol, period="6mo")
            
            if len(df) < 50: return None
            
            df.columns = [c.lower() for c in df.columns]
            df['timestamp'] = df.index
            
            setup = self.smc_engine.check_setup(df)
            if setup and setup['score'] >= 7:
                close = df['close'].iloc[-1]
                return {
                    "symbol": symbol,
                    "price": round(close, 2),
                    "change_pct": round(((close - df['close'].iloc[-2])/df['close'].iloc[-2])*100, 2),
                    "volume": int(df['volume'].iloc[-1]),
                    "patterns": f"SMC: {setup['signal']}",
                    "indicators": " | ".join(setup['reasons']),
                    "scan_type": "smc"
                }
        except: return None
        return None

    def run_scan(self):
        """Runs all scanners in parallel for speed."""
        if self.is_scanning:
            logger.warning("Scan already in progress, skipping...")
            return []
            
        self.is_scanning = True
        logger.info(f"Starting parallel market scan for {len(self.symbols_equity)} symbols...")
        results = []
        
        def process_symbol(symbol):
            symbol_results = []
            # 1. Swing
            try:
                swing = self.check_swing_criteria(symbol)
                if swing: symbol_results.append(swing)
            except: pass
            
            # 2. VCP
            try:
                vcp = self.check_vcp_criteria(symbol)
                if vcp: symbol_results.append(vcp)
            except: pass
            
            # 3. SMC
            try:
                smc = self.check_smc_criteria(symbol)
                if smc: symbol_results.append(smc)
            except: pass
            
            return symbol_results

        def fetch_chartink(scanner_obj):
            try:
                stocks = scanner_obj.fetch_results()
                results = []
                for s in stocks:
                    results.append({
                        "symbol": s['symbol'],
                        "price": s['price'],
                        "change_pct": s['change_pct'],
                        "volume": s['volume'],
                        "patterns": f"Chartink: {scanner_obj.scanner_name}",
                        "indicators": "Live Alert",
                        "scan_type": "chartink"
                    })
                return results
            except:
                return []

        try:
            # Parallel internal scanning (Python logic)
            with ThreadPoolExecutor(max_workers=10) as executor:
                # 1. run internal symbol checks
                future_to_sym = {executor.submit(process_symbol, sym): sym for sym in self.symbols_equity}
                
                # 2. run Chartink scanners in parallel too
                future_to_chartink = {executor.submit(fetch_chartink, c): c.scanner_name for c in self.chartink_scanners}
                
                for future in as_completed(future_to_sym):
                    res_list = future.result()
                    if res_list:
                        results.extend(res_list)
                        
                for future in as_completed(future_to_chartink):
                    chartink_res = future.result()
                    if chartink_res:
                        results.extend(chartink_res)

        except Exception as e:
            logger.error(f"Global scan failed: {e}")
        finally:
            self.is_scanning = False

        # Save to DB and Update Cache
        try:
            with get_db() as conn:
                # Clear old cache for dashboard (0-3% range)
                dashboard_results = [r for r in results if 0 <= r.get('change_pct', 0) <= 3.0]
                save_dashboard_cache(dashboard_results)
                
                for r in results:
                    conn.execute("""
                        INSERT INTO scanner_results (symbol, price, change_pct, volume, scan_type, patterns, indicators)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (r['symbol'], r['price'], r['change_pct'], r.get('volume', 0), r['scan_type'], r['patterns'], r['indicators']))
                    
                    # Telegram Alerts Logic
                    if 0 <= r.get('change_pct', 0) <= 3.0:
                        if not is_already_alerted(r['symbol']):
                            alert_msg = f"🚀 *{r['symbol']}* ({r['change_pct']:+.2f}%)\nPrice: ₹{r['price']}\nPatterns: {r['patterns']}\nType: {r['scan_type'].upper()}"
                            if send_telegram_alert(alert_msg):
                                log_alert(r['symbol'], r['price'], r['change_pct'], r['scan_type'], alert_msg)
            
            return dashboard_results
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            return []

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_scan()
