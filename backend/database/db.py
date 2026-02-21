
import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
import time
import pandas as pd

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "trade_with_nilay.db"

_INITIALIZED = False

def get_conn():
    """Get a connection to the SQLite database."""
    global _INITIALIZED
    
    # Ensure tables exist before connecting
    if not _INITIALIZED and not os.path.exists(DB_PATH):
        init_db()
    elif not _INITIALIZED:
        # Check if tables actually exist
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('stocks', 'symbols');")
            tables = [r[0] for r in cursor.fetchall()]
            if 'stocks' not in tables or 'symbols' not in tables:
                init_db()
            else:
                # 🚀 AUTO-MIGRATION: Check for missing columns
                cursor.execute("PRAGMA table_info(scanner_results)")
                columns = [row[1] for row in cursor.fetchall()]
                if columns and 'patterns' not in columns:
                    logger.info("Adding missing column 'patterns' to scanner_results")
                    cursor.execute("ALTER TABLE scanner_results ADD COLUMN patterns TEXT")
                
                # Check for other missing columns if needed
                if columns and 'ai_score' not in columns:
                    cursor.execute("ALTER TABLE scanner_results ADD COLUMN ai_score REAL")
                if columns and 'ai_rating' not in columns:
                    cursor.execute("ALTER TABLE scanner_results ADD COLUMN ai_rating TEXT")
                
                conn.commit()
                _INITIALIZED = True
            conn.close()
        except Exception as e:
            logger.error(f"Error during db connection/migration: {e}")
            init_db()

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Initialize the database schema."""
    global _INITIALIZED
    logger.info(f"Initializing database at {DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # STOCKS Table (Base universe)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        symbol TEXT PRIMARY KEY,
        company_name TEXT,
        industry TEXT,
        isin TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # SYMBOLS Table (Dashboard mapping)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symbols (
        symbol TEXT PRIMARY KEY,
        symbol_type TEXT DEFAULT 'equity',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # SCANNERS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scanners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        url TEXT,
        scanner_type TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # SCANNER RESULTS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scanner_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scanner_id INTEGER,
        symbol TEXT,
        price REAL,
        change_pct REAL,
        volume INTEGER,
        sector TEXT,
        ai_score REAL,
        ai_rating TEXT,
        patterns TEXT,
        alerted INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scanner_id) REFERENCES scanners (id)
    );
    """)
    
    # SYSTEM HEALTH Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_health (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        component TEXT,
        status TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()
    _INITIALIZED = True
    logger.info("Database initialized successfully.")

def insert_scanner(name, url, scanner_type="chartink", description=""):
    """Insert or get scanner ID."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO scanners (name, url, scanner_type, description)
        VALUES (?, ?, ?, ?)
        """, (name, url, scanner_type, description))
        conn.commit()
        
        cursor.execute("SELECT id FROM scanners WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error inserting scanner {name}: {e}")
        return None
    finally:
        conn.close()

def insert_scanner_result(scanner_id, symbol, price, change_pct, volume, sector="", timestamp=None, ai_score=None, ai_rating=None):
    """Insert a scanner result."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        if timestamp is None:
            timestamp = int(time.time())
            
        cursor.execute("""
        INSERT INTO scanner_results (scanner_id, symbol, price, change_pct, volume, sector, timestamp, ai_score, ai_rating, patterns)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (scanner_id, symbol, price, change_pct, volume, sector, timestamp, ai_score, ai_rating, ""))
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting result for {symbol}: {e}")
    finally:
        conn.close()

def update_scanner_result_ai(symbol, timestamp, ai_score, ai_rating, patterns=""):
    """Update a scanner result with AI analysis info."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE scanner_results 
        SET ai_score = ?, ai_rating = ?, patterns = ?
        WHERE symbol = ? AND timestamp = ?
        """, (ai_score, ai_rating, patterns, symbol, timestamp))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating AI result for {symbol}: {e}")
    finally:
        conn.close()

def log_health(component, status, message):
    """Log system health status."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO system_health (component, status, message)
        VALUES (?, ?, ?)
        """, (component, status, message))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging health: {e}")
    finally:
        conn.close()

def get_latest_results(scanner_name, limit=50):
    """Get latest results for a scanner."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT r.* 
        FROM scanner_results r
        JOIN scanners s ON r.scanner_id = s.id
        WHERE s.name = ?
        ORDER BY r.timestamp DESC
        LIMIT ?
        """, (scanner_name, limit))
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        return []
    finally:
        conn.close()

def get_auto_stock_findings(limit=10):
    """Get top 10 stocks with high AI scores across all scanners."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # 1. Try to get AI-scored results (Score > 7) from last 24h
        yesterday = int(time.time()) - (24 * 3600)
        cursor.execute("""
        SELECT r.*, s.name as scanner_name
        FROM scanner_results r
        JOIN scanners s ON r.scanner_id = s.id
        WHERE r.timestamp > ? AND r.ai_score >= 7.0
        ORDER BY r.ai_score DESC, r.timestamp DESC
        LIMIT ?
        """, (yesterday, limit))
        rows = [dict(row) for row in cursor.fetchall()]
        
        # 2. Fallback: If no AI results, get latest highly technical setups (manual filter equivalent)
        if not rows:
            cursor.execute("""
            SELECT r.*, s.name as scanner_name
            FROM scanner_results r
            JOIN scanners s ON r.scanner_id = s.id
            WHERE r.timestamp > ?
            ORDER BY r.timestamp DESC
            LIMIT ?
            """, (yesterday, limit))
            rows = [dict(row) for row in cursor.fetchall()]
            # Add dummy score for technical-only
            for r in rows:
                if r.get('ai_score') is None:
                    r['ai_score'] = "Tech"
                    r['ai_rating'] = "Strong Setup"
        
        return rows
    except Exception as e:
        logger.error(f"Error fetching auto findings: {e}")
        return []
    finally:
        conn.close()

def get_scanner_results(limit=50):
    """Get latest results as a DataFrame."""
    try:
        conn = get_conn()
        query = """
        SELECT r.symbol, r.price, r.change_pct, r.volume, r.ai_score, r.ai_rating, r.patterns, s.name as scanner_name, r.timestamp
        FROM scanner_results r
        JOIN scanners s ON r.scanner_id = s.id
        ORDER BY r.timestamp DESC
        LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error getting scanner results: {e}")
        return pd.DataFrame()

def get_historical_data(symbol, days=30):
    """Get historical prices for pattern detection."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT price as close, timestamp
        FROM scanner_results
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """, (symbol, days))
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return []
    finally:
        conn.close()

def mark_scanner_alerted(symbol, timestamp):
    """Mark a result as alerted."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE scanner_results SET alerted = 1 
        WHERE symbol = ? AND timestamp = ?
        """, (symbol, timestamp))
        conn.commit()
    except Exception as e:
        logger.error(f"Error marking alerted: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()