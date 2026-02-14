# Signal Ranking System - Quick Start Guide

## 30-Second Overview

The ranking system scores stocks 0-14 based on detected signals:
- **Order Block Tap**: 5 points
- **Swing Condition**: 3 points  
- **Doji Pattern**: 2 points
- **Consolidation**: 2 points
- **Volume Spike**: 2 points

Higher total score = stronger trade setup.

## Install & Test

```bash
# Run test suite to verify installation
python test_ranking.py

# See practical examples
python examples_ranking.py
```

## 5-Minute Usage

### 1. Basic Ranking (Scan + Rank)

```python
from core.ranking import SignalRankingEngine

# Create engine
engine = SignalRankingEngine()

# Score a stock with multiple signals
signal = engine.calculate_rank(
    symbol='RELIANCE.NS',
    metrics={
        'close': 2850.50,
        'pct_change': 1.25,
        'volume': 1500000
    },
    ob_tapped=True,
    swing_valid=True,
    doji_detected=True,
    consolidation_detected=False,
    volume_spiked=False
)

# Score = 5 + 3 + 2 = 10 points ⭐
print(f"{signal.symbol}: {signal.total_score}")
```

### 2. Rank Multiple Stocks

```python
# Create list of signals
signals = [
    engine.calculate_rank('STOCK_A.NS', metrics1, ob_tapped=True, swing_valid=True),
    engine.calculate_rank('STOCK_B.NS', metrics2, doji_detected=True),
    engine.calculate_rank('STOCK_C.NS', metrics3, volume_spiked=True),
]

# Sort by score (highest first)
ranked = engine.rank_signals(signals, top_n=10)

# Print results
for idx, sig in enumerate(ranked, 1):
    print(f"{idx}. {sig.symbol}: {sig.total_score} points")
```

### 3. Get Top N Stocks

```python
# Get top 5 stocks
top_5 = engine.rank_signals(all_signals, top_n=5)

# Get as dataframe
df = engine.to_dataframe(top_5)
df.to_csv('top_stocks.csv')

# Print formatted report
print(engine.format_ranking_report(top_5))
```

### 4. Filter by Score Threshold

```python
# Get stocks with score >= 7
strong_signals = [s for s in all_signals if s.total_score >= 7]
ranked = engine.rank_signals(strong_signals)

print(f"Found {len(ranked)} stocks with strong signals")
```

## CLI Quick Start

```bash
# Scan with ranking enabled
python main.py --rank --top-n 10

# Scan with specific signals
python main.py --rank --top-n 5 \
  --ob-symbols "RELIANCE.NS,TCS.NS" \
  --swing-symbols "INFY.NS" \
  --doji-symbols "WIPRO.NS"
```

## Signal Score Interpretation

| Score | Interpretation | Action |
|---|---|---|
| 0 | No signals | ❌ Pass |
| 1-2 | Very weak | ⚠️ Monitor |
| 3-5 | Weak to moderate | 🟡 Consider |
| 6-8 | Good | 🟢 Watch closely |
| 9-11 | Strong | 💪 High priority |
| 12-14 | Very strong | 🔥 Top tier |

## Common Patterns

### High Confidence Setup
**Score**: 8+ (OB tap + Swing)
```python
high_conf = [s for s in signals if s.ob_tapped and s.swing_valid]
```

### Multi-Signal Confirmation
**Score**: 7+ (3+ signals)
```python
multi = [s for s in signals if sum([
    s.ob_tapped, s.swing_valid, s.doji_detected,
    s.consolidation_detected, s.volume_spiked
]) >= 3]
```

### Quick Winners
**Score**: 5+ (Any combo)
```python
winners = [s for s in signals if s.total_score >= 5]
```

## Real-World Example

```python
from scanner import Scanner
from core.ranking import SignalRankingEngine

# Scan stocks
scanner = Scanner()
results_df = scanner.run_scan(['RELIANCE.NS', 'TCS.NS', 'INFY.NS'], max_workers=2)

# Rank with detected signals
ranked_df = scanner.rank_results(
    results_df,
    ob_tapped_symbols=['RELIANCE.NS'],        # Detected OB tap
    swing_valid_symbols=['TCS.NS', 'INFY.NS'], # Detected swing
    doji_symbols=['INFY.NS'],                  # Detected doji
    top_n=5                                    # Get top 5
)

# Display results
print(ranked_df)
#    Rank Symbol       Total_Score OB_Tap Swing Doji ...
# 0     1 INFY.NS      10          0      3     2   ...
# 1     2 RELIANCE.NS  5           5      0     0   ...
# 2     3 TCS.NS       3           0      3     0   ...
```

## Output Formats

### 1. Text Report
```
================================================================================
📊 SIGNAL RANKING REPORT
================================================================================
Rank  Symbol       Score   OB   Swing  Doji   Cons   Vol   Price      Chg%
────────────────────────────────────────────────────────────────────────────
1     RELIANCE.NS  10.0    ✓    ✓      ✓      ✗      ✗     ₹2850.50    +1.25%
2     TCS.NS       7.0     ✓    ✗      ✗      ✓      ✗     ₹3650.75    -0.75%
3     INFY.NS      5.0     ✗    ✓      ✗      ✗      ✓     ₹1850.25    +2.10%
================================================================================
```

### 2. DataFrame
```
   Rank       Symbol  Total_Score  OB_Tap  Swing  Doji  ...
0     1  RELIANCE.NS          10.0       5      3     2  ...
1     2       TCS.NS           7.0       5      0     0  ...
2     3      INFY.NS           5.0       0      3     0  ...
```

### 3. CSV Export
```
Rank,Symbol,Total_Score,OB_Tap,Swing,Doji,Consolidation,Volume_Spike,Close_Price,Pct_Change
1,RELIANCE.NS,10.0,5,3,2,0,0,2850.50,1.25
2,TCS.NS,7.0,5,0,0,2,0,3650.75,-0.75
3,INFY.NS,5.0,0,3,0,0,2,1850.25,2.10
```

## Troubleshooting

### No results?
- Check if scan found any matches: `len(results_df) > 0`
- Verify symbols have signals detected
- Try lowering score threshold

### Incorrect scores?
- Verify signal flags are set correctly
- Check metrics dictionary has required fields
- Run `test_ranking.py` to validate engine

### Missing columns in output?
- Use `to_dataframe()` for complete columns
- Check if signals were provided to `rank_results()`

## Tips & Tricks

1. **Track trends**: Monitor average score over time
2. **Weekly reports**: Generate weekly top 10 reports
3. **Alert thresholds**: Set alerts for score >= 10
4. **Volume confirmation**: Combine with volume analysis
5. **Price action**: Cross-verify with candlestick patterns

## Integration Checklist

- [ ] Import `SignalRankingEngine` in your module
- [ ] Create engine instance
- [ ] Collect signals from all detection engines (OB, PA, Swing)
- [ ] Calculate ranks for each stock
- [ ] Sort and filter results
- [ ] Export or display output
- [ ] Monitor performance metrics

## Next: Advanced Features

- Weighted scoring based on market conditions
- Dynamic score adjustments for volatility
- Backtesting framework integration
- Performance tracking dashboard
- Machine learning optimization

---

**Need Help?** See `RANKING.md` for comprehensive documentation.
