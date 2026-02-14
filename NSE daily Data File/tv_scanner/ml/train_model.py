"""
Phase 10: ML Model Training Script
Train ML model on historical signal data and backtesting results.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple
from pathlib import Path
import sys

try:
    from ml.signal_predictor import SignalPredictorML
except ImportError:
    print("Error: Could not import SignalPredictorML. Make sure ml/signal_predictor.py exists.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLModelTrainer:
    """Train ML model using historical signal data and backtesting results"""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize trainer.
        
        Args:
            model_type: 'random_forest' or 'gradient_boosting'
        """
        self.model = SignalPredictorML(model_type=model_type)
        self.training_data = None
        self.labels = None
    
    def prepare_training_data(self,
                             signals_df: pd.DataFrame,
                             backtest_results_df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare training data by merging signals with backtest results.
        
        Args:
            signals_df: DataFrame with signal information
            backtest_results_df: DataFrame with backtest results (including 'result' column)
        
        Returns:
            Tuple of (prepared data, labels)
        """
        # Merge on symbol
        merged = pd.merge(
            signals_df,
            backtest_results_df[['symbol', 'result']],
            on='symbol',
            how='inner'
        )
        
        if len(merged) == 0:
            raise ValueError("No overlapping symbols between signals and backtest results")
        
        # Create labels: 1 for WIN, 0 for LOSS
        labels = (merged['result'] == 'WIN').astype(int).values
        
        # Remove non-numeric columns for training
        features_only = merged.drop(columns=['result', 'entry_date', 'exit_date'], errors='ignore')
        
        logger.info(f"Prepared {len(features_only)} training samples")
        logger.info(f"Class distribution: {np.bincount(labels)}")
        
        return features_only, labels
    
    def train(self, 
              signals_df: pd.DataFrame,
              backtest_results_df: pd.DataFrame,
              test_size: float = 0.2) -> Dict:
        """
        Train the model.
        
        Args:
            signals_df: DataFrame with signal data
            backtest_results_df: DataFrame with backtest results
            test_size: Fraction of data for testing
        
        Returns:
            Dictionary with training metrics
        """
        # Prepare data
        training_data, labels = self.prepare_training_data(signals_df, backtest_results_df)
        
        self.training_data = training_data
        self.labels = labels
        
        # Train model
        metrics = self.model.train(training_data, labels, test_size=test_size)
        
        return metrics
    
    def save_model(self, filepath: str):
        """
        Save trained model.
        
        Args:
            filepath: Path to save model
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(filepath)
        logger.info(f"Model saved to {filepath}")
    
    def get_summary(self) -> str:
        """Get training summary"""
        return self.model.get_training_summary()


def train_model_from_files(signals_csv: str,
                          backtest_csv: str,
                          model_output: str,
                          model_type: str = 'random_forest') -> Dict:
    """
    Train model from CSV files.
    
    Args:
        signals_csv: Path to signals CSV
        backtest_csv: Path to backtest results CSV
        model_output: Path to save trained model
        model_type: Model type to train
    
    Returns:
        Dictionary with training metrics
    """
    logger.info("Loading data...")
    
    # Load data
    signals_df = pd.read_csv(signals_csv)
    backtest_df = pd.read_csv(backtest_csv)
    
    logger.info(f"Loaded {len(signals_df)} signals and {len(backtest_df)} backtest results")
    
    # Train model
    trainer = MLModelTrainer(model_type=model_type)
    metrics = trainer.train(signals_df, backtest_df)
    
    # Save model
    trainer.save_model(model_output)
    
    # Print summary
    print(trainer.get_summary())
    
    return metrics


def create_sample_training_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create sample training data for demonstration.
    
    Returns:
        Tuple of (signals_df, backtest_df)
    """
    # Create sample signals
    np.random.seed(42)
    n_samples = 100
    
    signals_df = pd.DataFrame({
        'symbol': [f'STOCK{i%20}' for i in range(n_samples)],
        'score': np.random.randint(5, 14, n_samples),
        'ob_depth': np.random.uniform(10, 100, n_samples),
        'volume_ratio': np.random.uniform(0.8, 2.0, n_samples),
        'close': np.random.uniform(100, 1000, n_samples),
        'ob_low': np.random.uniform(90, 900, n_samples),
        'ob_high': np.random.uniform(110, 1100, n_samples),
        'is_doji': np.random.randint(0, 2, n_samples),
        'is_swing': np.random.randint(0, 2, n_samples),
        'is_consolidation': np.random.randint(0, 2, n_samples),
        'is_ob_tap': np.random.randint(0, 2, n_samples),
    })
    
    # Create backtest results
    backtest_df = pd.DataFrame({
        'symbol': signals_df['symbol'],
        'result': np.random.choice(['WIN', 'LOSS'], n_samples, p=[0.65, 0.35]),
    })
    
    return signals_df, backtest_df


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML model for signal prediction')
    parser.add_argument('--signals', type=str, help='Path to signals CSV')
    parser.add_argument('--backtest', type=str, help='Path to backtest results CSV')
    parser.add_argument('--output', type=str, default='ml/signal_model.pkl',
                       help='Path to save trained model')
    parser.add_argument('--model-type', type=str, default='random_forest',
                       choices=['random_forest', 'gradient_boosting'],
                       help='Type of model to train')
    parser.add_argument('--demo', action='store_true', help='Use demo data')
    
    args = parser.parse_args()
    
    if args.demo:
        logger.info("Creating sample training data...")
        signals_df, backtest_df = create_sample_training_data()
        
        trainer = MLModelTrainer(model_type=args.model_type)
        metrics = trainer.train(signals_df, backtest_df)
        trainer.save_model(args.output)
        
        print(trainer.get_summary())
    else:
        if not args.signals or not args.backtest:
            parser.print_help()
            sys.exit(1)
        
        metrics = train_model_from_files(
            args.signals,
            args.backtest,
            args.output,
            args.model_type
        )
