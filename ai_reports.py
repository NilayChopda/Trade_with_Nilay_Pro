
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)

class AIReportGenerator:
    def __init__(self):
        pass

    def get_stock_report(self, symbol):
        """Generates a detailed fundamental and AI summary for a stock."""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            
            # Fundamentals
            report = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                "debt_ratio": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None,
                "profit_growth": info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else None,
                "market_cap": info.get("marketCap", 0) / 10000000, # In Crores
                "div_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
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
        name = info.get("longName", "The company")
        industry = info.get("industry", "its sector")
        mcap = info.get("marketCap", 0) / 10000000
        
        summary = f"{name} operates in the {industry} space with a market cap of ₹{mcap:,.1f} Cr. "
        
        roe = info.get("returnOnEquity", 0)
        debt = info.get("debtToEquity", 0)
        
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
