"""
Phase 9 Tests: Backtesting Module
Test trade simulation and metric calculations.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting.backtest_engine import BacktestEngine, Trade
from backtesting.backtest_report import BacktestReportGenerator


class TestTrade(unittest.TestCase):
    """Test Trade dataclass"""
    
    def test_trade_creation(self):
        """Test creating a trade"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        self.assertEqual(trade.symbol, "INFY")
        self.assertEqual(trade.entry_price, 1500)
        self.assertEqual(trade.stop_loss, 1450)
        self.assertEqual(trade.risk, 50)
        self.assertEqual(trade.reward, 100)
    
    def test_risk_reward_ratio(self):
        """Test risk/reward ratio calculation"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        # Risk = 50, Reward = 100, so RR = 2
        self.assertEqual(trade.risk_reward_ratio, 2.0)
    
    def test_close_trade_with_target(self):
        """Test closing trade at target"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        exit_date = datetime.now() + timedelta(days=1)
        trade.close_trade(1600, exit_date, "TARGET")
        
        self.assertEqual(trade.exit_price, 1600)
        self.assertEqual(trade.exit_type, "TARGET")
        self.assertEqual(trade.result, "WIN")
        self.assertEqual(trade.pnl, 100)
    
    def test_close_trade_with_sl(self):
        """Test closing trade at stop loss"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        exit_date = datetime.now() + timedelta(days=1)
        trade.close_trade(1450, exit_date, "SL")
        
        self.assertEqual(trade.exit_price, 1450)
        self.assertEqual(trade.exit_type, "SL")
        self.assertEqual(trade.result, "LOSS")
        self.assertEqual(trade.pnl, -50)


class TestBacktestEngine(unittest.TestCase):
    """Test BacktestEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = BacktestEngine(slippage_percent=0.1)
    
    def test_create_trade(self):
        """Test creating a trade with backtesting logic"""
        trade = self.engine.create_trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            ob_low=1450,
            risk_multiplier=2.0
        )
        
        # With 0.1% slippage: 1500 * 1.001 = 1501.5
        # Risk = 1501.5 - 1450 = 51.5
        # Target = 1501.5 + (51.5 * 2) = 1604.5
        self.assertGreater(trade.entry_price, 1500)
        self.assertEqual(trade.stop_loss, 1450)
        self.assertGreater(trade.target_price, 1600)
    
    def test_simulate_trade_hit_target(self):
        """Test trade that hits target"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        # Create OHLCV data
        dates = pd.date_range(start='2025-01-01', periods=5, freq='D')
        ohlcv_data = pd.DataFrame({
            'open': [1500, 1510, 1550, 1590, 1610],
            'high': [1510, 1520, 1560, 1600, 1620],
            'low': [1490, 1500, 1540, 1580, 1600],
            'close': [1505, 1515, 1555, 1595, 1615],
            'volume': [1000000] * 5,
        }, index=dates)
        
        result = self.engine.simulate_trade(trade, ohlcv_data)
        
        self.assertTrue(result)
        self.assertEqual(trade.exit_type, "TARGET")
        self.assertEqual(trade.result, "WIN")
    
    def test_simulate_trade_hit_sl(self):
        """Test trade that hits stop loss"""
        trade = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        
        # Create OHLCV data with stop loss hit
        dates = pd.date_range(start='2025-01-01', periods=5, freq='D')
        ohlcv_data = pd.DataFrame({
            'open': [1500, 1480, 1470, 1460, 1450],
            'high': [1505, 1485, 1475, 1465, 1455],
            'low': [1445, 1475, 1465, 1455, 1445],
            'close': [1480, 1470, 1460, 1450, 1440],
            'volume': [1000000] * 5,
        }, index=dates)
        
        result = self.engine.simulate_trade(trade, ohlcv_data)
        
        self.assertTrue(result)
        self.assertEqual(trade.exit_type, "SL")
        self.assertEqual(trade.result, "LOSS")
    
    def test_backtest_metrics(self):
        """Test metrics calculation"""
        # Create sample trades
        trade1 = Trade(
            symbol="INFY",
            entry_price=1500,
            entry_date=datetime.now(),
            stop_loss=1450,
            target_price=1600,
        )
        trade1.close_trade(1600, datetime.now(), "TARGET")
        
        trade2 = Trade(
            symbol="TCS",
            entry_price=3000,
            entry_date=datetime.now(),
            stop_loss=2950,
            target_price=3100,
        )
        trade2.close_trade(2950, datetime.now(), "SL")
        
        self.engine.trades = [trade1, trade2]
        metrics = self.engine.calculate_metrics()
        
        self.assertEqual(metrics['total_trades'], 2)
        self.assertEqual(metrics['winning_trades'], 1)
        self.assertEqual(metrics['losing_trades'], 1)
        self.assertEqual(metrics['win_rate'], 50.0)


class TestBacktestReportGenerator(unittest.TestCase):
    """Test BacktestReportGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = BacktestReportGenerator()
        self.metrics = {
            'total_trades': 10,
            'winning_trades': 7,
            'losing_trades': 3,
            'win_rate': 70.0,
            'total_pnl': 5000,
            'avg_pnl': 500,
            'avg_return_percent': 5.5,
            'avg_win': 750,
            'avg_loss': -250,
            'max_win': 1500,
            'max_loss': -1000,
            'max_drawdown': 2000,
            'profit_factor': 3.5,
            'avg_risk_reward': 2.0,
            'expectancy': 450,
            'gross_profit': 5250,
            'gross_loss': -750,
        }
    
    def test_generate_summary_report(self):
        """Test text report generation"""
        report = self.generator.generate_summary_report(self.metrics)
        
        self.assertIn("BACKTESTING SUMMARY REPORT", report)
        self.assertIn("10", report)  # total trades
        self.assertIn("70", report)  # win rate
        self.assertIn("5000", report)  # total pnl
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        trades_df = pd.DataFrame({
            'symbol': ['INFY', 'TCS'],
            'entry_price': [1500, 3000],
            'stop_loss': [1450, 2950],
            'target_price': [1600, 3100],
            'exit_price': [1600, 2950],
            'pnl': [100, -50],
            'pnl_percent': [6.67, -1.67],
            'result': ['WIN', 'LOSS'],
        })
        
        html = self.generator.generate_html_report(self.metrics, trades_df)
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Backtesting Report", html)
        self.assertIn("INFY", html)
        self.assertIn("TCS", html)
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        trades_df = pd.DataFrame({
            'symbol': ['INFY'],
            'entry_price': [1500],
            'result': ['WIN'],
        })
        
        json_str = self.generator.generate_json_report(self.metrics, trades_df)
        
        self.assertIn('"metrics"', json_str)
        self.assertIn('"trades"', json_str)
        self.assertIn('INFY', json_str)
    
    def test_generate_statistics_summary(self):
        """Test statistics summary generation"""
        stats = self.generator.generate_statistics_summary(self.metrics)
        
        self.assertIn('overview', stats)
        self.assertIn('profitability', stats)
        self.assertIn('risk', stats)
        self.assertEqual(stats['overview']['total_trades'], 10)
        self.assertEqual(stats['profitability']['profit_factor'], 3.5)


if __name__ == '__main__':
    unittest.main()
