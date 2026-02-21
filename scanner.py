
import logging
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from data_provider import DataProvider
from indicators import get_technical_summary, calculate_wma, calculate_rsi
from database import get_db, save_dashboard_cache, log_alert, is_already_alerted
from telegram_bot import send_telegram_alert

logger = logging.getLogger(__name__)

class MarketScanner:
    def __init__(self):
        self.data_provider = DataProvider()
        self.symbols_equity = self._load_symbols()
        # F&O filtered subset
        self.symbols_fno = self.symbols_equity[:50] 

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

    def check_swing_criteria(self, symbol):
        """Logic for Nilay Swing Pick Algo (7 Criteria)."""
        df_daily = self.data_provider.get_historical_data(symbol, period="2y")
        if len(df_daily) < 100:
            return None
        
        df_weekly = self.resample_data(df_daily, 'W')
        df_monthly = self.resample_data(df_daily, 'M')

        # WMA Calculations
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
        return None

    def check_vcp_criteria(self, symbol):
        """Logic for Special VCP / Breakout Watch Scanner."""
        try:
            df = self.data_provider.get_historical_data(symbol, period="6mo")
            if len(df) < 50: return None
            
            # Indicators
            close = df['Close'].iloc[-1]
            ema50 = df['Close'].ewm(span=50).mean().iloc[-1]
            ema200 = df['Close'].ewm(span=200).mean().iloc[-1]
            rsi = calculate_rsi(df).iloc[-1]
            high1m = df['High'].iloc[-22:].max()
            
            # --- 1. TREND FILTER ---
            trend_ok = close > ema50 and ema50 > ema200 and close > (high1m * 0.90) and rsi > 55
            if not trend_ok: return None
            
            # --- 2. CONSOLIDATION (Tightness) ---
            range15 = df['High'].iloc[-15:].max() - df['Low'].iloc[-15:].min()
            tight_range = range15 < (close * 0.12)
            small_bodies = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1]) < (close * 0.012) and \
                           abs(df['Close'].iloc[-2] - df['Open'].iloc[-2]) < (close * 0.012)
            
            # --- 3. VOLUME DRYING ---
            avg_v5 = df['Volume'].iloc[-5:].mean()
            avg_v20 = df['Volume'].iloc[-20:].mean()
            avg_v10 = df['Volume'].iloc[-10:].mean()
            avg_v30 = df['Volume'].iloc[-30:].mean()
            vol_ok = avg_v5 < avg_v20 and avg_v10 < avg_v30
            
            # --- 4. HIGHER LOW COMPRESSION ---
            low_ok = df['Low'].iloc[-1] > df['Low'].iloc[-6] and df['Low'].iloc[-6] > df['Low'].iloc[-11]
            
            # --- 5. NEAR RESISTANCE ---
            res20 = df['High'].iloc[-21:-1].max()
            near_res = close > (res20 * 0.95)
            
            # --- BONUS: VCP STRUCTURE ---
            v30 = df['High'].iloc[-30:].max() - df['Low'].iloc[-30:].min()
            v20 = df['High'].iloc[-20:].max() - df['Low'].iloc[-20:].min()
            v10 = df['High'].iloc[-10:].max() - df['Low'].iloc[-10:].min()
            vcp_bonus = v30 > v20 and v20 > v10
            
            if trend_ok and tight_range and small_bodies and vol_ok and low_ok and near_res:
                score = "🔥 STRONG" if vcp_bonus else "⚡ TIGHT"
                return {
                    "symbol": symbol,
                    "price": round(close, 2),
                    "change_pct": round(((close - df['Close'].iloc[-2])/df['Close'].iloc[-2])*100, 2),
                    "volume": int(df['Volume'].iloc[-1]),
                    "patterns": f"VCP {score}",
                    "indicators": f"RSI: {int(rsi)} | Near Res",
                    "scan_type": "vcp"
                }
        except: return None
        return None

    def run_scan(self):
        """Runs Nilay Swing and FNO scans."""
        logger.info("Starting market scan...")
        results = []
        
        # 1. Broad Equity Scan (Swing)
        for symbol in self.symbols_equity:
            try:
                res = self.check_swing_criteria(symbol)
                if res:
                    results.append(res)
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")

        # 2. FNO Specific Scan (Tagging mostly)
        for symbol in self.symbols_fno:
            # If already in results, we skip or tag
            # For simplicity, if it meets swing, it's also a swing pick
            # But we want to show it in FNO too
            if symbol not in [r['symbol'] for r in results]:
                 try:
                    # Simple pulse check for FNO if it didn't meet full swing criteria
                    # Just to have data in FNO tab if needed, or re-run check
                    res = self.check_swing_criteria(symbol)
                    if res:
                        res['scan_type'] = 'fno' # Override for FNO tab
                        results.append(res)
                 except: continue

        # 3. SPECIAL VCP SCANPER (New Request)
        for symbol in self.symbols_equity:
            try:
                res = self.check_vcp_criteria(symbol)
                if res:
                    results.append(res)
            except: continue
        
        # Save to DB and Update Cache
        with get_db() as conn:
            for r in results:
                conn.execute("""
                    INSERT INTO scanner_results (symbol, price, change_pct, volume, scan_type, patterns, indicators)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (r['symbol'], r['price'], r['change_pct'], r['volume'], r['scan_type'], r['patterns'], r['indicators']))
                
                # Telegram: Alert ONLY if in 0-3% range
                if 0 <= r['change_pct'] <= 3.0:
                    if not is_already_alerted(r['symbol']):
                        alert_msg = f"🚀 *{r['symbol']}* ({r['change_pct']:+.2f}%)\nPrice: ₹{r['price']}\nPatterns: {r['patterns']}\nType: {r['scan_type'].upper()}"
                        if send_telegram_alert(alert_msg):
                            log_alert(r['symbol'], r['price'], r['change_pct'], r['scan_type'], alert_msg)
            
            conn.commit()
        
        # Dashboard Cache: ONLY 0-3% stocks
        dashboard_list = [r for r in results if 0 <= r['change_pct'] <= 3.0]
        save_dashboard_cache(dashboard_list)
        
        logger.info(f"Scan complete. Found {len(results)} total, {len(dashboard_list)} in 0-3% zone.")
        return results

if __name__ == "__main__":
    scanner = MarketScanner()
    scanner.run_scan()
