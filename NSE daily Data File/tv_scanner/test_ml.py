"""
Phase 10 Tests: ML Layer Testing
Test ML model training and prediction.
"""

import unittest
import pandas as pd
import numpy as np
from ml.signal_predictor import SignalPredictorML, PredictionResult
from ml.train_model import MLModelTrainer, create_sample_training_data
import tempfile
import os


class TestSignalPredictorML(unittest.TestCase):
    """Test SignalPredictorML"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = SignalPredictorML(model_type='random_forest')
        
        # Create sample training data
        np.random.seed(42)
        n_samples = 50
        
        self.signal_data = pd.DataFrame({
            'symbol': [f'STOCK{i%10}' for i in range(n_samples)],
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
        
        self.labels = np.random.randint(0, 2, n_samples)
    
    def test_prepare_features(self):
        """Test feature preparation"""
        X, feature_names = self.predictor.prepare_features(self.signal_data)
        
        self.assertIsNotNone(X)
        self.assertIsNotNone(feature_names)
        self.assertEqual(X.shape[0], len(self.signal_data))
        self.assertGreater(len(feature_names), 0)
    
    def test_model_training(self):
        """Test model training"""
        metrics = self.predictor.train(self.signal_data, self.labels)
        
        self.assertTrue(self.predictor.is_trained)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1', metrics)
        self.assertGreaterEqual(metrics['accuracy'], 0)
        self.assertLessEqual(metrics['accuracy'], 1)
    
    def test_model_prediction(self):
        """Test model prediction"""
        # Train first
        self.predictor.train(self.signal_data, self.labels)
        
        # Predict
        results = self.predictor.predict(self.signal_data.head(5))
        
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, PredictionResult)
            self.assertGreaterEqual(result.probability, 0)
            self.assertLessEqual(result.probability, 1)
            self.assertGreaterEqual(result.confidence, 0)
            self.assertLessEqual(result.confidence, 1)
    
    def test_predict_single(self):
        """Test single signal prediction"""
        # Train first
        self.predictor.train(self.signal_data, self.labels)
        
        # Predict single
        signal_dict = {
            'symbol': 'INFY',
            'score': 10,
            'ob_depth': 50,
            'volume_ratio': 1.5,
            'close': 500,
            'ob_low': 450,
            'ob_high': 550,
            'is_doji': 1,
            'is_swing': 0,
            'is_consolidation': 0,
            'is_ob_tap': 1,
        }
        
        result = self.predictor.predict_single(signal_dict)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, 'INFY')
        self.assertGreaterEqual(result.probability, 0)
        self.assertLessEqual(result.probability, 1)
    
    def test_save_and_load_model(self):
        """Test saving and loading model"""
        # Train
        self.predictor.train(self.signal_data, self.labels)
        
        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.pkl')
            self.predictor.save_model(model_path)
            
            # Load
            loaded_predictor = SignalPredictorML.load_model(model_path)
            
            self.assertTrue(loaded_predictor.is_trained)
            self.assertEqual(loaded_predictor.model_type, 'random_forest')
            
            # Verify same predictions
            original_pred = self.predictor.predict(self.signal_data.head(1))
            loaded_pred = loaded_predictor.predict(self.signal_data.head(1))
            
            np.testing.assert_almost_equal(
                original_pred[0].probability,
                loaded_pred[0].probability
            )
    
    def test_feature_importance(self):
        """Test feature importance extraction"""
        # Train
        self.predictor.train(self.signal_data, self.labels)
        
        # Check feature importance
        self.assertIsNotNone(self.predictor.feature_importance)
        self.assertGreater(len(self.predictor.feature_importance), 0)
    
    def test_training_summary(self):
        """Test training summary generation"""
        # Train
        self.predictor.train(self.signal_data, self.labels)
        
        summary = self.predictor.get_training_summary()
        
        self.assertIn('ML MODEL TRAINING SUMMARY', summary)
        self.assertIn('Accuracy', summary)
        self.assertIn('Precision', summary)
        self.assertIn('Recall', summary)


class TestMLModelTrainer(unittest.TestCase):
    """Test MLModelTrainer"""
    
    def test_trainer_initialization(self):
        """Test trainer initialization"""
        trainer = MLModelTrainer(model_type='random_forest')
        
        self.assertIsNotNone(trainer.model)
        self.assertFalse(trainer.model.is_trained)
    
    def test_prepare_training_data(self):
        """Test training data preparation"""
        signals_df, backtest_df = create_sample_training_data()
        
        trainer = MLModelTrainer()
        training_data, labels = trainer.prepare_training_data(signals_df, backtest_df)
        
        self.assertEqual(len(training_data), len(backtest_df))
        self.assertEqual(len(labels), len(backtest_df))
        self.assertTrue(all(label in [0, 1] for label in labels))
    
    def test_trainer_model_training(self):
        """Test model training via trainer"""
        signals_df, backtest_df = create_sample_training_data()
        
        trainer = MLModelTrainer()
        metrics = trainer.train(signals_df, backtest_df)
        
        self.assertIn('accuracy', metrics)
        self.assertGreater(metrics['train_size'], 0)
        self.assertGreater(metrics['test_size'], 0)
    
    def test_trainer_save_model(self):
        """Test model saving via trainer"""
        signals_df, backtest_df = create_sample_training_data()
        
        trainer = MLModelTrainer()
        trainer.train(signals_df, backtest_df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'trainer_model.pkl')
            trainer.save_model(model_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(model_path))
    
    def test_sample_data_creation(self):
        """Test sample data creation"""
        signals_df, backtest_df = create_sample_training_data()
        
        self.assertEqual(len(signals_df), len(backtest_df))
        self.assertIn('symbol', signals_df.columns)
        self.assertIn('score', signals_df.columns)
        self.assertIn('result', backtest_df.columns)


class TestPredictionResult(unittest.TestCase):
    """Test PredictionResult dataclass"""
    
    def test_prediction_result_creation(self):
        """Test creating prediction result"""
        result = PredictionResult(
            symbol='INFY',
            probability=0.75,
            predicted_label=1,
            confidence=0.5,
        )
        
        self.assertEqual(result.symbol, 'INFY')
        self.assertEqual(result.probability, 0.75)
        self.assertEqual(result.predicted_label, 1)
    
    def test_prediction_result_str(self):
        """Test string representation"""
        result = PredictionResult(
            symbol='INFY',
            probability=0.75,
            predicted_label=1,
            confidence=0.5,
        )
        
        str_rep = str(result)
        self.assertIn('INFY', str_rep)
        self.assertIn('75.0%', str_rep)


if __name__ == '__main__':
    unittest.main()
