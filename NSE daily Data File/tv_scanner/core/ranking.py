"""
Phase 7: Signal Ranking System
Assigns scores to stocks based on multiple signal conditions and returns top N ranked stocks.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RankedSignal:
    """Data class for ranked trading signals"""
    symbol: str
    total_score: float
    ob_tap_score: float = 0.0
    swing_condition_score: float = 0.0
    doji_score: float = 0.0
    consolidation_score: float = 0.0
    volume_spike_score: float = 0.0
    
    # Additional context
    close_price: float = 0.0
    pct_change: float = 0.0
    volume: float = 0.0
    
    # Signal details
    ob_tapped: bool = False
    swing_valid: bool = False
    doji_detected: bool = False
    consolidation_detected: bool = False
    volume_spiked: bool = False


class SignalRankingEngine:
    """
    Ranks stocks based on multiple signal conditions.
    
    Scoring System:
    - OB tap = 5 points
    - Swing condition = 3 points
    - Doji = 2 points
    - Consolidation = 2 points
    - Volume spike = 2 points
    """
    
    # Scoring weights
    SCORES = {
        'ob_tap': 5,
        'swing_condition': 3,
        'doji': 2,
        'consolidation': 2,
        'volume_spike': 2
    }
    
    def __init__(self):
        self.ranked_signals: List[RankedSignal] = []
    
    def calculate_rank(self, 
                      symbol: str,
                      metrics: Dict,
                      ob_tapped: bool = False,
                      swing_valid: bool = False,
                      doji_detected: bool = False,
                      consolidation_detected: bool = False,
                      volume_spiked: bool = False) -> RankedSignal:
        """
        Calculate score for a single stock based on detected signals.
        
        Args:
            symbol: Stock symbol
            metrics: Dictionary with OHLCV data and indicators
            ob_tapped: Whether Order Block was tapped
            swing_valid: Whether swing condition met
            doji_detected: Whether doji pattern detected
            consolidation_detected: Whether consolidation detected
            volume_spiked: Whether volume spike detected
        
        Returns:
            RankedSignal object with computed score
        """
        scores = {}
        total_score = 0.0
        
        # OB Tap: 5 points
        ob_score = self.SCORES['ob_tap'] if ob_tapped else 0.0
        scores['ob_tap'] = ob_score
        total_score += ob_score
        
        # Swing Condition: 3 points
        swing_score = self.SCORES['swing_condition'] if swing_valid else 0.0
        scores['swing_condition'] = swing_score
        total_score += swing_score
        
        # Doji: 2 points
        doji_score = self.SCORES['doji'] if doji_detected else 0.0
        scores['doji'] = doji_score
        total_score += doji_score
        
        # Consolidation: 2 points
        consolidation_score = self.SCORES['consolidation'] if consolidation_detected else 0.0
        scores['consolidation'] = consolidation_score
        total_score += consolidation_score
        
        # Volume Spike: 2 points
        volume_score = self.SCORES['volume_spike'] if volume_spiked else 0.0
        scores['volume_spike'] = volume_score
        total_score += volume_score
        
        # Create ranked signal
        ranked = RankedSignal(
            symbol=symbol,
            total_score=total_score,
            ob_tap_score=ob_score,
            swing_condition_score=swing_score,
            doji_score=doji_score,
            consolidation_score=consolidation_score,
            volume_spike_score=volume_score,
            close_price=metrics.get('close', 0.0),
            pct_change=metrics.get('pct_change', 0.0),
            volume=metrics.get('volume', 0.0),
            ob_tapped=ob_tapped,
            swing_valid=swing_valid,
            doji_detected=doji_detected,
            consolidation_detected=consolidation_detected,
            volume_spiked=volume_spiked
        )
        
        return ranked
    
    def rank_signals(self, signals: List[RankedSignal], 
                     top_n: Optional[int] = None) -> List[RankedSignal]:
        """
        Sort signals by total score in descending order.
        
        Args:
            signals: List of RankedSignal objects
            top_n: Return only top N signals (None = return all)
        
        Returns:
            Sorted list of RankedSignal objects
        """
        sorted_signals = sorted(signals, key=lambda x: x.total_score, reverse=True)
        
        if top_n:
            sorted_signals = sorted_signals[:top_n]
        
        self.ranked_signals = sorted_signals
        return sorted_signals
    
    def format_ranking_report(self, signals: List[RankedSignal]) -> str:
        """
        Format ranked signals as a readable report.
        
        Args:
            signals: List of RankedSignal objects to format
        
        Returns:
            Formatted string report
        """
        if not signals:
            return "No signals to rank."
        
        report = []
        report.append("\n" + "="*80)
        report.append("📊 SIGNAL RANKING REPORT")
        report.append("="*80)
        report.append(f"{'Rank':<5} {'Symbol':<12} {'Score':<7} {'OB':<4} {'Swing':<6} {'Doji':<6} {'Cons':<6} {'Vol':<5} {'Price':<10} {'Chg%':<7}")
        report.append("-"*80)
        
        for idx, signal in enumerate(signals, 1):
            # Create signal indicators
            ob_ind = "✓" if signal.ob_tapped else "✗"
            swing_ind = "✓" if signal.swing_valid else "✗"
            doji_ind = "✓" if signal.doji_detected else "✗"
            cons_ind = "✓" if signal.consolidation_detected else "✗"
            vol_ind = "✓" if signal.volume_spiked else "✗"
            
            report.append(
                f"{idx:<5} {signal.symbol:<12} {signal.total_score:<7.1f} "
                f"{ob_ind:<4} {swing_ind:<6} {doji_ind:<6} {cons_ind:<6} {vol_ind:<5} "
                f"₹{signal.close_price:<9.2f} {signal.pct_change:>+6.2f}%"
            )
        
        report.append("="*80)
        report.append(f"Total Signals: {len(signals)}")
        report.append("Legend: OB=Order Block, Swing=Swing Condition, Cons=Consolidation, Vol=Volume Spike")
        report.append("="*80 + "\n")
        
        return "\n".join(report)
    
    def to_dataframe(self, signals: List[RankedSignal]) -> pd.DataFrame:
        """
        Convert ranked signals to pandas DataFrame.
        
        Args:
            signals: List of RankedSignal objects
        
        Returns:
            DataFrame with ranking information
        """
        data = []
        for idx, signal in enumerate(signals, 1):
            data.append({
                'Rank': idx,
                'Symbol': signal.symbol,
                'Total_Score': signal.total_score,
                'OB_Tap': signal.ob_tap_score,
                'Swing': signal.swing_condition_score,
                'Doji': signal.doji_score,
                'Consolidation': signal.consolidation_score,
                'Volume_Spike': signal.volume_spike_score,
                'Close_Price': signal.close_price,
                'Pct_Change': signal.pct_change,
                'OB_Tapped': signal.ob_tapped,
                'Swing_Valid': signal.swing_valid,
                'Doji_Detected': signal.doji_detected,
                'Consolidation_Detected': signal.consolidation_detected,
                'Volume_Spiked': signal.volume_spiked
            })
        
        return pd.DataFrame(data)
    
    def get_summary_stats(self, signals: List[RankedSignal]) -> Dict:
        """
        Get summary statistics for ranked signals.
        
        Args:
            signals: List of RankedSignal objects
        
        Returns:
            Dictionary with summary statistics
        """
        if not signals:
            return {}
        
        scores = [s.total_score for s in signals]
        
        return {
            'total_signals': len(signals),
            'avg_score': np.mean(scores),
            'max_score': np.max(scores),
            'min_score': np.min(scores),
            'std_score': np.std(scores),
            'ob_tapped_count': sum(1 for s in signals if s.ob_tapped),
            'swing_valid_count': sum(1 for s in signals if s.swing_valid),
            'doji_count': sum(1 for s in signals if s.doji_detected),
            'consolidation_count': sum(1 for s in signals if s.consolidation_detected),
            'volume_spike_count': sum(1 for s in signals if s.volume_spiked),
        }
