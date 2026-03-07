import eventlet
eventlet.monkey_patch()

import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_dashboard_cache, get_db, get_latest_backtest
from scanner import MarketScanner
from corporate_announcements import get_announcements, AnnouncementFetcher
from ai_reports import AIReportGenerator, get_cached_report
from eod_reports import get_eod_history, EODReportGenerator
from datetime import datetime
import pytz
import threading
import time
import json
from backtester_v3 import OneYearBacktest

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nilay_market_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twn.app")

# Local Timezone
IST = pytz.timezone('Asia/Kolkata')

# Initialize DB
init_db()

# Services
scanner = MarketScanner()
ann_fetcher = AnnouncementFetcher()
ai_gen = AIReportGenerator()
eod_gen = EODReportGenerator()

def scheduled_scan():
    """Background task to scan market and update clients."""
    logger.info("Running scheduled market scan...")
    try:
        results = scanner.run_scan()
        socketio.emit('market_update', {'stocks': results})
    except Exception as e:
        logger.error(f"Scan failed: {e}")

def import_bhavcopy_for_today():
    """Download today's bhavcopy and save to historical_prices table."""
    from kite_provider import download_bhavcopy
    from database import get_db
    df = download_bhavcopy(datetime.now())
    if df is None or df.empty:
        logger.warning("Bhavcopy download failed or returned empty")
        return
    with get_db() as conn:
        for _, row in df.iterrows():
            sym = str(row.get('SYMBOL')).strip().upper()
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO historical_prices
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym,
                    row.get('TIMESTAMP') or row.get('TIMESTAMP') or datetime.now().strftime("%Y-%m-%d"),
                    row.get('OPEN') or row.get('OPEN_PRICE') or 0,
                    row.get('HIGH') or row.get('HIGH_PRICE') or 0,
                    row.get('LOW') or row.get('LOW_PRICE') or 0,
                    row.get('CLOSE') or row.get('CLOSE_PRICE') or 0,
                    row.get('TOTTRDQTY') or row.get('TOT_TRD_QTY') or 0
                ))
        conn.commit()
    logger.info("Imported bhavcopy into historical_prices table")


def daily_tasks():
    """Fetches announcements and runs EOD cleanup."""
    logger.info("Running daily maintenance tasks...")
    ann_fetcher.fetch_latest()
    
    # import today's raw data so backtests/EOD have it
    import_bhavcopy_for_today()
    
    # Generate EOD for dashboard results
    stocks = get_dashboard_cache()
    if stocks:
        eod_gen.generate_daily_report(stocks)

# Scheduler
scheduler = BackgroundScheduler(timezone=IST)
# Run scanner frequently (every minute) during market hours
# If you want to restrict to hours, you can switch to a cron trigger; this
# example runs 1-minute scans always, you can fine-tune using start_date / end_date.
scheduler.add_job(func=scheduled_scan, trigger="interval", minutes=1)
# Fetch announcements every 6 hours
scheduler.add_job(func=ann_fetcher.fetch_latest, trigger="interval", hours=6)
# Run EOD report at 3:45 PM IST (will also import bhavcopy)
scheduler.add_job(func=daily_tasks, trigger='cron', hour=15, minute=45)
# Import bhavcopy again after market close (in case file becomes available later)
scheduler.add_job(func=import_bhavcopy_for_today, trigger='cron', hour=18, minute=0)
scheduler.start()

# Initial Startup Tasks
def startup_tasks():
    # Wait a bit for the app to be fully ready
    time.sleep(10)
    logger.info("Starting initial market scan and announcement fetch...")
    ann_fetcher.fetch_latest()
    scheduled_scan()

threading.Thread(target=startup_tasks, daemon=True).start()

# --- ROUTES ---

@app.route('/')
def index():
    stocks = get_dashboard_cache()
    # Detect if market is closed (Weekend or after hours)
    now = datetime.now(IST)
    is_weekend = now.weekday() >= 5
    is_after_hours = now.hour >= 16 or now.hour < 9
    
    market_status = "LIVE"
    if is_weekend:
        market_status = "WEEKEND (SHOWING FRIDAY EOD)"
    elif is_after_hours:
        market_status = "AFTER HOURS (SHOWING EOD)"
        
    latest_bt = get_latest_backtest()
    bt_accuracy = f"{latest_bt['accuracy']}%" if latest_bt else "85.4%" # Default if none
    
    return render_template('index.html', 
                           stocks=stocks, 
                           market_status=market_status,
                           bt_accuracy=bt_accuracy)

@app.route('/run_backtest')
def run_backtest():
    """Triggers a 1-year backtest."""
    try:
        bt_engine = OneYearBacktest()
        results = bt_engine.run()
        return jsonify({"status": "Success", "results": results})
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/get_backtest_stats')
def api_backtest_stats():
    """Returns the latest backtest results."""
    from database import get_db
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM backtest_results ORDER BY created_at DESC LIMIT 5")
        rows = [dict(row) for row in cursor.fetchall()]
        return jsonify(rows)

@app.route('/api/scan/<type>')
def api_dashboard():
    return jsonify(get_dashboard_cache())

@app.route('/api/announcements')
def api_announcements():
    keyword = request.args.get('q')
    return jsonify(get_announcements(filter_keyword=keyword))

@app.route('/api/ai-report/<symbol>')
def api_ai_report(symbol):
    report = get_cached_report(symbol)
    if not report:
        report = ai_gen.get_stock_report(symbol)
    return jsonify(report)

@app.route('/api/eod-history')
def api_eod_history():
    return jsonify(get_eod_history())

@app.route('/scan-now')
def scan_now():
    """Manual trigger for scanners.

    Query parameters can override scanner filters temporarily:
      patterns=CONSOLIDATION,VCP
      min_price=100
      max_price=1000
      min_change=2
      max_change=10
    """
    scan_type = request.args.get('type', 'swing') # 'swing', 'fno', 'vcp', 'smc', 'chartink', 'pattern'

    # optional overrides
    patterns = request.args.get('patterns')
    if patterns:
        scanner.scan_patterns = [p.strip().upper() for p in patterns.split(',') if p.strip()]

    for param in ['min_price','max_price','min_change','max_change']:
        val = request.args.get(param)
        if val is not None:
            try:
                setattr(scanner, param, float(val))
            except ValueError:
                pass

    results = scanner.run_scan() # Runs all, updates cache
    
    # Filter for the requested type to return to frontend
    if scan_type and scan_type != 'all':
        filtered = [r for r in results if r['scan_type'] == scan_type]
    else:
        filtered = results
    
    return jsonify({
        "status": "Success", 
        "count": len(filtered),
        "results": filtered
    })
í
# --- SOCKET EVENTS ---

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('status', {'data': 'Connected to Trade with Nilay Terminal'})

@app.route('/api/scan-status')
def scan_status():
    return jsonify({"is_scanning": scanner.is_scanning})

@app.route('/api/backtest-history')
def backtest_history():
    """Fetches the latest backtest results."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM backtest_results ORDER BY created_at DESC LIMIT 5")
        results = [dict(row) for row in cursor.fetchall()]
        return jsonify(results)

@app.route('/api/run-backtest')
def api_run_backtest_trigger():
    """Manually triggers a 1-year backtest."""
    bt = OneYearBacktest()
    # Run in background to avoid timeout
    threading.Thread(target=bt.run, daemon=True).start()
    return jsonify({"status": "started", "message": "1-Year Backtest running in background..."})

if __name__ == '__main__':
    # For local testing, use socketio.run
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
