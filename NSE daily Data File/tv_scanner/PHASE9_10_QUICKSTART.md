# Phase 9-10 Quick Start Guide

## Quick Reference

### Phase 9: Backtesting

#### Basic Usage
```python
from backtesting.backtest_engine import BacktestEngine

# Create engine
engine = BacktestEngine(slippage_percent=0.1)

# Create trade from signal
trade = engine.create_trade(
    symbol="INFY",
    entry_price=1500,
    entry_date=datetime.now(),
    ob_low=1450,
    risk_multiplier=2.0
)

# Simulate on price data
engine.simulate_trade(trade, ohlcv_df, lookback_bars=20)

# Get metrics
metrics = engine.calculate_metrics()
# {'win_rate': 65.0, 'total_pnl': 5000, 'max_drawdown': 2000, ...}

# Generate report
from backtesting.backtest_report import BacktestReportGenerator
gen = BacktestReportGenerator()
report = gen.generate_summary_report(metrics)
html = gen.generate_html_report(metrics, engine.get_trades_dataframe())
```

### Phase 10: ML Prediction

#### Training
```python
from ml.train_model import MLModelTrainer
from ml.train_model import create_sample_training_data

# Create sample data or use your own
signals_df, backtest_df = create_sample_training_data()

# Train model
trainer = MLModelTrainer(model_type='random_forest')
metrics = trainer.train(signals_df, backtest_df)

# Save model
trainer.save_model('ml/signal_model.pkl')
```

#### Prediction
```python
from ml.signal_predictor import SignalPredictorML

# Load model
model = SignalPredictorML.load_model('ml/signal_model.pkl')

# Single prediction
result = model.predict_single({
    'symbol': 'INFY',
    'score': 12,
    'ob_depth': 50,
})
print(f"Success probability: {result.probability*100:.1f}%")

# Batch prediction
results = model.predict(signals_df)
best = sorted(results, key=lambda r: r.probability, reverse=True)[0]
```

---

## File Locations

```
backtesting/
├── __init__.py
├── backtest_engine.py      (Trade simulation - 250 lines)
└── backtest_report.py      (Report generation - 200 lines)

ml/
├── __init__.py
├── signal_predictor.py     (ML model - 350 lines)
├── train_model.py          (Training - 200 lines)
└── signal_model.pkl        (Trained model - generated)

test_backtesting.py         (12 tests - 200 lines)
test_ml.py                  (11 tests - 250 lines)
examples_phase9_10.py       (Examples - 350 lines)
PHASE9_10_COMPLETE.md       (Documentation - 400 lines)
```

---

## Test Coverage

```
Phase 9 Tests (12 total):
  ✓ test_trade_creation
  ✓ test_risk_reward_ratio
  ✓ test_close_trade_with_target
  ✓ test_close_trade_with_sl
  ✓ test_create_trade
  ✓ test_simulate_trade_hit_target
  ✓ test_simulate_trade_hit_sl
  ✓ test_backtest_metrics
  ✓ test_generate_summary_report
  ✓ test_generate_html_report
  ✓ test_generate_json_report
  ✓ test_generate_statistics_summary

Phase 10 Tests (11 total):
  ✓ test_prepare_features
  ✓ test_model_training
  ✓ test_model_prediction
  ✓ test_predict_single
  ✓ test_save_and_load_model
  ✓ test_feature_importance
  ✓ test_training_summary
  ✓ test_trainer_initialization
  ✓ test_prepare_training_data
  ✓ test_trainer_model_training
  ✓ test_trainer_save_model
```

---

## Key Metrics Explained

### Backtesting
| Metric | Good Range | Interpretation |
|--------|-----------|-----------------|
| Win Rate | > 55% | Percentage of profitable trades |
| Profit Factor | > 1.5 | Gross profit / Gross loss |
| Max Drawdown | < 5% | Largest peak-to-trough decline |
| Avg Return | > 2% | Average profit per trade |
| Expectancy | > 0 | Expected profit per trade |

### ML Model
| Metric | Good Range | Interpretation |
|--------|-----------|-----------------|
| Accuracy | > 65% | Correct predictions / total |
| Precision | > 70% | Predicted wins that were correct |
| Recall | > 80% | Actual wins we predicted |
| F1 Score | > 0.75 | Harmonic mean of precision & recall |
| ROC AUC | > 0.70 | Ability to distinguish classes |

---

## Common Workflows

### Workflow 1: Evaluate Historical Signals
```python
# Step 1: Load historical signals
signals_df = pd.read_csv('signals.csv')

# Step 2: Backtest each signal
engine = BacktestEngine()
trades = engine.backtest_signals(signals_df, price_data, ob_data)

# Step 3: Analyze results
metrics = engine.calculate_metrics()
print(f"Win Rate: {metrics['win_rate']}%")
print(f"Total P&L: {metrics['total_pnl']}")
```

### Workflow 2: Train Predictive Model
```python
# Step 1: Collect signals & backtest results
signals_df = pd.read_csv('signals.csv')
backtest_df = pd.read_csv('backtest_results.csv')

# Step 2: Train ML model
trainer = MLModelTrainer()
trainer.train(signals_df, backtest_df)
trainer.save_model('signal_model.pkl')

# Step 3: Evaluate model
print(trainer.get_summary())
```

### Workflow 3: Predict on New Signals
```python
# Step 1: Load trained model
model = SignalPredictorML.load_model('signal_model.pkl')

# Step 2: Get new signals
new_signals = detect_signals(price_data)

# Step 3: Predict
predictions = model.predict(new_signals)

# Step 4: Filter high-confidence
high_prob = [p for p in predictions if p.probability > 0.7]
print(f"High probability signals: {len(high_prob)}")
```

---

## Performance Tips

### Backtesting
- Use realistic slippage (0.1-0.5%)
- Adjust lookback_bars based on strategy (20 is default)
- Consider multiple risk multipliers (1.5R, 2R, 3R)

### ML Training
- Use at least 50-100 labeled samples
- Balance class distribution (50/50 if possible)
- Try both RandomForest and GradientBoosting
- Adjust test_size (0.2 is default = 80% train, 20% test)

### Prediction
- All features should be normalized (StandardScaler used internally)
- Missing features are zero-padded automatically
- Higher probability = more confidence

---

## Troubleshooting

### Error: "X has N features, but StandardScaler expecting M"
**Solution:** Ensure all signals have the same features when predicting
```python
# Good: All required features present
result = model.predict_single({
    'symbol': 'INFY',
    'score': 12,
    'ob_depth': 50,
    'volume_ratio': 1.5,
    'is_doji': 1,
    'is_swing': 0,
    # ... all expected features
})
```

### Error: "Model must be trained before prediction"
**Solution:** Train the model first
```python
model = SignalPredictorML()
model.train(training_data, labels)  # Must call this first
results = model.predict(test_data)
```

### Poor Model Performance
**Solution:** Check data quality
1. Ensure backtest labels (WIN/LOSS) are accurate
2. Remove outliers from signals
3. Verify feature normalization
4. Try different model_type ('gradient_boosting')

---

## Dependencies

```bash
# Required
pip install pandas numpy scikit-learn

# Optional (for enhanced features)
pip install matplotlib plotly jupyter
```

---

## Examples

See `examples_phase9_10.py` for complete working examples:

1. **Example 1**: Basic backtesting workflow
2. **Example 2**: ML training and prediction
3. **Example 3**: Combined backtest + ML pipeline
4. **Example 4**: Model persistence (save/load)

Run with:
```bash
python examples_phase9_10.py
```

---

## Next Steps

- Integrate with Phase 8 web dashboard
- Add result visualization to HTML reports
- Implement portfolio-level backtesting
- Create hyperparameter optimization
- Add walk-forward validation

---

## Support & Documentation

- Full API docs: See docstrings in source files
- Examples: `examples_phase9_10.py`
- Tests: `test_backtesting.py`, `test_ml.py`
- Architecture: `PHASE9_10_COMPLETE.md`

---

**Phase 9-10 Status: ✅ COMPLETE**

All components implemented, tested, and documented.
