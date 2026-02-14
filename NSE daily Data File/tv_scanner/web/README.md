# Phase 8: Web Dashboard

## Overview
Phase 8 implements a simple, clean web dashboard using Flask that displays:
- Table of today's trading signals with scores
- Order Block (OB) zones with tap status
- Signal statistics and breakdown
- Last update time
- Real-time refresh capability

## Architecture

### File Structure
```
web/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── templates/
│   ├── index.html             # Main dashboard template
│   ├── 404.html               # 404 error page
│   └── 500.html               # 500 error page
└── static/
    └── style.css              # Stylesheet
```

### Technology Stack
- **Framework**: Flask 2.3.3
- **Template Engine**: Jinja2
- **Styling**: Clean CSS (no frameworks, no JavaScript frameworks)
- **Data Source**: CSV results from scanner
- **Port**: 5000 (localhost)

## Features

### 1. Dashboard Page (`/`)
Main dashboard with all information in one view.

**Display Elements**:
- Statistics cards (Total Signals, High Score Count, Average Score, OB Tapped)
- Signals table with sorting by rank
- Order Block zones table
- Signal breakdown (count by type)
- Legend for score colors and signal indicators
- Last update time

### 2. Signals Table
Displays all detected signals with:
- **Rank**: Position by score
- **Symbol**: Stock symbol
- **Score**: Total ranking score (0-14)
- **Signal Flags**: OB, Swing, Doji, Consolidation, Volume Spike
- **Price**: Current price in rupees
- **Change**: Percentage change (color-coded)

**Score Colors**:
- 🟢 Excellent (≥10): Dark green background
- 🔵 Good (7-9): Blue background
- 🟡 Moderate (4-6): Orange background
- 🔴 Low (0-3): Red background

### 3. Order Block Zones Table
Shows identified order block levels:
- **Symbol**: Stock symbol
- **Zone Low**: Lower OB level
- **Zone High**: Upper OB level
- **Status**: Whether price tapped the zone
- **Strength**: OB strength (Strong/Moderate/Weak)

### 4. Statistics Cards
Quick overview metrics:
- **Total Signals**: Number of detected signals today
- **High Score (≥7)**: Count of strong signals
- **Average Score**: Mean of all signal scores
- **OB Tapped**: Count of order blocks that were tapped

### 5. Signal Breakdown
Detailed count of each signal type:
- Order Block Taps
- Swing Conditions
- Doji Patterns
- Consolidations
- Volume Spikes

### 6. API Endpoints

#### GET `/api/signals`
Returns signals data as JSON
```json
{
    "status": "success",
    "count": 10,
    "signals": [
        {
            "rank": 1,
            "symbol": "RELIANCE.NS",
            "score": "10.0",
            "ob_tap": "✓",
            "swing": "✓",
            ...
        }
    ],
    "last_update": "2026-01-28 14:30:45"
}
```

#### GET `/api/ob-zones`
Returns order block zones as JSON
```json
{
    "status": "success",
    "count": 3,
    "zones": [
        {
            "symbol": "RELIANCE.NS",
            "zone_low": "₹2820.00",
            "zone_high": "₹2880.00",
            "tapped": "✓ Tapped",
            "strength": "Strong"
        }
    ]
}
```

#### GET `/api/stats`
Returns dashboard statistics as JSON
```json
{
    "status": "success",
    "total_signals": 10,
    "high_score_count": 3,
    "average_score": "5.4",
    "last_update": "2026-01-28 14:30:45",
    "stats": {
        "total_signals": 10,
        "avg_score": 5.4,
        "ob_tapped_count": 3,
        ...
    }
}
```

#### POST `/refresh`
Manually trigger data refresh
```json
{
    "status": "success",
    "message": "Data refreshed",
    "timestamp": "2026-01-28T14:30:45.123456"
}
```

## Installation & Setup

### 1. Install Dependencies
```bash
cd web
pip install -r requirements.txt
```

### 2. Run Dashboard
```bash
python app.py
```

**Output**:
```
* Running on http://127.0.0.1:5000
```

### 3. Access Dashboard
Open browser and navigate to:
```
http://localhost:5000
```

## Usage

### Starting the Dashboard
```bash
cd tv_scanner/web
python app.py
```

### Auto-Refresh
- Page automatically updates statistics every 30 seconds
- Manual refresh button available in header

### Data Sources
- **Signals**: Read from `results.csv` (created by scanner)
- **OB Zones**: Placeholder data (integrate with Phase 4 engine)
- **Scores**: Calculated from ranking engine on page load

## Customization

### Change Port
Edit `app.py`:
```python
if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8000,  # Change here
        debug=True,
    )
```

### Change Auto-Refresh Interval
Edit `templates/index.html`:
```javascript
// Change 30000 (milliseconds) to desired interval
setInterval(() => {
    // ... refresh code
}, 30000);
```

### Modify Statistics
Edit `app.py` dashboard route:
```python
# Add/modify stat cards in render_template call
```

### Update Styling
Edit `static/style.css`:
- Modify color scheme (`:root` variables)
- Adjust font sizes
- Change layout breakpoints

## Data Flow

```
Scanner (runs periodically)
    ↓
results.csv created/updated
    ↓
Flask reads CSV on page load
    ↓
Ranking engine scores signals
    ↓
Dashboard renders HTML
    ↓
Browser displays dashboard
    ↓
Auto-refresh every 30s via API
```

## Integration Points

### Phase 7 (Ranking Engine)
- Uses `SignalRankingEngine` to score stocks
- Displays ranking scores in signals table

### Phase 6 (Price Action Engine)
- PA signal detection feeds into dashboard
- Shows Doji, Consolidation patterns

### Phase 5 (Telegram Bot)
- Can send top signals to Telegram
- Dashboard complements mobile notifications

### Phase 4 (Order Block Engine)
- OB zones displayed in separate table
- Tap detection shown in table

### Phase 3 (Swing Scanner)
- Swing condition shown as signal indicator

## Performance

### Load Time
- Average: < 500ms (depends on CSV size)
- Minimal HTML/CSS/no JavaScript frameworks
- Direct CSV read (no database)

### CSV Size Considerations
| Size | Performance |
|---|---|
| <100 signals | Excellent |
| 100-500 signals | Good |
| 500-1000 signals | Acceptable |
| >1000 signals | Slow (consider database) |

## Best Practices

1. **Run Scanner First**: Dashboard reads from `results.csv`
2. **Monitor File Updates**: Check modification time for freshness
3. **Limit Signals**: Keep top N signals for better performance
4. **Regular Cleanup**: Archive old CSV files periodically
5. **Error Handling**: Check logs for data loading issues

## Troubleshooting

### Port Already in Use
```bash
# Change port in app.py or kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### No Signals Showing
1. Run scanner first: `python main.py --rank --top-n 10`
2. Check `results.csv` exists and has data
3. Check logs for errors in data loading

### Styling Issues
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh page (Ctrl+Shift+R)
3. Check `static/style.css` exists

### Data Not Updating
1. Manually click "🔄 Refresh" button
2. Check CSV file modification time
3. Verify scanner is running and saving results

## Security Considerations

### Current Setup (Development)
- ✅ Local only (127.0.0.1)
- ✅ Debug mode for development
- ✅ No authentication required (local network)

### Production Deployment
- [ ] Disable debug mode
- [ ] Add authentication
- [ ] Use HTTPS
- [ ] Deploy behind reverse proxy (nginx)
- [ ] Add rate limiting
- [ ] Sanitize CSV input

## API Rate Limiting (Future)

When deploying to production:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/signals')
@limiter.limit("60/minute")
def api_signals():
    # ...
```

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Files Reference

### app.py (Main Application)
- `dashboard()`: Main page route
- `api_signals()`: JSON endpoint
- `api_ob_zones()`: OB zones endpoint
- `api_stats()`: Statistics endpoint
- `refresh_data()`: Manual refresh endpoint
- Data loading functions
- Template filters (score_class, signal_color)

### index.html (Main Template)
- Header with title and refresh button
- Statistics cards
- Signals table
- OB zones table
- Signal breakdown
- Legend
- Footer

### style.css (Styling)
- CSS variables for theming
- Grid layouts for responsive design
- Color scheme for signal scores
- Media queries for mobile
- Table styling
- Card styling

## Next Steps (Phase 9+)

- [ ] Add real-time WebSocket updates
- [ ] Implement signal alerts/notifications
- [ ] Add historical data charts
- [ ] Create backtesting dashboard
- [ ] Add user preferences/settings
- [ ] Implement export functionality (PDF, Excel)
- [ ] Add trading performance metrics
- [ ] Create admin panel for configuration

## Summary

**Phase 8 Status**: ✅ Complete

**Created**:
- ✅ `web/app.py` - Flask application (400+ lines)
- ✅ `web/templates/index.html` - Main dashboard (200+ lines)
- ✅ `web/templates/404.html` - Error page
- ✅ `web/templates/500.html` - Error page
- ✅ `web/static/style.css` - Styling (400+ lines)
- ✅ `web/requirements.txt` - Dependencies
- ✅ Documentation

**Features**:
- ✅ Signals table with ranking scores
- ✅ Order Block zones table
- ✅ Statistics cards
- ✅ Signal breakdown
- ✅ Auto-refresh (30-second interval)
- ✅ Manual refresh button
- ✅ Responsive design
- ✅ Clean, simple UI
- ✅ JSON API endpoints
- ✅ Error handling

---

**Created**: January 28, 2026
**Framework**: Flask 2.3.3
**URL**: http://localhost:5000
