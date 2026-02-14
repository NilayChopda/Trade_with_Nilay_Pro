import sqlite3
from pathlib import Path
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "trade_with_nilay.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


_INIT_LOCK = threading.Lock()
_INITIALIZED = False


def init_db():
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _INIT_LOCK:
        conn = get_conn()
        cur = conn.cursor()
        
        # ===== CORE TABLES =====
        
        # Symbols table: managed externally (list of tracked symbols)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                symbol TEXT PRIMARY KEY,
                exchange TEXT DEFAULT 'NSE',
                symbol_type TEXT DEFAULT 'equity',  -- 'equity', 'fno', 'index'
                is_active INTEGER DEFAULT 1,
                last_updated INTEGER,
                meta JSON
            )
            """
        )

        # Minute data: basic OHLCV per minute per symbol (EQUITY)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS minute_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                ts INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(symbol, ts)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_minute_symbol_ts ON minute_data(symbol, ts)")
        
        # ===== F&O TABLES =====
        
        # F&O option chain data
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fno_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                strike_price REAL,
                option_type TEXT,  -- 'CE', 'PE', 'FUT'
                timestamp INTEGER NOT NULL,
                open_interest INTEGER,
                volume INTEGER,
                ltp REAL,
                bid REAL,
                ask REAL,
                iv REAL,  -- Implied Volatility
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                UNIQUE(symbol, expiry_date, strike_price, option_type, timestamp)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fno_symbol_expiry ON fno_data(symbol, expiry_date, timestamp)")
        
        # ===== INDICES TABLES =====
        
        # Index values (NIFTY, BANKNIFTY, etc.)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS indices_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                value REAL NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                change_pct REAL,
                volume INTEGER,
                UNIQUE(index_name, timestamp)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_indices_name_ts ON indices_data(index_name, timestamp)")
        
        # ===== SCANNER TABLES =====
        
        # Scanner configurations
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scanners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                scanner_type TEXT NOT NULL,  -- 'equity', 'fno'
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at INTEGER NOT NULL,
                last_run INTEGER
            )
            """
        )
        
        # Scanner results
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scanner_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scanner_id INTEGER,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                price REAL NOT NULL,
                change_pct REAL NOT NULL,
                volume INTEGER,
                market_cap REAL,
                sector TEXT,
                alerted INTEGER DEFAULT 0,  -- Telegram alert sent flag
                alert_sent_at INTEGER,
                FOREIGN KEY(scanner_id) REFERENCES scanners(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scanner_results_ts ON scanner_results(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scanner_results_symbol ON scanner_results(symbol, timestamp)")
        
        # ===== MONITORING & QUALITY TABLES =====
        
        # Data quality log
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS data_quality_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                data_type TEXT NOT NULL,  -- 'equity', 'fno', 'indices'
                total_symbols INTEGER,
                successful INTEGER,
                failed INTEGER,
                error_details TEXT,
                fetch_duration_sec REAL,
                status TEXT DEFAULT 'success'  -- 'success', 'partial', 'failed'
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_quality_log_ts ON data_quality_log(timestamp)")
        
        # System health monitoring
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                component TEXT NOT NULL,  -- 'fetcher', 'scanner', 'api', 'telegram'
                status TEXT NOT NULL,  -- 'healthy', 'degraded', 'down'
                latency_ms REAL,
                error_count INTEGER DEFAULT 0,
                message TEXT
            )
            """
        )
        
        # ===== EOD REPORTS =====
        
        # End of day reports
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS eod_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL UNIQUE,  -- YYYY-MM-DD
                timestamp INTEGER NOT NULL,
                total_stocks INTEGER,
                gainers INTEGER,
                losers INTEGER,
                unchanged INTEGER,
                top_gainer TEXT,
                top_gainer_pct REAL,
                top_loser TEXT,
                top_loser_pct REAL,
                total_volume INTEGER,
                market_sentiment TEXT,  -- 'bullish', 'bearish', 'neutral'
                report_data JSON  -- Full report as JSON
            )
            """
        )

        conn.commit()
        conn.close()
        _INITIALIZED = True


def insert_minute(symbol: str, ts: int, o: float, h: float, l: float, c: float, volume: float):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO minute_data(symbol, ts, open, high, low, close, volume) VALUES(?,?,?,?,?,?,?)",
            (symbol, ts, o, h, l, c, volume),
        )
        conn.commit()
    finally:
        conn.close()


def bulk_insert(rows):
    """rows: iterable of (symbol, ts, o,h,l,c,volume)"""
    conn = get_conn()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO minute_data(symbol, ts, open, high, low, close, volume) VALUES(?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


# ===== SCANNER FUNCTIONS =====

def insert_scanner(name: str, url: str, scanner_type: str, description: str = None):
    """Add a new scanner configuration"""
    conn = get_conn()
    try:
        import time
        ts = int(time.time())
        conn.execute(
            "INSERT OR REPLACE INTO scanners(name, url, scanner_type, description, created_at) VALUES(?,?,?,?,?)",
            (name, url, scanner_type, description, ts),
        )
        conn.commit()
        return conn.execute("SELECT id FROM scanners WHERE name=?", (name,)).fetchone()[0]
    finally:
        conn.close()


def insert_scanner_result(scanner_id: int, symbol: str, price: float, change_pct: float, 
                         volume: int = None, market_cap: float = None, sector: str = None):
    """Insert scanner result"""
    conn = get_conn()
    try:
        import time
        ts = int(time.time())
        conn.execute(
            """INSERT INTO scanner_results(scanner_id, symbol, timestamp, price, change_pct, volume, market_cap, sector)
               VALUES(?,?,?,?,?,?,?,?)""",
            (scanner_id, symbol, ts, price, change_pct, volume, market_cap, sector),
        )
        conn.commit()
    finally:
        conn.close()


def mark_scanner_alerted(result_id: int):
    """Mark scanner result as alerted"""
    conn = get_conn()
    try:
        import time
        ts = int(time.time())
        conn.execute(
            "UPDATE scanner_results SET alerted=1, alert_sent_at=? WHERE id=?",
            (ts, result_id)
        )
        conn.commit()
    finally:
        conn.close()


# ===== MONITORING FUNCTIONS =====

def log_data_quality(data_type: str, total: int, successful: int, failed: int, 
                     duration: float, status: str = 'success', errors: str = None):
    """Log data quality metrics"""
    conn = get_conn()
    try:
        import time
        ts = int(time.time())
        conn.execute(
            """INSERT INTO data_quality_log(timestamp, data_type, total_symbols, successful, failed, 
               fetch_duration_sec, status, error_details) VALUES(?,?,?,?,?,?,?,?)""",
            (ts, data_type, total, successful, failed, duration, status, errors)
        )
        conn.commit()
    finally:
        conn.close()


def log_system_health(component: str, status: str, latency_ms: float = None, 
                     error_count: int = 0, message: str = None):
    """Log system health check"""
    conn = get_conn()
    try:
        import time
        ts = int(time.time())
        conn.execute(
            """INSERT INTO system_health(timestamp, component, status, latency_ms, error_count, message)
               VALUES(?,?,?,?,?,?)""",
            (ts, component, status, latency_ms, error_count, message)
        )
        conn.commit()
    finally:
        conn.close()


# ===== QUERY FUNCTIONS =====

def get_latest_price(symbol: str):
    """Get latest price for a symbol"""
    conn = get_conn()
    try:
        result = conn.execute(
            "SELECT close, ts FROM minute_data WHERE symbol=? ORDER BY ts DESC LIMIT 1",
            (symbol,)
        ).fetchone()
        return result if result else None
    finally:
        conn.close()


def get_historical_data(symbol: str, start_ts: int, end_ts: int):
    """Get historical OHLCV data for a symbol"""
    conn = get_conn()
    try:
        import pandas as pd
        query = """
            SELECT ts, open, high, low, close, volume 
            FROM minute_data 
            WHERE symbol=? AND ts BETWEEN ? AND ?
            ORDER BY ts ASC
        """
        df = pd.read_sql_query(query, conn, params=(symbol, start_ts, end_ts))
        return df
    finally:
        conn.close()


def get_historical_data(symbol: str, days: int = 30):
    """
    Get historical OHLCV data for a symbol
    
    Args:
        symbol: Stock symbol
        days: Number of days of history to fetch
        
    Returns:
        List of dicts with timestamp, open, high, low, close, volume
    """
    import pandas as pd
    from datetime import datetime, timedelta
    
    conn = get_conn()
    try:
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        
        query = """
            SELECT ts as timestamp, open, high, low, close, volume 
            FROM minute_data 
            WHERE symbol=? AND ts BETWEEN ? AND ?
            ORDER BY ts ASC
        """
        cursor = conn.execute(query, (symbol, start_ts, end_ts))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        if rows:
            return [
                {
                    'timestamp': row[0],
                    'open': row[1],
                    'high': row[2],
                    'low': row[3],
                    'close': row[4],
                    'volume': row[5]
                }
                for row in rows
            ]
        return []
    finally:
        conn.close()


def get_scanner_results(scanner_id: int = None, limit: int = 100, only_unalerted: bool = False):
    """Get scanner results"""
    conn = get_conn()
    try:
        query = """
            SELECT sr.*, s.name as scanner_name 
            FROM scanner_results sr
            LEFT JOIN scanners s ON sr.scanner_id = s.id
            WHERE 1=1
        """
        params = []
        
        if scanner_id:
            query += " AND sr.scanner_id=?"
            params.append(scanner_id)
        
        if only_unalerted:
            query += " AND alerted=0"
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        import pandas as pd
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized DB at {DB_PATH}")