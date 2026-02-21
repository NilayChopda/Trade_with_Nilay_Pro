
import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, get_dashboard_cache, get_db
from scanner import MarketScanner
from corporate_announcements import get_announcements, AnnouncementFetcher
from ai_reports import AIReportGenerator, get_cached_report
from eod_reports import get_eod_history, EODReportGenerator
from datetime import datetime
import pytz
import threading

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nilay_market_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

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

def daily_tasks():
    """Fetches announcements and runs EOD cleanup."""
    logger.info("Running daily maintenance tasks...")
    ann_fetcher.fetch_latest()
    
    # Generate EOD for dashboard results
    stocks = get_dashboard_cache()
    if stocks:
        eod_gen.generate_daily_report(stocks)

# Scheduler
scheduler = BackgroundScheduler(timezone=IST)
# Run scanner every 5 mins during market hours
scheduler.add_job(func=scheduled_scan, trigger="interval", minutes=5)
# Fetch announcements every 6 hours
scheduler.add_job(func=ann_fetcher.fetch_latest, trigger="interval", hours=6)
scheduler.start()

# Initial Startup Scan
def startup_scan():
    logger.info("Starting initial market scan...")
    scheduled_scan()

threading.Thread(target=startup_scan, daemon=True).start()
# Run EOD report at 3:45 PM IST
scheduler.add_job(func=daily_tasks, trigger='cron', hour=15, minute=45)
scheduler.start()

# --- ROUTES ---

@app.route('/')
def index():
    """Homepage - Dashboard."""
    stocks = get_dashboard_cache()
    return render_template('index.html', stocks=stocks)

@app.route('/api/dashboard')
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
    """Manual trigger for scanners."""
    scan_type = request.args.get('type', 'swing') # 'swing', 'fno', 'vcp', 'smc', 'chartink'
    results = scanner.run_scan() # Runs all, updates cache
    
    # Filter for the requested type to return to frontend
    filtered = [r for r in results if r['scan_type'] == scan_type]
    
    return jsonify({
        "status": "Success", 
        "count": len(filtered),
        "results": filtered
    })

# --- SOCKET EVENTS ---

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('status', {'data': 'Connected to Trade with Nilay Terminal'})

@app.route('/api/scan-status')
def scan_status():
    return jsonify({"is_scanning": scanner.is_scanning})

if __name__ == '__main__':
    # For local testing, use socketio.run
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
