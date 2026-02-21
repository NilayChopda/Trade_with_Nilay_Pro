
import logging
import json
from datetime import datetime
from data_provider import DataProvider
from database import get_db

logger = logging.getLogger(__name__)

class EODReportGenerator:
    def __init__(self):
        self.data_provider = DataProvider()

    def generate_daily_report(self, stocks_list):
        """Processes a list of quotes to generate the End of Day summary."""
        logger.info("Generating EOD report...")
        
        # Sort by change %
        sorted_stocks = sorted(stocks_list, key=lambda x: x.get('change_pct', 0), reverse=True)
        
        top_gainers = sorted_stocks[:5]
        top_losers = sorted_stocks[-5:]
        
        # Breadth calculation
        advances = sum(1 for s in stocks_list if s.get('change_pct', 0) > 0)
        declines = sum(1 for s in stocks_list if s.get('change_pct', 0) < 0)
        
        fii_dii = self.data_provider.fetch_fii_dii_activity()
        
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "top_gainers": json.dumps(top_gainers),
            "top_losers": json.dumps(top_losers),
            "fii_dii_activity": json.dumps(fii_dii),
            "market_breadth": json.dumps({"advances": advances, "declines": declines}),
            "summary": f"Market closed with {advances} advances and {declines} declines. FII Net: {fii_dii['fii_net']} Cr."
        }
        
        self._save_to_db(report)
        return report

    def _save_to_db(self, r):
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO eod_reports 
                (report_date, top_gainers, top_losers, fii_dii_activity, market_breadth, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (r['report_date'], r['top_gainers'], r['top_losers'], r['fii_dii_activity'], r['market_breadth'], r['summary']))
            conn.commit()

def get_eod_history(limit=30):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM eod_reports ORDER BY report_date DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
