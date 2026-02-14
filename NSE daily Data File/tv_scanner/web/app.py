"""
Phase 8: Web Dashboard
Flask application for displaying trading signals, OB zones, scores, and update time.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ranking import SignalRankingEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Data paths
BASE_DIR = Path(__file__).parent.parent
RESULTS_CSV = BASE_DIR / 'results.csv'
SCANNER_RESULTS_DIR = BASE_DIR / 'scanner_results'

# Initialize ranking engine
ranking_engine = SignalRankingEngine()


def load_scan_results():
    """Load latest scan results from CSV"""
    if RESULTS_CSV.exists():
        try:
            df = pd.read_csv(RESULTS_CSV)
            return df
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def load_ob_zones():
    """Load order block zones data"""
    # TODO: Integrate with Phase 4 OrderBlock Engine
    # For now, return placeholder data
    return {
        'RELIANCE.NS': {'zone_low': 2820, 'zone_high': 2880, 'tapped': True, 'strength': 'Strong'},
        'TCS.NS': {'zone_low': 3600, 'zone_high': 3700, 'tapped': False, 'strength': 'Moderate'},
        'INFY.NS': {'zone_low': 1800, 'zone_high': 1900, 'tapped': True, 'strength': 'Weak'},
    }


def load_ranked_signals():
    """Load and rank signals from results"""
    df = load_scan_results()
    if df.empty:
        return []
    
    ranked_signals = []
    
    for _, row in df.iterrows():
        try:
            # Convert row to dict
            metrics = row.to_dict()
            
            # Simulate signal detection (would come from actual engines in production)
            signal = ranking_engine.calculate_rank(
                symbol=metrics.get('symbol', 'UNKNOWN'),
                metrics=metrics,
                ob_tapped=metrics.get('ob_tapped', False),
                swing_valid=metrics.get('swing_valid', False),
                doji_detected=metrics.get('doji_detected', False),
                consolidation_detected=metrics.get('consolidation_detected', False),
                volume_spiked=metrics.get('volume_spiked', False),
            )
            ranked_signals.append(signal)
        except Exception as e:
            logger.error(f"Error ranking signal: {e}")
            continue
    
    # Sort by score
    ranked_signals = ranking_engine.rank_signals(ranked_signals)
    return ranked_signals


def get_last_update_time():
    """Get last update time from scan results"""
    if RESULTS_CSV.exists():
        try:
            mtime = os.path.getmtime(RESULTS_CSV)
            return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error getting update time: {e}")
    return "Never"


def format_signal_data(ranked_signals):
    """Format signals for display"""
    signals_data = []
    
    for idx, sig in enumerate(ranked_signals, 1):
        signals_data.append({
            'rank': idx,
            'symbol': sig.symbol,
            'score': f"{sig.total_score:.1f}",
            'ob_tap': '✓' if sig.ob_tapped else '✗',
            'swing': '✓' if sig.swing_valid else '✗',
            'doji': '✓' if sig.doji_detected else '✗',
            'consolidation': '✓' if sig.consolidation_detected else '✗',
            'volume_spike': '✓' if sig.volume_spiked else '✗',
            'price': f"₹{sig.close_price:.2f}",
            'change': f"{sig.pct_change:+.2f}%",
        })
    
    return signals_data


def format_ob_data(ob_zones):
    """Format OB zone data for display"""
    ob_data = []
    
    for symbol, zone_info in ob_zones.items():
        ob_data.append({
            'symbol': symbol,
            'zone_low': f"₹{zone_info['zone_low']:.2f}",
            'zone_high': f"₹{zone_info['zone_high']:.2f}",
            'tapped': '✓ Tapped' if zone_info['tapped'] else '✗ Not Tapped',
            'strength': zone_info['strength'],
        })
    
    return ob_data


@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Load data
        ranked_signals = load_ranked_signals()
        ob_zones = load_ob_zones()
        last_update = get_last_update_time()
        
        # Format data for display
        signals_table = format_signal_data(ranked_signals)
        ob_table = format_ob_data(ob_zones)
        
        # Calculate stats
        total_signals = len(ranked_signals)
        high_score_count = sum(1 for s in ranked_signals if s.total_score >= 7)
        average_score = sum(s.total_score for s in ranked_signals) / len(ranked_signals) if ranked_signals else 0
        
        # Count signals
        signal_counts = ranking_engine.get_summary_stats(ranked_signals) if ranked_signals else {}
        
        return render_template(
            'index.html',
            signals_table=signals_table,
            ob_table=ob_table,
            last_update=last_update,
            total_signals=total_signals,
            high_score_count=high_score_count,
            average_score=f"{average_score:.1f}",
            signal_counts=signal_counts,
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template(
            'index.html',
            signals_table=[],
            ob_table=[],
            last_update="Error",
            total_signals=0,
            high_score_count=0,
            average_score="0.0",
            signal_counts={},
            error=str(e),
        ), 500


@app.route('/api/signals')
def api_signals():
    """API endpoint for signals data"""
    try:
        ranked_signals = load_ranked_signals()
        signals_table = format_signal_data(ranked_signals)
        
        return jsonify({
            'status': 'success',
            'count': len(signals_table),
            'signals': signals_table,
            'last_update': get_last_update_time(),
        })
    except Exception as e:
        logger.error(f"Error in API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), 500


@app.route('/api/ob-zones')
def api_ob_zones():
    """API endpoint for OB zones data"""
    try:
        ob_zones = load_ob_zones()
        ob_table = format_ob_data(ob_zones)
        
        return jsonify({
            'status': 'success',
            'count': len(ob_table),
            'zones': ob_table,
        })
    except Exception as e:
        logger.error(f"Error in API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), 500


@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        ranked_signals = load_ranked_signals()
        
        if ranked_signals:
            stats = ranking_engine.get_summary_stats(ranked_signals)
            average_score = stats.get('avg_score', 0)
            total = stats.get('total_signals', 0)
        else:
            stats = {}
            average_score = 0
            total = 0
        
        return jsonify({
            'status': 'success',
            'total_signals': total,
            'high_score_count': sum(1 for s in ranked_signals if s.total_score >= 7),
            'average_score': f"{average_score:.1f}",
            'last_update': get_last_update_time(),
            'stats': stats,
        })
    except Exception as e:
        logger.error(f"Error in API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), 500


@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Manually trigger data refresh"""
    try:
        logger.info("Manual refresh triggered")
        return jsonify({
            'status': 'success',
            'message': 'Data refreshed',
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error refreshing: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), 500


@app.template_filter('score_class')
def score_class(score):
    """Filter to determine CSS class based on score"""
    try:
        score_float = float(score)
        if score_float >= 10:
            return 'score-excellent'
        elif score_float >= 7:
            return 'score-good'
        elif score_float >= 4:
            return 'score-moderate'
        else:
            return 'score-low'
    except:
        return 'score-low'


@app.template_filter('signal_color')
def signal_color(tapped):
    """Filter to determine CSS class based on signal status"""
    return 'signal-active' if '✓' in str(tapped) else 'signal-inactive'


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return render_template('500.html', error=str(error)), 500


if __name__ == '__main__':
    logger.info("Starting NSE Scanner Web Dashboard...")
    logger.info(f"Results CSV path: {RESULTS_CSV}")
    logger.info(f"Serving on http://localhost:5000")
    
    # Run Flask app
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False,
    )
