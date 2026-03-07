
import logging
import pandas as pd
# fundamental data will be fetched via nsepython or datasource instead of yfinance
from nsepython import nse_fundamental
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)

class AIReportGenerator:
    def __init__(self):
        pass

    def get_stock_report(self, symbol):
        """Generates a detailed fundamental and AI summary for a stock."""
        try:
            # gather fundamentals from NSE or other provider; using nsepython helper
            info = nse_fundamental(symbol)
            report = {
                "symbol": symbol,
                "name": info.get("Company Name", symbol),
                "sector": info.get("Industry", "N/A"),
                "industry": info.get("Industry", "N/A"),
                "pe_ratio": float(info.get("P/E", 0)) if info.get("P/E") else None,
                "pb_ratio": float(info.get("P/B", 0)) if info.get("P/B") else None,
                "roe": float(info.get("ROE", 0)),
                "debt_ratio": float(info.get("Debt Equity", 0)) if info.get("Debt Equity") else None,
                "revenue_growth": None,
                "profit_growth": None,
                "market_cap": float(info.get("Market Cap", 0)) / 10000000, # In Crores
                "div_yield": float(info.get("Dividend Yield", 0)) if info.get("Dividend Yield") else 0,
                "fundamental_summary": self._generate_fundamental_summary(info),
            }
            
            # Fetch relevant announcements
            report["announcements"] = self._get_latest_announcements(symbol)
            
            # AI Insight
            report["ai_insights"] = self._generate_ai_insight(info, symbol)
            
            self._save_to_db(report)
            return report
        except Exception as e:
            logger.error(f"Error generating AI report for {symbol}: {e}")
            return None

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
        # support both yfinance-like and nsepython-like keys
        name = info.get("longName") or info.get("Company Name") or "The company"
        industry = info.get("industry") or info.get("Industry") or "its sector"
        mcap_val = info.get("marketCap") or info.get("Market Cap") or 0
        try:
            mcap = float(mcap_val) / 10000000
        except:
            mcap = 0
        
        summary = f"{name} operates in the {industry} space with a market cap of ₹{mcap:,.1f} Cr. "
        
        roe = info.get("returnOnEquity") or info.get("ROE") or 0
        debt = info.get("debtToEquity") or info.get("Debt Equity") or 0
        try:
            roe = float(roe)
        except:
            roe = 0
        try:
            debt = float(debt)
        except:
            debt = 0
        
        if roe > 0.20:
            summary += "It boasts exceptionally high efficiency (ROE > 20%). "
        elif roe > 0.12:
            summary += "It maintains healthy capital efficiency. "
        else:
            summary += "Efficiency levels are currently below industry average. "
            
        if debt < 50:
            summary += "The balance sheet is strong with low leverage. "
        elif debt > 150:
            summary += "Note: High debt-to-equity ratio may restrict growth capital. "
            
        return summary

    def _generate_ai_insight(self, info, symbol):
        """Rule-based strategy insight mimicking AI analysis."""
        pe = info.get("trailingPE", 0)
        growth = info.get("revenueGrowth", 0)
        roe = info.get("returnOnEquity", 0)
        
        insights = []
        
        # Valuation Logic
        if pe and pe < 15:
            insights.append("UNDERVALUED: Trading at a significant discount to historical averages.")
        elif pe and pe > 60:
            insights.append("PREMIUM PRICING: Market has priced in high future expectations.")
            
        # Growth Logic
        if growth and growth > 0.2:
            insights.append("HIGH GROWTH: Outperforming industry peers in revenue acceleration.")
            
        # Strategy Recommendation
        if not insights:
            insights.append("NEUTRAL: Stock is fairly valued. Monitor technical breakout levels.")
        
        if roe > 0.15 and pe < 25:
             insights.append("QUALITY BUY: Rare combination of quality and reasonable valuation (GARP).")
             
        return " | ".join(insights)

    def _save_to_db(self, r):
        """Persists the report."""
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ai_reports 
                (symbol, pe_ratio, roe, debt_ratio, revenue_growth, profit_growth, fundamental_summary, ai_insights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (r['symbol'], r['pe_ratio'], r['roe'], r['debt_ratio'], r['revenue_growth'], r['profit_growth'], r['fundamental_summary'], r['ai_insights']))
            conn.commit()

def get_cached_report(symbol):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM ai_reports WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
