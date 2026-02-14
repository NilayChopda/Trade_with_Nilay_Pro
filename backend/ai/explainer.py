"""
AI Explanation Generator
Generates human-readable explanations for AI scores
"""

from typing import Dict, List
import random

def generate_explanation(score_data: Dict, symbol: str) -> str:
    """
    Generate a text explanation for the trade setup
    """
    score = score_data.get('score', 0)
    rating = score_data.get('rating', 'WEAK')
    reasons = score_data.get('reasons', [])
    
    if not reasons:
        return f"Setup for {symbol} is weak (Score: {score}/10). No significant confluence found."
        
    intro_phrases = [
        f"Strong setup detected for {symbol}!",
        f"{symbol} looks promising based on technicals.",
        f"AI Analysis for {symbol}:",
        f"High probability setup on {symbol}."
    ]
    
    intro = random.choice(intro_phrases)
    
    # Bullet points for reasons
    reason_text = "\n".join([f"• {r}" for r in reasons])
    
    summary = f"""{intro}

**Score**: {score}/10 ({rating})
**Key Drivers**:
{reason_text}

_Confidence: {rating}_"""

    return summary
