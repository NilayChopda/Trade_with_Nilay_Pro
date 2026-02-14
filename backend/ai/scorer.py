"""
AI Setup Scorer
Evaluates trading setups based on technical confluence and assigns a score (0-10)
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("twn.ai_scorer")

class AIScorer:
    """
    Heuristic Scoring Engine for Trading Setups
    """
    
    def __init__(self):
        pass
        
    def score_setup(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate score (0-10) for a setup
        
        Args:
            symbol: Stock symbol
            data: Dictionary containing:
                - price_action: {close, change_pct, volume, rsi, ema_trend}
                - strategies: List of active strategies/patterns
                - fno: {pcr, bias, max_pain} (optional)
                
        Returns:
            Dict with score, confidence, and factors
        """
        score = 0.0
        max_score = 10.0
        factors = []
        
        # 1. Price Momentum & Breakout (Max 5 points)
        change_pct = data.get('price_action', {}).get('change_pct', 0)
        volume_mult = data.get('price_action', {}).get('volume_mult', 1.0) # vs Avg Vol
        strategies = data.get('strategies', [])
        patterns = [s.get('pattern') for s in strategies if 'pattern' in s]
        
        if change_pct > 1.0:
            score += 1.0
            factors.append("Positive Momentum (>1%)")
        if change_pct > 2.0:
            score += 1.0 # Significant momentum
            factors.append("Strong Momentum (>2%)")
        if change_pct > 4.0:
            score += 1.0 # High momentum bonus
            factors.append("Explosive Move (>4%)")
            
        if volume_mult > 1.2:
            score += 1.0
            factors.append(f"Volume Support ({volume_mult:.1f}x)")
        if volume_mult > 2.0:
            score += 1.0 # Significant volume spike
            factors.append(f"Volume Spike ({volume_mult:.1f}x)")
        if volume_mult > 5.0:
            score += 1.0 # Ultra volume
            factors.append("HNI/Institutional Volume")
            
        if "Price Breakout" in patterns:
            score += 2.0
            factors.append("Confirmed Price Breakout")
            # Confluence: Breakout + Volume
            if volume_mult > 2.0:
                score += 1.0
                factors.append("High-Volume Breakout (Strong)")

        # 2. Trend Alignment (Max 2 points)
        trend = data.get('price_action', {}).get('trend', 'NEUTRAL')
        if trend == 'UPTREND':
            score += 2.0
            factors.append("Trend Aligned (HTF)")
            
        # 3. Strategy Confluence (Max 3 points)
        unique_patterns = set(patterns)
        
        if len(unique_patterns) >= 2:
            score += 1.5 # Confluence bonus
            factors.append("Multiple Pattern Confluence")
            
        # 4. FnO Sentiment (Max 2 points)
        fno_bias = data.get('fno', {}).get('bias', 'Neutral')
        if fno_bias == 'Bullish':
            score += 2.0
            factors.append("FnO Data Bullish")
        elif fno_bias == 'Bearish':
            score -= 2.0 # Penalty
            factors.append("FnO Divergence (Bearish)")
            
        # Normalization
        final_score = min(max(score, 0), 10.0)
        
        # Categorize
        rating = "WEAK"
        color = "🔴"
        if final_score >= 8.0:
            rating = "A+ SETUP"
            color = "🟢"
        elif final_score >= 6.0:
            rating = "GOOD"
            color = "🟡"
            
        return {
            "score": round(final_score, 1),
            "rating": rating,
            "color": color,
            "reasons": factors
        }
