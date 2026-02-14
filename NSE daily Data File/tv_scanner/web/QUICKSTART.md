# Phase 8: Web Dashboard - Quick Start

## 30-Second Overview

A simple Flask web dashboard that displays:
- 📊 Trading signals table with rankings
- 🎯 Order Block zones
- 📈 Signal statistics
- ⏰ Last update time
- 🔄 Auto-refresh every 30 seconds

**URL**: `http://localhost:5000`

## Get Started

### 1. Install Flask
```bash
pip install Flask pandas
```

### 2. Start Dashboard
```bash
cd web
python app.py
```

### 3. Open Browser
Navigate to: `http://localhost:5000`

## Features

### Main Dashboard Page
```
┌─────────────────────────────────────────────────────┐
│ NSE Scanner Dashboard                  Refresh │ 2pm │
├─────────────────────────────────────────────────────┤
│ Total: 15  | High Score: 4  | Avg: 5.2  | OB: 6    │
├─────────────────────────────────────────────────────┤
│ Today's Signals                                     │
├─────────────────────────────────────────────────────┤
│ Rank │ Symbol    │ Score │ OB │ Swing │ Price     │
├─────────────────────────────────────────────────────┤
│  1   │ RELIANCE  │  10.0 │ ✓ │  ✓   │ ₹2850.50  │
│  2   │ TCS       │   7.0 │ ✓ │  ✗   │ ₹3650.75  │
│  3   │ INFY      │   5.0 │ ✗ │  ✓   │ ₹1850.25  │
└─────────────────────────────────────────────────────┘
```

### What You See

1. **Statistics Cards**
   - Total signals detected
   - High-quality signals (score ≥ 7)
   - Average score
   - Order blocks tapped

2. **Signals Table**
   - Rank by score
   - Symbol
   - Total score (color-coded)
   - Signal indicators (✓/✗)
   - Price and change %

3. **OB Zones Table**
   - Symbol
   - Zone levels (Low/High)
   - Tap status
   - Strength rating

4. **Signal Breakdown**
   - Count of each signal type
   - Visual cards

5. **Update Time**
   - When data was last updated
   - Auto-updates every 30s

## Common Tasks

### Refresh Data Manually
Click the **🔄 Refresh** button in top-right corner

### Interpret Scores
- **🟢 10-14**: Excellent (Take position)
- **🔵 7-9**: Good (Watch closely)
- **🟡 4-6**: Moderate (Consider with caution)
- **🔴 0-3**: Low (Skip)

### Export Signals
1. Run scanner with ranking:
   ```bash
   python main.py --rank --top-n 10
   ```
2. Open dashboard
3. Signals auto-populated from `results.csv`

### Check Last Update
- Shown in header: "Last Update: 14:30:45"
- Auto-updates from API every 30 seconds

## API Endpoints

Use these for integrations:

### Get Signals (JSON)
```bash
curl http://localhost:5000/api/signals
```

### Get OB Zones (JSON)
```bash
curl http://localhost:5000/api/ob-zones
```

### Get Statistics (JSON)
```bash
curl http://localhost:5000/api/stats
```

### Manual Refresh
```bash
curl -X POST http://localhost:5000/refresh
```

## Troubleshooting

### Dashboard Shows "No signals"
1. Run scanner first:
   ```bash
   python main.py --rank --top-n 10
   ```
2. Check `results.csv` exists
3. Click "Refresh" button

### Can't access dashboard
1. Check if running: `http://localhost:5000`
2. Port 5000 busy? Change in `app.py`:
   ```python
   app.run(port=8000)
   ```

### Styling looks broken
1. Hard refresh: Ctrl+Shift+R
2. Clear cache

### Data not updating
1. Click "Refresh" button
2. Auto-refresh happens every 30 seconds
3. Check if scanner is running

## Keyboard Shortcuts

- `Ctrl+Shift+R`: Hard refresh (clear cache)
- `F5`: Regular refresh

## Mobile Access

Dashboard is responsive - works on:
- Desktop browsers
- Tablets
- Mobile phones

Use responsive breakpoints for different screen sizes.

## Production Deployment

For production, modify `app.py`:

```python
app.run(
    host='0.0.0.0',        # Accept external connections
    port=5000,
    debug=False,            # Disable debug
    use_reloader=False,
)
```

Then use production server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## File Structure

```
web/
├── app.py                 # ← Start here
├── requirements.txt       # Flask dependencies
├── templates/
│   ├── index.html        # Dashboard page
│   ├── 404.html          # Error pages
│   └── 500.html
└── static/
    └── style.css         # Clean styling
```

## Next Steps

1. ✅ Run scanner to generate signals
2. ✅ Start dashboard
3. ✅ View signals in browser
4. ✅ Check rankings
5. ✅ Monitor OB zones
6. ✅ Take trades based on top signals!

## Need Help?

See full documentation in `README.md`

---

**Phase 8**: ✅ Complete
**Framework**: Flask
**Port**: 5000
**URL**: http://localhost:5000
