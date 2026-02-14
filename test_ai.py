"""
Test AI Scoring Engine
"""

import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.ai.scorer import AIScorer
from backend.ai.explainer import generate_explanation

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("twn.test_ai")
    
    logger.info("Testing AI Scorer...")
    scorer = AIScorer()
    
    # Test Case 1: Strong Setup
    setup1 = {
        "price_action": {
            "change_pct": 3.5,
            "volume_mult": 2.5,
            "trend": "UPTREND"
        },
        "strategies": [
            {"pattern": "Bullish Order Block"},
            {"pattern": "Breakout"}
        ],
        "fno": {
            "bias": "Bullish"
        }
    }
    
    # Test Case 2: Weak Setup
    setup2 = {
        "price_action": {
            "change_pct": 0.5,
            "volume_mult": 0.8,
            "trend": "SIDEWAYS"
        },
        "strategies": [],
        "fno": {
            "bias": "Neutral"
        }
    }
    
    # Run Scorer
    score1 = scorer.score_setup("RELIANCE", setup1)
    logger.info(f"Setup 1 Score: {score1['score']}/10 ({score1['rating']})")
    print(generate_explanation(score1, "RELIANCE"))
    print("-" * 40)
    
    score2 = scorer.score_setup("TCS", setup2)
    logger.info(f"Setup 2 Score: {score2['score']}/10 ({score2['rating']})")
    print(generate_explanation(score2, "TCS"))
