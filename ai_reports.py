
import logging
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)

def _safe_float(val, default=0):
    """Safely convert a value to float."""
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

class AIReportGenerator:
    def __init__(self):
        pass

    def _fetch_nse_info(self, symbol):
        """Fetch fundamental info from NSE using nse_quote (available in nsepython 2.x)."""
        try:
            from nsepython import nse_quote
            data = nse_quote(symbol)
            if not data:
                return {}
            # Extract useful fields from the NSE quote response
            price_info = data.get("priceInfo", {})
            info = data.get("info", {}) or data.get("metadata", {}) or {}
            return {
                "Company Name": info.get("companyName", symbol),
                "Industry": info.get("industry", "N/A"),
                "symbol": symbol,
                "lastPrice": price_info.get("lastPrice", 0),
                "pChange": price_info.get("pChange", 0),
                "previousClose": price_info.get("previousClose", 0),
                # PE/PB etc. are not always in quote; set to None if missing
                "P/E": info.get("pe", None) or info.get("pdSymbolPe", None),
                "P/B": None,
                "ROE": 0,
                "Debt Equity": 0,
                "Market Cap": 0,
                "Dividend Yield": 0,
            }
        except Exception as e:
            logger.error(f"NSE quote fetch failed for {symbol}: {e}")
            return {"Company Name": symbol, "Industry": "N/A"}

    def get_stock_report(self, symbol):
        """Generates a detailed fundamental and AI summary for a stock."""
        try:
            info = self._fetch_nse_info(symbol)
            report = {
                "symbol": symbol,
                "name": info.get("Company Name", symbol),
                "sector": info.get("Industry", "N/A"),
                "industry": info.get("Industry", "N/A"),
                "pe_ratio": _safe_float(info.get("P/E"), None),
                "pb_ratio": _safe_float(info.get("P/B"), None),
                "roe": _safe_float(info.get("ROE")),
                "debt_ratio": _safe_float(info.get("Debt Equity"), None),
                "revenue_growth": None,
                "profit_growth": None,
                "fundamental_summary": self._generate_fundamental_summary(info),
            }
            
            report["announcements"] = self._get_latest_announcements(symbol)
            report["ai_insights"] = self._generate_ai_insight(info, symbol)
            
            self._save_to_db(report)
            return report
        except Exception as e:
            logger.error(f"Error generating AI report for {symbol}: {e}")
            return {
                "symbol": symbol,
                "pe_ratio": None,
                "roe": None,
                "fundamental_summary": "Report generation failed. Please try again later.",
                "ai_insights": "Unable to generate insights at this time."
            }

    def _get_latest_announcements(self, symbol):
        """Fetches top 3 announcements for this stock from DB."""
        try:
            with get_db() as conn:
                cursor = conn.execute("SELECT title, ann_date FROM announcements WHERE symbol = ? ORDER BY ann_date DESC LIMIT 3", (symbol,))
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def _generate_fundamental_summary(self, info):
        """Creates a human-readable fundamental summary."""
        name = info.get("Company Name") or "The company"
        industry = info.get("Industry") or "its sector"
        mcap = _safe_float(info.get("Market Cap")) / 10000000

        summary = f"{name} operates in the {industry} space"
        if mcap > 0:
            summary += f" with a market cap of ₹{mcap:,.1f} Cr"
        summary += ". "
        
        roe = _safe_float(info.get("ROE"))
        debt = _safe_float(info.get("Debt Equity"))

        if roe > 0.20:
            summary += "It boasts exceptionally high efficiency (ROE > 20%). "
        elif roe > 0.12:
            summary += "It maintains healthy capital efficiency. "
        
        if debt > 0 and debt < 50:
            summary += "The balance sheet is strong with low leverage. "
        elif debt > 150:
            summary += "Note: High debt-to-equity ratio may restrict growth capital. "
            
        return summary

    def _generate_ai_insight(self, info, symbol):
        """Rule-based strategy insight mimicking AI analysis."""
        pe = _safe_float(info.get("P/E"))
        roe = _safe_float(info.get("ROE"))
        
        insights = []
        
        if pe and pe < 15:
            insights.append("UNDERVALUED: Trading at a significant discount to historical averages.")
        elif pe and pe > 60:
            insights.append("PREMIUM PRICING: Market has priced in high future expectations.")
            
        if not insights:
            insights.append("NEUTRAL: Stock is fairly valued. Monitor technical breakout levels.")
        
        if roe > 0.15 and pe and pe < 25:
            insights.append("QUALITY BUY: Rare combination of quality and reasonable valuation (GARP).")
             
        return " | ".join(insights)

    def _save_to_db(self, r):
        """Persists the report."""
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ai_reports 
                (symbol, pe_ratio, roe, debt_ratio, revenue_growth, profit_growth, fundamental_summary, ai_insights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (r['symbol'], r.get('pe_ratio'), r.get('roe'), r.get('debt_ratio'), r.get('revenue_growth'), r.get('profit_growth'), r.get('fundamental_summary',''), r.get('ai_insights','')))
            conn.commit()

def get_cached_report(symbol):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM ai_reports WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
