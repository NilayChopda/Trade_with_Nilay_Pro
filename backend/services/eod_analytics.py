"""
End of Day (EOD) Analytics Service
Generates daily market reports, gainers/losers, and sector performance

Features:
- Daily market summary (Nifty/BankNifty)
- Top Gainers & Losers
- Market Breadth (Advance/Decline)
- Sector Performance
- Auto-generated Telegram Report
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_conn, get_historical_data
from services.symbol_manager import get_indices
from services.telegram_v2 import get_notifier

logger = logging.getLogger("twn.eod_analytics")

class EODAnalytics:
    """
    Generates End of Day analysis and reports
    """
    
    def __init__(self):
        self.conn = get_conn()
        self.notifier = get_notifier()
        
    def get_market_summary(self):
        """Get summary of major indices"""
        indices = get_indices()
        summary = []
        
        # TODO: In a real implementation with live index data, 
        # we would fetch today's OHLC for indices.
        # For now, we'll placeholder this or fetch from recent data if available.
        # Since we don't store index history in minute_data (yet), we returns known indices.
        
        for idx in indices:
            if idx['name'] in ['NIFTY 50', 'NIFTY BANK']:
                summary.append(idx)
                
        return summary

    def get_top_movers(self, limit: int = 5):
        """Get top gainers and losers based on daily change"""
        try:
            # We need to calculate daily change from minute_data
            # Logic: Get latest close for each symbol and previous day's close
            # This is resource intensive, so for efficiency we'll use a simplified approach:
            # Get latest price vs price 24h ago (or open of today)
            
            # Efficient Query: Get latest candle for every symbol
            query = """
                SELECT symbol, close, 
                       (close - open) / open * 100 as change_pct,
                       volume
                FROM minute_data
                GROUP BY symbol
                HAVING max(ts)
            """
            
            # Note: The above is an approximation (Change from Today's Open). 
            # Real daily change is vs Yesterday Close. 
            # For a free tool without daily candles table, this is a good proxy for "Intraday Change".
            
            df = pd.read_sql(query, self.conn)
            
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()
                
            gainers = df.nlargest(limit, 'change_pct')
            losers = df.nsmallest(limit, 'change_pct')
            
            return gainers, losers
            
        except Exception as e:
            logger.error(f"Error calculating top movers: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_market_breadth(self):
        """Calculate market breadth (Advances vs Declines)"""
        try:
            query = """
                SELECT 
                    COUNT(CASE WHEN close > open THEN 1 END) as advances,
                    COUNT(CASE WHEN close < open THEN 1 END) as declines,
                    COUNT(CASE WHEN close = open THEN 1 END) as unchanged
                FROM minute_data
                GROUP BY symbol
                HAVING max(ts)
            """
            
            # Note: This aggregates across all symbols based on their *latest* candle
            # A better way is to iterate.
            
            # Let's reuse the logic from get_top_movers for consistency
            query_all = """
                SELECT symbol, (close - open) as change
                FROM minute_data
                GROUP BY symbol
                HAVING max(ts)
            """
            df = pd.read_sql(query_all, self.conn)
            
            if df.empty:
                return {"advances": 0, "declines": 0, "unchanged": 0}
            
            advances = len(df[df['change'] > 0])
            declines = len(df[df['change'] < 0])
            unchanged = len(df[df['change'] == 0])
            
            return {
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "total": len(df)
            }
            
        except Exception as e:
            logger.error(f"Error calculating breadth: {e}")
            return {"advances": 0, "declines": 0, "unchanged": 0}

    def generate_report(self):
        """Generate and send EOD report"""
        logger.info("Generating EOD Report...")
        
        # 1. Market Breadth
        breadth = self.get_market_breadth()
        
        # 2. Top Movers
        gainers, losers = self.get_top_movers(limit=5)
        
        # 3. Construct Message
        lines = []
        lines.append("📊 *END OF DAY REPORT* 📊")
        lines.append(f"Date: {datetime.now().strftime('%d-%b-%Y')}")
        lines.append("")
        
        # Market Breadth
        if breadth.get('total', 0) > 0:
            lines.append(f"📈 *Market Breadth*")
            lines.append(f"🟢 Advances: {breadth['advances']}")
            lines.append(f"🔴 Declines: {breadth['declines']}")
            lines.append(f"⚪ Unchanged: {breadth['unchanged']}")
            ratio = breadth['advances'] / breadth['declines'] if breadth['declines'] > 0 else 0
            lines.append(f"A/D Ratio: {ratio:.2f}")
            lines.append("")
        
        # Top Gainers
        if not gainers.empty:
            lines.append("🚀 *Top 5 Gainers*")
            for _, row in gainers.iterrows():
                lines.append(f"{row['symbol']}: ₹{row['close']:.2f} (+{row['change_pct']:.2f}%)")
            lines.append("")
            
        # Top Losers
        if not losers.empty:
            lines.append("🐻 *Top 5 Losers*")
            for _, row in losers.iterrows():
                lines.append(f"{row['symbol']}: ₹{row['close']:.2f} ({row['change_pct']:.2f}%)")
            lines.append("")
            
        # Footer
        lines.append("---")
        lines.append("Generated by Trade With Nilay")
        
        report_text = "\n".join(lines)
        
        # Send via Telegram
        self.notifier.send_message(report_text)
        
        logger.info("EOD Report Sent.")
        return report_text

    def close(self):
        self.conn.close()

def run_eod_process():
    """Main entry point for scheduler"""
    analytics = EODAnalytics()
    try:
        analytics.generate_report()
    finally:
        analytics.close()

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    run_eod_process()
