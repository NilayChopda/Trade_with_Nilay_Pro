"""
Phase 9: Backtesting Report Generator
Generate comprehensive backtesting reports with metrics and analysis.
"""

import pandas as pd
import json
from typing import Dict, List
from datetime import datetime
import os


class BacktestReportGenerator:
    """Generate detailed backtesting reports"""
    
    def __init__(self):
        self.metrics = {}
        self.trades_df = pd.DataFrame()
    
    def generate_summary_report(self, metrics: Dict) -> str:
        """
        Generate text summary report.
        
        Args:
            metrics: Dictionary of backtest metrics
        
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("BACKTESTING SUMMARY REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Trade Statistics
        report.append("TRADE STATISTICS")
        report.append("-" * 60)
        report.append(f"Total Trades:        {metrics.get('total_trades', 0)}")
        report.append(f"Winning Trades:      {metrics.get('winning_trades', 0)}")
        report.append(f"Losing Trades:       {metrics.get('losing_trades', 0)}")
        report.append(f"Win Rate:            {metrics.get('win_rate', 0)}%")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 60)
        report.append(f"Total P&L:           {metrics.get('total_pnl', 0)}")
        report.append(f"Average P&L:         {metrics.get('avg_pnl', 0)}")
        report.append(f"Average Return:      {metrics.get('avg_return_percent', 0)}%")
        report.append(f"Average Win:         {metrics.get('avg_win', 0)}")
        report.append(f"Average Loss:        {metrics.get('avg_loss', 0)}")
        report.append("")
        
        # Risk Analysis
        report.append("RISK ANALYSIS")
        report.append("-" * 60)
        report.append(f"Max Win:             {metrics.get('max_win', 0)}")
        report.append(f"Max Loss:            {metrics.get('max_loss', 0)}")
        report.append(f"Max Drawdown:        {metrics.get('max_drawdown', 0)}")
        report.append(f"Profit Factor:       {metrics.get('profit_factor', 0)}")
        report.append(f"Avg Risk/Reward:     {metrics.get('avg_risk_reward', 0)}")
        report.append("")
        
        # Advanced Metrics
        report.append("ADVANCED METRICS")
        report.append("-" * 60)
        report.append(f"Expectancy:          {metrics.get('expectancy', 0)}")
        report.append(f"Gross Profit:        {metrics.get('gross_profit', 0)}")
        report.append(f"Gross Loss:          {metrics.get('gross_loss', 0)}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def generate_html_report(self, 
                            metrics: Dict,
                            trades_df: pd.DataFrame,
                            output_path: str = None) -> str:
        """
        Generate HTML report with charts and tables.
        
        Args:
            metrics: Dictionary of backtest metrics
            trades_df: DataFrame with trade details
            output_path: Path to save HTML file
        
        Returns:
            HTML string
        """
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Backtesting Report</title>")
        html.append("<style>")
        html.append("""
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 20px; }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .metric-card {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric-label {
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                margin-top: 5px;
            }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                margin: 20px 0;
            }
            th {
                background-color: #007bff;
                color: white;
                padding: 10px;
                text-align: left;
            }
            td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            tr:hover { background-color: #f9f9f9; }
            .WIN { background-color: #d4edda; }
            .LOSS { background-color: #f8d7da; }
        """)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        
        html.append("<h1>📊 Backtesting Report</h1>")
        html.append(f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        # Metrics Grid
        html.append("<h2>Key Metrics</h2>")
        html.append("<div class='metrics-grid'>")
        
        metric_items = [
            ("Total Trades", metrics.get('total_trades', 0), ''),
            ("Win Rate", f"{metrics.get('win_rate', 0)}%", ''),
            ("Total P&L", metrics.get('total_pnl', 0), 
             'positive' if metrics.get('total_pnl', 0) >= 0 else 'negative'),
            ("Avg Return", f"{metrics.get('avg_return_percent', 0)}%", ''),
            ("Max Drawdown", metrics.get('max_drawdown', 0), 'negative'),
            ("Profit Factor", metrics.get('profit_factor', 0), ''),
            ("Expectancy", metrics.get('expectancy', 0), ''),
            ("Avg Risk/Reward", metrics.get('avg_risk_reward', 0), ''),
        ]
        
        for label, value, css_class in metric_items:
            html.append(f"<div class='metric-card'>")
            html.append(f"<div class='metric-label'>{label}</div>")
            html.append(f"<div class='metric-value {css_class}'>{value}</div>")
            html.append(f"</div>")
        
        html.append("</div>")
        
        # Trades Table
        html.append("<h2>Trade Details</h2>")
        html.append("<table>")
        html.append("<thead><tr>")
        
        columns = ['symbol', 'entry_price', 'stop_loss', 'target_price', 
                  'exit_price', 'pnl', 'pnl_percent', 'result']
        for col in columns:
            html.append(f"<th>{col.replace('_', ' ').title()}</th>")
        html.append("</tr></thead>")
        html.append("<tbody>")
        
        for _, trade in trades_df.iterrows():
            result_class = trade['result']
            html.append(f"<tr class='{result_class}'>")
            for col in columns:
                value = trade[col]
                if isinstance(value, float):
                    value = f"{value:.2f}"
                html.append(f"<td>{value}</td>")
            html.append("</tr>")
        
        html.append("</tbody>")
        html.append("</table>")
        
        html.append("</body>")
        html.append("</html>")
        
        html_string = "\n".join(html)
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(html_string)
        
        return html_string
    
    def generate_json_report(self,
                            metrics: Dict,
                            trades_df: pd.DataFrame,
                            output_path: str = None) -> str:
        """
        Generate JSON report for API integration.
        
        Args:
            metrics: Dictionary of backtest metrics
            trades_df: DataFrame with trade details
            output_path: Path to save JSON file
        
        Returns:
            JSON string
        """
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'trades': trades_df.to_dict('records') if len(trades_df) > 0 else [],
        }
        
        json_string = json.dumps(report_data, indent=2, default=str)
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(json_string)
        
        return json_string
    
    def generate_statistics_summary(self, metrics: Dict) -> Dict:
        """
        Generate detailed statistics summary.
        
        Args:
            metrics: Dictionary of backtest metrics
        
        Returns:
            Organized statistics dictionary
        """
        return {
            'overview': {
                'total_trades': metrics.get('total_trades', 0),
                'winning_trades': metrics.get('winning_trades', 0),
                'losing_trades': metrics.get('losing_trades', 0),
                'win_rate_percent': metrics.get('win_rate', 0),
            },
            'profitability': {
                'total_pnl': metrics.get('total_pnl', 0),
                'avg_pnl': metrics.get('avg_pnl', 0),
                'avg_return_percent': metrics.get('avg_return_percent', 0),
                'gross_profit': metrics.get('gross_profit', 0),
                'gross_loss': metrics.get('gross_loss', 0),
                'profit_factor': metrics.get('profit_factor', 0),
            },
            'risk': {
                'max_drawdown': metrics.get('max_drawdown', 0),
                'max_win': metrics.get('max_win', 0),
                'max_loss': metrics.get('max_loss', 0),
                'avg_risk_reward': metrics.get('avg_risk_reward', 0),
            },
            'trade_analysis': {
                'avg_win': metrics.get('avg_win', 0),
                'avg_loss': metrics.get('avg_loss', 0),
                'expectancy': metrics.get('expectancy', 0),
            }
        }
