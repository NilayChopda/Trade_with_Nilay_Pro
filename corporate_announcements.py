
import logging
import requests
import json
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)

class AnnouncementFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
        })

    def fetch_latest(self):
        """Fetches latest announcements from NSE."""
        logger.info("Fetching corporate announcements...")
        try:
            # Initial hit to get cookies
            self.session.get("https://www.nseindia.com", timeout=10)
            
            # API endpoint for announcements
            url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                self._save_to_db(data)
                return data
            else:
                logger.error(f"NSE Announcement API failed with status {resp.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching announcements: {e}")
            return []

    def _is_important(self, title, desc):
        """Checks if an announcement is high-impact."""
        keywords = [
            'RESULT', 'EARNINGS', 'DIVIDEND', 'BONUS', 'SPLIT', 'MERGER', 
            'ACQUISITION', 'ORDER', 'CONTRACT', 'CONCALL', 'MEETING', 
            'AWARD', 'JOINT VENTURE', 'BUYBACK', 'LOAN', 'DEFAULT', 'FRAUD'
        ]
        text = (title + " " + desc).upper()
        return any(k in text for k in keywords)

    def _save_to_db(self, data):
        """Saves announcements to the database, avoids duplicates."""
        with get_db() as conn:
            for item in data:
                symbol = item.get('symbol')
                desc = item.get('desc', '')
                title = item.get('subject', 'Announcement')
                category = item.get('category', 'Others')
                link = item.get('attchmntText', '')
                dt_str = item.get('attchmntDate', datetime.now().strftime("%Y-%m-%d"))
                
                important = 1 if self._is_important(title, desc) else 0
                
                # Check for duplicate link or description
                cursor = conn.execute("SELECT id FROM announcements WHERE symbol = ? AND title = ? AND ann_date = ?", (symbol, title, dt_str))
                if not cursor.fetchone():
                    conn.execute("""
                        INSERT INTO announcements (symbol, title, description, category, ann_date, link, is_important)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (symbol, title, desc, category, dt_str, link, important))
            conn.commit()
        logger.info(f"Announcements updated: {len(data)} items processed.")

def get_announcements(filter_keyword=None, limit=100):
    """Fetches announcements from DB with optional filter."""
    with get_db() as conn:
        query = "SELECT * FROM announcements"
        params = []
        if filter_keyword:
            query += " WHERE symbol LIKE ? OR title LIKE ? OR category LIKE ?"
            like_val = f"%{filter_keyword}%"
            params = [like_val, like_val, like_val]
        
        query += " ORDER BY ann_date DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

if __name__ == "__main__":
    fetcher = AnnouncementFetcher()
    fetcher.fetch_latest()
