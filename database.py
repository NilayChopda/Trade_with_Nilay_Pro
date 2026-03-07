
import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running on Render (mount path /data exists)
RENDER_DATA_DIR = "/data"
if os.path.exists(RENDER_DATA_DIR):
    DB_PATH = os.path.join(RENDER_DATA_DIR, "trade_with_nilay_prod.db")
else:
    DB_PATH = os.environ.get("DATABASE_URL", "trade_with_nilay_prod.db")

def get_db():
    """Returns a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency on Render
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Initializes the production database schema."""
    logger.info(f"Initializing production database at {DB_PATH}")
    with get_db() as conn:
        # 1. Scanner Results (History)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scanner_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL,
                change_pct REAL,
                volume INTEGER,
                scan_type TEXT, -- 'swing' or 'fno'
                patterns TEXT,
                indicators TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Alerts Log (Telegram)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL,
                change_pct REAL,
                alert_type TEXT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Corporate Announcements
        conn.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT,
                description TEXT,
                category TEXT,
                ann_date TIMESTAMP,
                link TEXT,
                is_important INTEGER DEFAULT 0,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. EOD Reports
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eod_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE UNIQUE,
                top_gainers TEXT, -- JSON
                top_losers TEXT, -- JSON
                fii_dii_activity TEXT, -- JSON
                market_breadth TEXT, -- JSON
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. AI Reports
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_reports (
                symbol TEXT PRIMARY KEY,
                pe_ratio REAL,
                roe REAL,
                debt_ratio REAL,
                revenue_growth REAL,
                profit_growth REAL,
                fundamental_summary TEXT,
                ai_insights TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 7. Backtest Results
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                total_signals INTEGER,
                accuracy REAL,
                avg_return REAL,
                period TEXT,
                results_json TEXT, -- detailed JSON of signals
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 8. Historical Prices (NSE Bhavcopy)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_prices (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
        """)
        
        # 6. Dashboard Cache (Top results within 0-3%)
        # Better to recreate for schema updates since it's just a cache
        conn.execute("DROP TABLE IF EXISTS dashboard_cache")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                price REAL,
                change_pct REAL,
                volume INTEGER,
                scan_type TEXT,
                patterns TEXT,
                indicators TEXT,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    logger.info("Database initialization complete.")

def save_dashboard_cache(results):
    """Saves current 0-4% stocks for fast dashboard loading."""
    if not results:
        # Don't wipe the cache if we didn't find anything new (e.g. data error or empty scan)
        logger.warning("Scan returned 0 results, keeping existing cache.")
        return
        
    with get_db() as conn:
        conn.execute("DELETE FROM dashboard_cache")
        for r in results:
            conn.execute("""
                INSERT OR REPLACE INTO dashboard_cache (symbol, price, change_pct, volume, scan_type, patterns, indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                r['symbol'], 
                r['price'], 
                r['change_pct'], 
                r.get('volume', 0),
                r.get('scan_type', 'swing'),
                r.get('patterns', ''),
                r.get('indicators', '')
            ))
        conn.commit()

def get_dashboard_cache():
    """Fetches cached dashboard results."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM dashboard_cache ORDER BY change_pct DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_latest_backtest():
    """Fetches the latest backtest accuracy."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM backtest_results ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

def log_alert(symbol, price, change, alert_type, message):
    """Logs a sent Telegram alert to prevent duplicates."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO alerts_log (symbol, price, change_pct, alert_type, message)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, price, change, alert_type, message))
        conn.commit()

def is_already_alerted(symbol, hours=4):
    """Checks if alert was sent in the last 4 hours."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id FROM alerts_log 
            WHERE symbol = ? AND sent_at > datetime('now', '-' || ? || ' hours')
            LIMIT 1
        """, (symbol, hours))
        return cursor.fetchone() is not None

if __name__ == "__main__":
    init_db()
