# Phase 7: Signal Ranking System

## Overview
The Signal Ranking System assigns numeric scores to stocks based on detected trading signals, enabling prioritization of the most promising opportunities. This system aggregates signals from multiple analysis engines and returns ranked stocks sorted by total score.

## Scoring System

### Points per Signal
| Signal Type | Points | Description |
|---|---|---|
| **Order Block Tap** | 5 | Stock price tapped an identified order block |
| **Swing Condition** | 3 | Valid swing trading setup detected |
| **Doji Pattern** | 2 | Doji candlestick pattern identified |
| **Consolidation** | 2 | Price consolidation/range-bound movement |
| **Volume Spike** | 2 | Unusual volume increase detected |

### Maximum Score: 14 points
(All five signals present: 5+3+2+2+2=14)

## Architecture

### Core Components

#### 1. **RankedSignal** (Dataclass)
```python
@dataclass
class RankedSignal:
    symbol: str                        # Stock symbol
    total_score: float                 # Sum of all signal scores
    
    # Individual signal scores
    ob_tap_score: float               # Order block tap score
    swing_condition_score: float      # Swing condition score
    doji_score: float                 # Doji pattern score
    consolidation_score: float        # Consolidation score
    volume_spike_score: float         # Volume spike score
    
    # Stock metrics
    close_price: float                # Current close price
    pct_change: float                 # Percentage change
    volume: float                     # Trading volume
    
    # Signal flags
    ob_tapped: bool                   # Whether OB was tapped
    swing_valid: bool                 # Whether swing is valid
    doji_detected: bool               # Whether doji detected
    consolidation_detected: bool      # Whether consolidation detected
    volume_spiked: bool               # Whether volume spiked
```

#### 2. **SignalRankingEngine** (Main Engine)
Core ranking functionality with methods:

| Method | Purpose |
|---|---|
| `calculate_rank()` | Compute score for a stock based on signals |
| `rank_signals()` | Sort signals by score (optionally get top N) |
| `to_dataframe()` | Convert signals to pandas DataFrame |
| `format_ranking_report()` | Generate formatted text report |
| `get_summary_stats()` | Compute aggregate statistics |

## Usage Examples

### Basic Usage

```python
from core.ranking import SignalRankingEngine

# Initialize engine
engine = SignalRankingEngine()

# Calculate score for a stock
ranked_signal = engine.calculate_rank(
    symbol='RELIANCE.NS',
    metrics={'close': 2850.50, 'pct_change': 1.25, 'volume': 1500000},
    ob_tapped=True,
    swing_valid=True,
    doji_detected=True,
    consolidation_detected=False,
    volume_spiked=False
)
# Result: Total Score = 5 + 3 + 2 = 10
```

### Rank Multiple Stocks

```python
ranked_signals = [
    engine.calculate_rank('STOCK_A.NS', metrics1, ob_tapped=True, swing_valid=True),
    engine.calculate_rank('STOCK_B.NS', metrics2, doji_detected=True),
    engine.calculate_rank('STOCK_C.NS', metrics3, volume_spiked=True),
]

# Sort by score (highest first)
sorted_signals = engine.rank_signals(ranked_signals)

# Get top 3
top_3 = engine.rank_signals(ranked_signals, top_n=3)
```

### Convert to DataFrame

```python
df = engine.to_dataframe(sorted_signals)
# Columns: Rank, Symbol, Total_Score, OB_Tap, Swing, Doji, 
#          Consolidation, Volume_Spike, Close_Price, Pct_Change, etc.

df.to_csv('ranked_signals.csv', index=False)
```

### Generate Report

```python
report = engine.format_ranking_report(top_signals)
print(report)

# Output:
# ================================================================================
# 📊 SIGNAL RANKING REPORT
# ================================================================================
# Rank  Symbol       Score   OB   Swing  Doji   Cons   Vol   Price      Chg%
# ────────────────────────────────────────────────────────────────────────────
# 1     RELIANCE.NS  10.0    ✓    ✓      ✓      ✗      ✗     ₹2850.50    +1.25%
# 2     TCS.NS       7.0     ✓    ✗      ✗      ✓      ✗     ₹3650.75    -0.75%
# 3     INFY.NS      5.0     ✗    ✓      ✗      ✗      ✓     ₹1850.25    +2.10%
# ================================================================================
```

### Summary Statistics

```python
stats = engine.get_summary_stats(ranked_signals)

# Output:
# {
#     'total_signals': 10,
#     'avg_score': 5.2,
#     'max_score': 14.0,
#     'min_score': 0.0,
#     'std_score': 3.1,
#     'ob_tapped_count': 5,
#     'swing_valid_count': 6,
#     'doji_count': 4,
#     'consolidation_count': 3,
#     'volume_spike_count': 2,
# }
```

## Integration with Scanner

### Updated Scanner Class

```python
from scanner import Scanner

scanner = Scanner(username='tv_user', password='tv_pass')

# Run scan
results_df = scanner.run_scan(symbols, max_workers=5)

# Rank results
ranked_df = scanner.rank_results(
    results_df,
    ob_tapped_symbols=['RELIANCE.NS', 'TCS.NS'],
    swing_valid_symbols=['INFY.NS', 'HDFCBANK.NS'],
    doji_symbols=['WIPRO.NS'],
    consolidation_symbols=['MARUTI.NS'],
    volume_spike_symbols=['RELIANCE.NS'],
    top_n=10  # Get top 10 stocks
)

print(ranked_df)
```

### CLI Usage

```bash
# Basic scan
python main.py

# Scan with ranking
python main.py --rank --top-n 10

# Scan with signal specifications
python main.py --rank \
  --top-n 5 \
  --ob-symbols "RELIANCE.NS,TCS.NS" \
  --swing-symbols "INFY.NS,HDFCBANK.NS" \
  --doji-symbols "WIPRO.NS" \
  --cons-symbols "MARUTI.NS" \
  --vol-symbols "RELIANCE.NS,HDFCBANK.NS"
```

## Practical Strategies

### Strategy 1: High Confidence Signals
Get stocks with OB tap + swing condition:
```python
high_confidence = [s for s in signals if s.ob_tapped and s.swing_valid]
filtered = engine.rank_signals(high_confidence, top_n=5)
```
**Score Range**: 8-14 (5+3 minimum to max)

### Strategy 2: Multi-Signal Confirmation
Get stocks with 3+ different signals:
```python
multi_signal = [
    s for s in signals if sum([
        s.ob_tapped, s.swing_valid, s.doji_detected,
        s.consolidation_detected, s.volume_spiked
    ]) >= 3
]
filtered = engine.rank_signals(multi_signal, top_n=10)
```

### Strategy 3: Minimum Threshold
Filter by score threshold:
```python
min_threshold = 5
above_threshold = [s for s in signals if s.total_score >= min_threshold]
filtered = engine.rank_signals(above_threshold)
```

### Strategy 4: Signal-Specific Focus
Focus on specific signal type:
```python
# Only order block taps
ob_focus = [s for s in signals if s.ob_tapped]
filtered = engine.rank_signals(ob_focus, top_n=5)

# Only consolidation + volume spike
cons_vol = [s for s in signals if s.consolidation_detected and s.volume_spiked]
filtered = engine.rank_signals(cons_vol)
```

## Testing

### Run Test Suite
```bash
python test_ranking.py
```

**Test Coverage**:
- ✅ Individual signal scoring
- ✅ Combined signal scoring
- ✅ Ranking and sorting
- ✅ Top N filtering
- ✅ DataFrame conversion
- ✅ Summary statistics
- ✅ Report formatting

### Run Usage Examples
```bash
python examples_ranking.py
```

## Data Flow

```
Scan Results
    ↓
Signal Detection Engines (OB, Swing, PA, etc.)
    ↓
Signal Ranking Engine
    ├── Calculate Score for Each Stock
    ├── Apply Signal Weights
    └── Aggregate Total Score
    ↓
Rank & Sort
    ├── Sort by Total Score (Descending)
    ├── Filter Top N
    └── Generate Report
    ↓
Output
    ├── Ranked DataFrame
    ├── Text Report
    ├── Summary Statistics
    └── CSV Export
```

## Performance Metrics

### Scoring Distribution Example
For 100 scanned stocks with mixed signals:

| Score Range | Count | % | Interpretation |
|---|---|---|---|
| 0 | 40 | 40% | No signals |
| 1-3 | 25 | 25% | Single weak signal |
| 4-6 | 20 | 20% | Moderate signals |
| 7-10 | 12 | 12% | Strong signals |
| 11-14 | 3 | 3% | Very strong signals |

## Integration Points

### Phase 6 (Price Action Engine)
```python
# Get PA signals and combine with ranking
pa_signals = price_action_engine.detect_patterns(ohlcv_data)
for symbol in pa_signals:
    ranked = engine.calculate_rank(
        symbol,
        metrics,
        doji_detected=pa_signals[symbol]['doji'],
        consolidation_detected=pa_signals[symbol]['consolidation']
    )
```

### Phase 5 (Order Block Engine)
```python
# Get OB data and update ranking
ob_taps = orderblock_engine.detect_taps(ohlcv_data)
for symbol in ob_taps:
    ranked = engine.calculate_rank(
        symbol,
        metrics,
        ob_tapped=True
    )
```

### Phase 4 (Swing Scanner)
```python
# Get swing signals
swing_results = swing_scanner.scan(symbols)
for symbol in swing_results:
    ranked = engine.calculate_rank(
        symbol,
        metrics,
        swing_valid=True
    )
```

## Best Practices

1. **Use Multiple Signals**: Stocks with more signal confirmations are generally more reliable
2. **Monitor Score Distribution**: Track avg/max/min scores to identify market conditions
3. **Top N Focus**: Focus on top 5-10 ranked stocks rather than all matches
4. **Combine with Risk Management**: High score doesn't guarantee profit; always use stop losses
5. **Rebalance Regularly**: Update rankings as new signals emerge throughout the day
6. **Log Signal Combinations**: Track which signal combinations work best for your strategy

## Next Steps (Phase 8+)

- [ ] Add backtesting framework to validate signal accuracy
- [ ] Implement dynamic scoring weights based on market conditions
- [ ] Add volatility adjustment (higher scores for stable moves)
- [ ] Create alert system for top-ranked stocks
- [ ] Build performance analytics dashboard
- [ ] Add machine learning for signal weight optimization

## Files

| File | Purpose |
|---|---|
| `core/ranking.py` | SignalRankingEngine implementation |
| `scanner.py` | Updated with rank_results() method |
| `main.py` | Updated with CLI ranking options |
| `test_ranking.py` | Comprehensive test suite |
| `examples_ranking.py` | Usage examples and patterns |
| `RANKING.md` | This documentation |

---

**Phase 7 Status**: ✅ Complete and Tested
**Last Updated**: January 28, 2026
