"""
Phase 9-10 Complete Example
Demonstrates full backtesting and ML prediction workflow.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adjust path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtesting.backtest_engine import BacktestEngine, Trade
from backtesting.backtest_report import BacktestReportGenerator
from ml.train_model import MLModelTrainer, create_sample_training_data
from ml.signal_predictor import SignalPredictorML


def generate_sample_signals(n_signals=50):
    """Generate sample signals with realistic characteristics"""
    np.random.seed(42)
    
    signals = []
    symbols = ['INFY', 'TCS', 'HDFC', 'RELIANCE', 'SBIN', 'ITC', 'WIPRO', 'LT']
    
    for i in range(n_signals):
        entry_price = np.random.uniform(100, 1000)
        signal = {
            'symbol': symbols[i % len(symbols)],
            'entry_price': entry_price,
            'close': entry_price + np.random.uniform(-10, 10),
            'ob_low': entry_price - np.random.uniform(30, 100),
            'ob_high': entry_price + np.random.uniform(30, 100),
            'volume': np.random.uniform(1000000, 10000000),
            'score': np.random.randint(5, 14),
            'ob_depth': np.random.uniform(10, 100),
            'volume_ratio': np.random.uniform(0.8, 2.0),
            'is_doji': np.random.randint(0, 2),
            'is_swing': np.random.randint(0, 2),
            'is_consolidation': np.random.randint(0, 2),
            'is_ob_tap': np.random.randint(0, 2),
            'entry_date': datetime.now() - timedelta(days=i),
        }
        signals.append(signal)
    
    return pd.DataFrame(signals)


def generate_sample_ohlcv(symbol, n_bars=20):
    """Generate sample OHLCV data for a symbol"""
    np.random.seed(hash(symbol) % 2**32)
    
    dates = pd.date_range(end=datetime.now(), periods=n_bars, freq='D')
    base_price = np.random.uniform(100, 1000)
    
    data = []
    for i, date in enumerate(dates):
        open_price = base_price + np.random.uniform(-5, 5)
        close = base_price + np.random.uniform(-5, 5)
        high = max(open_price, close) + np.random.uniform(0, 10)
        low = min(open_price, close) - np.random.uniform(0, 10)
        volume = np.random.uniform(1000000, 10000000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        })
        base_price = close
    
    df = pd.DataFrame(data)
    df.index = dates
    return df


def example_1_basic_backtesting():
    """Example 1: Basic backtesting workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 1: BASIC BACKTESTING")
    print("="*70)
    
    # Generate sample signals
    print("\n1. Generating sample signals...")
    signals = generate_sample_signals(n_signals=20)
    print(f"   Generated {len(signals)} signals")
    print(f"   Symbols: {signals['symbol'].unique().tolist()}")
    
    # Create backtesting engine
    print("\n2. Creating backtesting engine...")
    engine = BacktestEngine(slippage_percent=0.1)
    
    # Prepare price data
    print("\n3. Generating price data...")
    price_data = {}
    for symbol in signals['symbol'].unique():
        price_data[symbol] = generate_sample_ohlcv(symbol, n_bars=20)
    print(f"   Generated OHLCV data for {len(price_data)} symbols")
    
    # Prepare OB data
    print("\n4. Preparing OB data...")
    ob_data = {}
    for _, signal in signals.iterrows():
        ob_data[signal['symbol']] = {
            'low': signal['ob_low'],
            'high': signal['ob_high'],
        }
    
    # Backtest signals
    print("\n5. Running backtest simulation...")
    trades = engine.backtest_signals(signals, price_data, ob_data)
    print(f"   Executed {len(trades)} trades")
    
    # Calculate metrics
    print("\n6. Calculating metrics...")
    metrics = engine.calculate_metrics()
    
    print("\n7. BACKTEST RESULTS:")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Total P&L: {metrics['total_pnl']:.2f}")
    print(f"   Avg Return: {metrics['avg_return_percent']:.2f}%")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"   Expectancy: {metrics['expectancy']:.2f}")
    
    # Generate reports
    print("\n8. Generating reports...")
    generator = BacktestReportGenerator()
    
    text_report = generator.generate_summary_report(metrics)
    print("\n" + text_report)
    
    # Get trades DataFrame
    trades_df = engine.get_trades_dataframe()
    print(f"\n9. Top winning trades:")
    wins = trades_df[trades_df['result'] == 'WIN'].nlargest(3, 'pnl')[
        ['symbol', 'entry_price', 'exit_price', 'pnl', 'result']
    ]
    print(wins.to_string())


def example_2_ml_training_and_prediction():
    """Example 2: ML model training and prediction"""
    print("\n" + "="*70)
    print("EXAMPLE 2: ML TRAINING AND PREDICTION")
    print("="*70)
    
    # Create training data
    print("\n1. Creating training data...")
    signals_df, backtest_df = create_sample_training_data()
    print(f"   Signals: {len(signals_df)} records")
    print(f"   Backtest results: {len(backtest_df)} records")
    print(f"   Class distribution: {backtest_df['result'].value_counts().to_dict()}")
    
    # Train model
    print("\n2. Training ML model (random_forest)...")
    trainer = MLModelTrainer(model_type='random_forest')
    metrics = trainer.train(signals_df, backtest_df, test_size=0.2)
    print(f"   Train size: {metrics['train_size']}")
    print(f"   Test size: {metrics['test_size']}")
    
    # Display training metrics
    print("\n3. TRAINING METRICS:")
    print(f"   Accuracy:  {metrics['accuracy']:.2%}")
    print(f"   Precision: {metrics['precision']:.2%}")
    print(f"   Recall:    {metrics['recall']:.2%}")
    print(f"   F1 Score:  {metrics['f1']:.2%}")
    print(f"   ROC AUC:   {metrics['roc_auc']:.2%}")
    
    # Display training summary
    print("\n4. DETAILED TRAINING SUMMARY:")
    print(trainer.get_summary())
    
    # Make predictions on test signals
    print("\n5. Making predictions on signals...")
    test_signals = signals_df.iloc[:10].copy()
    results = trainer.model.predict(test_signals)
    
    print("\n6. PREDICTION RESULTS:")
    print(f"{'Symbol':<10} {'Score':<8} {'Probability':<15} {'Prediction':<12}")
    print("-" * 50)
    for i, result in enumerate(results):
        pred_label = "WIN" if result.predicted_label == 1 else "LOSS"
        print(f"{result.symbol:<10} {test_signals.iloc[i]['score']:<8} "
              f"{result.probability*100:>6.1f}% ({result.probability:.2f})  {pred_label:<12}")
    
    # Rank signals by probability
    print("\n7. TOP SIGNALS BY SUCCESS PROBABILITY:")
    sorted_results = sorted(results, key=lambda r: r.probability, reverse=True)
    print(f"{'Rank':<6} {'Symbol':<10} {'Probability':<15} {'Confidence':<12}")
    print("-" * 50)
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"{i:<6} {result.symbol:<10} {result.probability*100:>6.1f}%  "
              f"{result.confidence:.2f}")


def example_3_combined_workflow():
    """Example 3: Combined backtesting + ML workflow"""
    print("\n" + "="*70)
    print("EXAMPLE 3: COMBINED BACKTEST + ML WORKFLOW")
    print("="*70)
    
    # Step 1: Generate signals
    print("\n1. Generating signals...")
    signals = generate_sample_signals(n_signals=100)
    
    # Step 2: Backtest signals
    print("2. Backtesting signals...")
    engine = BacktestEngine()
    price_data = {sym: generate_sample_ohlcv(sym, 20) 
                  for sym in signals['symbol'].unique()}
    ob_data = {sym: {'low': signals[signals['symbol']==sym]['ob_low'].iloc[0], 
                     'high': signals[signals['symbol']==sym]['ob_high'].iloc[0]}
               for sym in signals['symbol'].unique()}
    
    engine.backtest_signals(signals, price_data, ob_data)
    backtest_results = engine.get_trades_dataframe()
    
    # Step 3: Train ML model
    print("3. Training ML model...")
    signals_for_ml = signals[['symbol', 'score', 'ob_depth', 'volume_ratio', 
                              'is_doji', 'is_swing', 'is_consolidation', 'is_ob_tap']]
    backtest_for_ml = backtest_results[['symbol', 'result']]
    
    trainer = MLModelTrainer()
    trainer.train(signals_for_ml, backtest_for_ml)
    
    # Step 4: Predict on new signals
    print("4. Predicting on new signals...")
    new_signals = generate_sample_signals(n_signals=10)
    predictions = trainer.model.predict(new_signals)
    
    # Step 5: Display combined results
    print("\n5. COMBINED RESULTS:")
    print(f"{'Symbol':<10} {'Score':<6} {'BT Win%':<10} {'ML Prob%':<12} {'Rank':<6}")
    print("-" * 55)
    
    for pred in sorted(predictions, key=lambda p: p.probability, reverse=True):
        bt_wins = backtest_results[backtest_results['symbol'] == pred.symbol]['result'].value_counts()
        win_pct = (bt_wins.get('WIN', 0) / len(bt_wins) * 100) if len(bt_wins) > 0 else 0
        print(f"{pred.symbol:<10} "
              f"{new_signals[new_signals['symbol']==pred.symbol]['score'].iloc[0]:<6} "
              f"{win_pct:>6.1f}%     "
              f"{pred.probability*100:>6.1f}%      "
              f"{'A' if pred.probability > 0.7 else 'B' if pred.probability > 0.5 else 'C':<6}")


def example_4_model_persistence():
    """Example 4: Saving and loading models"""
    print("\n" + "="*70)
    print("EXAMPLE 4: MODEL PERSISTENCE")
    print("="*70)
    
    import tempfile
    
    # Train and save model
    print("\n1. Training and saving model...")
    signals_df, backtest_df = create_sample_training_data()
    trainer = MLModelTrainer(model_type='random_forest')
    trainer.train(signals_df, backtest_df)
    
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        model_path = f.name
    
    trainer.save_model(model_path)
    print(f"   Model saved to: {model_path}")
    
    # Load model
    print("\n2. Loading saved model...")
    loaded_model = SignalPredictorML.load_model(model_path)
    print(f"   Model loaded successfully")
    print(f"   Trained: {loaded_model.is_trained}")
    print(f"   Features: {loaded_model.feature_names}")
    
    # Make predictions with loaded model
    print("\n3. Making predictions with loaded model...")
    test_signal = signals_df.iloc[0:5].copy()
    results = loaded_model.predict(test_signal)
    
    print(f"\n   Predictions from loaded model:")
    for result in results:
        print(f"   {result.symbol}: {result.probability*100:.1f}% success probability")
    
    # Cleanup
    os.unlink(model_path)
    print(f"\n   Temp file cleaned up")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PHASE 9-10 COMPLETE WORKFLOW EXAMPLES")
    print("Backtesting & Machine Learning Integration")
    print("="*70)
    
    # Run all examples
    example_1_basic_backtesting()
    example_2_ml_training_and_prediction()
    example_3_combined_workflow()
    example_4_model_persistence()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("="*70)
