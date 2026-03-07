import pandas as pd
import numpy as np
from backend.strategy.pattern_detector import PatternDetector

def generate_fake_data():
    dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
    prices = np.linspace(100, 120, 60) + np.random.randn(60)
    vol = np.random.randint(1000,5000,size=60)
    df = pd.DataFrame({
        'open': prices - np.random.rand(60),
        'high': prices + np.random.rand(60),
        'low': prices - np.random.rand(60)*2,
        'close': prices,
        'volume': vol
    }, index=dates)
    return df


def test_pattern_detection_runs():
    detector = PatternDetector()
    df = generate_fake_data()
    result = detector.analyze(df, 'TEST')
    # should always return dictionary with expected keys
    assert 'symbol' in result
    assert result['symbol'] == 'TEST'
    assert 'patterns' in result
    assert 'primary_pattern' in result
    # candlestick may be None or string
    assert 'candlestick' in result
