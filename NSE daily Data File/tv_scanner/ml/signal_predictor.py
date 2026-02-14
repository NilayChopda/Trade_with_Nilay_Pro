"""
Phase 10: ML Signal Predictor
Train and predict signal success probability using machine learning.
"""

import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
except ImportError:
    raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of signal prediction"""
    symbol: str
    probability: float
    predicted_label: int
    confidence: float
    feature_importance: Dict[str, float] = None
    
    def __str__(self) -> str:
        return f"{self.symbol}: {self.probability*100:.1f}% (confidence: {self.confidence:.2f})"


class SignalPredictorML:
    """
    Machine learning model to predict signal success probability.
    
    Features used:
    - Signal score (0-14)
    - OB zone depth
    - Volume ratio
    - Signal type (doji, swing, consolidation, etc.)
    - Price position in zone
    - Time-based features
    """
    
    def __init__(self, 
                 model_type: str = 'random_forest',
                 random_state: int = 42):
        """
        Initialize ML predictor.
        
        Args:
            model_type: 'random_forest' or 'gradient_boosting'
            random_state: Seed for reproducibility
        """
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.training_metrics = {}
        self.feature_importance = {}
        
        # Initialize model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=random_state
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def prepare_features(self, signal_data: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features from signal data.
        
        Args:
            signal_data: DataFrame with signal information
        
        Returns:
            Tuple of (feature matrix, feature names)
        """
        features = []
        feature_names = []
        
        # Signal score (0-14)
        if 'score' in signal_data.columns:
            features.append(signal_data['score'].values)
            feature_names.append('score')
        
        # OB zone depth
        if 'ob_depth' in signal_data.columns:
            features.append(signal_data['ob_depth'].values)
            feature_names.append('ob_depth')
        
        # Volume ratio (current vs MA)
        if 'volume_ratio' in signal_data.columns:
            features.append(signal_data['volume_ratio'].values)
            feature_names.append('volume_ratio')
        
        # Price position (0-1, where 0 is at OB low, 1 is at OB high)
        if 'ob_low' in signal_data.columns and 'ob_high' in signal_data.columns and 'close' in signal_data.columns:
            price_position = (
                (signal_data['close'] - signal_data['ob_low']) / 
                (signal_data['ob_high'] - signal_data['ob_low'])
            ).clip(0, 1)
            features.append(price_position.values)
            feature_names.append('price_position')
        
        # Signal strength (additional metric)
        if 'signal_strength' in signal_data.columns:
            features.append(signal_data['signal_strength'].values)
            feature_names.append('signal_strength')
        
        # One-hot encode signal types if available
        signal_types = ['is_doji', 'is_swing', 'is_consolidation', 'is_ob_tap']
        for sig_type in signal_types:
            if sig_type in signal_data.columns:
                features.append(signal_data[sig_type].astype(int).values)
                feature_names.append(sig_type)
        
        # Combine all features
        if features:
            X = np.column_stack(features)
        else:
            # Default features if none provided
            X = np.ones((len(signal_data), 1))
            feature_names = ['default_feature']
        
        self.feature_names = feature_names
        return X, feature_names
    
    def train(self, 
              signal_data: pd.DataFrame,
              labels: np.ndarray,
              test_size: float = 0.2) -> Dict:
        """
        Train the ML model.
        
        Args:
            signal_data: DataFrame with signal information
            labels: Binary array (1 for winning signal, 0 for losing)
            test_size: Fraction of data for testing
        
        Returns:
            Dictionary with training metrics
        """
        if len(signal_data) < 10:
            raise ValueError("Need at least 10 samples for training")
        
        # Prepare features
        X, feature_names = self.prepare_features(signal_data)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=test_size, random_state=self.random_state
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        self.training_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'train_size': len(X_train),
            'test_size': len(X_test),
        }
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = {
                name: float(importance)
                for name, importance in zip(feature_names, self.model.feature_importances_)
            }
        
        logger.info(f"Model trained - Accuracy: {self.training_metrics['accuracy']:.2%}")
        
        return self.training_metrics
    
    def predict(self, signal_data: pd.DataFrame) -> List[PredictionResult]:
        """
        Predict success probability for signals.
        
        Args:
            signal_data: DataFrame with signal information
        
        Returns:
            List of PredictionResult objects
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Prepare features
        X, _ = self.prepare_features(signal_data)
        
        # Ensure X has correct number of features by padding or truncating
        n_features_expected = len(self.feature_names)
        if X.shape[1] < n_features_expected:
            # Pad with zeros if missing features
            padding = np.zeros((X.shape[0], n_features_expected - X.shape[1]))
            X = np.column_stack([X, padding])
        elif X.shape[1] > n_features_expected:
            # Truncate if too many features
            X = X[:, :n_features_expected]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        # Calculate confidence (distance from 0.5)
        confidence = np.abs(probabilities - 0.5) * 2
        
        # Create results
        results = []
        for i, row in signal_data.iterrows():
            result = PredictionResult(
                symbol=row.get('symbol', f'Signal_{i}'),
                probability=float(probabilities[i]),
                predicted_label=int(predictions[i]),
                confidence=float(confidence[i]),
                feature_importance=self.feature_importance,
            )
            results.append(result)
        
        return results
    
    def predict_single(self, signal_dict: Dict) -> PredictionResult:
        """
        Predict for a single signal.
        
        Args:
            signal_dict: Dictionary with signal data
        
        Returns:
            PredictionResult object
        """
        signal_df = pd.DataFrame([signal_dict])
        results = self.predict(signal_df)
        return results[0] if results else None
    
    def save_model(self, filepath: str):
        """
        Save trained model to file.
        
        Args:
            filepath: Path to save model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'training_metrics': self.training_metrics,
            'feature_importance': self.feature_importance,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    @staticmethod
    def load_model(filepath: str) -> 'SignalPredictorML':
        """
        Load trained model from file.
        
        Args:
            filepath: Path to model file
        
        Returns:
            SignalPredictorML instance
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        predictor = SignalPredictorML(model_type=model_data['model_type'])
        predictor.model = model_data['model']
        predictor.scaler = model_data['scaler']
        predictor.feature_names = model_data['feature_names']
        predictor.training_metrics = model_data['training_metrics']
        predictor.feature_importance = model_data['feature_importance']
        predictor.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")
        return predictor
    
    def get_training_summary(self) -> str:
        """
        Get text summary of training metrics.
        
        Returns:
            Formatted text summary
        """
        if not self.training_metrics:
            return "Model not trained yet"
        
        summary = []
        summary.append("=" * 50)
        summary.append("ML MODEL TRAINING SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Model Type:     {self.model_type}")
        summary.append(f"Train Size:     {self.training_metrics.get('train_size', 0)}")
        summary.append(f"Test Size:      {self.training_metrics.get('test_size', 0)}")
        summary.append("")
        summary.append("PERFORMANCE METRICS")
        summary.append("-" * 50)
        summary.append(f"Accuracy:       {self.training_metrics.get('accuracy', 0):.2%}")
        summary.append(f"Precision:      {self.training_metrics.get('precision', 0):.2%}")
        summary.append(f"Recall:         {self.training_metrics.get('recall', 0):.2%}")
        summary.append(f"F1 Score:       {self.training_metrics.get('f1', 0):.2%}")
        summary.append(f"ROC AUC:        {self.training_metrics.get('roc_auc', 0):.2%}")
        summary.append("")
        
        if self.feature_importance:
            summary.append("TOP FEATURES")
            summary.append("-" * 50)
            sorted_features = sorted(
                self.feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            for feature, importance in sorted_features:
                summary.append(f"{feature:.<20} {importance:.4f}")
        
        summary.append("=" * 50)
        return "\n".join(summary)
