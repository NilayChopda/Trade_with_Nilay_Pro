"""
Scanner Results Verification & Dashboard Generator
Tests scanner accuracy and creates visual dashboard for comparison with Charting.in
"""

import pandas as pd
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_latest_scan_results():
    """Load the most recent scan results"""
    scanner_results_dir = '../scanner_results'
    
    # Find all CSV files
    csv_files = [f for f in os.listdir(scanner_results_dir) if f.startswith('results_') and f.endswith('.csv')]
    
    if not csv_files:
        logger.error("No scanner results found!")
        return None, None
    
    # Get the latest one
    csv_files.sort()
    latest_file = csv_files[-1]
    
    filepath = os.path.join(scanner_results_dir, latest_file)
    df = pd.read_csv(filepath)
    
    logger.info(f"✓ Loaded: {latest_file}")
    logger.info(f"✓ Records: {len(df)}")
    
    return df, latest_file


def verify_against_charking_format():
    """Display data in format easy to verify against Charting.in"""
    
    df, filename = load_latest_scan_results()
    
    if df is None:
        return
    
    # Extract date from filename: results_20260127_2332.csv -> 2026-01-27
    date_part = filename.split('_')[1]  # 20260127
    scan_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
    
    logger.info("\n" + "="*80)
    logger.info("SCANNER RESULTS - READY TO VERIFY ON CHARTING.IN")
    logger.info("="*80)
    logger.info(f"\nScan Date: {scan_date}")
    logger.info(f"Results File: {filename}")
    logger.info(f"Total Signals: {len(df)}")
    logger.info(f"Passed Filter: {df['passes_filter'].sum()}")
    
    # Filter only those that passed filter
    df_passed = df[df['passes_filter'] == True].copy()
    df_passed = df_passed.sort_values('price', ascending=False)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TOP 20 SIGNALS TO VERIFY:")
    logger.info(f"{'='*80}\n")
    logger.info(f"{'Rank':<6} {'Symbol':<12} {'Price':<12} {'Change':<10} {'Volume':<15}")
    logger.info(f"{'-'*80}\n")
    
    for idx, (_, row) in enumerate(df_passed.head(20).iterrows(), 1):
        logger.info(
            f"{idx:<6} {str(row['symbol']):<12} ₹{row['price']:<11.2f} "
            f"{row['change']:>8.2f}% {row['volume']:>14.0f}"
        )
    
    return df_passed, scan_date


def create_verification_html(df_passed, scan_date):
    """Create HTML dashboard for verification"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSE Scanner Results - {scan_date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }}
        
        .stat-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-box h3 {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-box .number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .instructions {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            color: #856404;
        }}
        
        .instructions h4 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .instructions ol {{
            margin-left: 20px;
        }}
        
        .instructions li {{
            margin-bottom: 8px;
        }}
        
        .instructions strong {{
            color: #333;
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        thead {{
            background: #667eea;
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        tr:nth-child(even) {{
            background: #fafafa;
        }}
        
        .rank {{
            font-weight: bold;
            color: #667eea;
            width: 50px;
        }}
        
        .symbol {{
            font-weight: bold;
            color: #333;
        }}
        
        .price {{
            color: #27ae60;
            font-weight: 600;
        }}
        
        .change {{
            font-weight: 600;
        }}
        
        .change.positive {{
            color: #27ae60;
        }}
        
        .change.negative {{
            color: #e74c3c;
        }}
        
        .volume {{
            color: #7f8c8d;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #ddd;
        }}
        
        .comparison-note {{
            background: #e8f4f8;
            border: 1px solid #5cb3cc;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            color: #1a5c7a;
        }}
        
        .comparison-note h5 {{
            margin-bottom: 10px;
        }}
        
        .comparison-note ul {{
            margin-left: 20px;
        }}
        
        .comparison-note li {{
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 NSE Scanner Results</h1>
            <p>Signals detected on {scan_date} | Ready for verification</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>Total Signals</h3>
                <div class="number">{len(df_passed)}</div>
            </div>
            <div class="stat-box">
                <h3>Scan Date</h3>
                <div class="number">{scan_date}</div>
            </div>
            <div class="stat-box">
                <h3>Data Status</h3>
                <div class="number">✓ Ready</div>
            </div>
            <div class="stat-box">
                <h3>Action</h3>
                <div class="number">📋 Verify</div>
            </div>
        </div>
        
        <div class="content">
            <div class="instructions">
                <h4>✅ How to Verify Against Charting.in</h4>
                <ol>
                    <li><strong>Open Charting.in</strong> in your browser (charting.in)</li>
                    <li><strong>Select each symbol</strong> from the list below</li>
                    <li><strong>Set date to {scan_date}</strong> (when scan was run)</li>
                    <li><strong>Check the price</strong> at market close on that date</li>
                    <li><strong>Compare with the price column</strong> - they should match</li>
                    <li><strong>Verify volume</strong> matches the volume column</li>
                    <li><strong>Check if patterns match</strong> your indicator setup</li>
                </ol>
            </div>
            
            <h3>📈 Signals Detected</h3>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th class="rank">#</th>
                            <th>Symbol</th>
                            <th>Company Name</th>
                            <th>Price (Close)</th>
                            <th>Change %</th>
                            <th>Volume</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Add table rows
    for idx, (_, row) in enumerate(df_passed.head(50).iterrows(), 1):
        change_class = "positive" if row['change'] >= 0 else "negative"
        html_content += f"""
                        <tr>
                            <td class="rank">{idx}</td>
                            <td class="symbol">{row['symbol']}</td>
                            <td>{row['name']}</td>
                            <td class="price">₹{row['price']:.2f}</td>
                            <td class="change {change_class}">{row['change']:.2f}%</td>
                            <td class="volume">{int(row['volume']):,}</td>
                        </tr>
"""
    
    html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="comparison-note">
                <h5>🔍 Verification Checklist</h5>
                <ul>
                    <li>Price on Charting.in matches the "Price (Close)" column</li>
                    <li>Volume on Charting.in matches the "Volume" column</li>
                    <li>All listed symbols are NSE securities (not forex/crypto)</li>
                    <li>Patterns visible on date match your criteria</li>
                    <li>No data discrepancies or red flags</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ | 
            Data Source: NSE Scanner | 
            Status: Pending Verification
        </div>
    </div>
</body>
</html>
"""
    
    # Write to file
    output_file = f'verification_dashboard_{scan_date.replace("-", "")}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"\n✓ Dashboard created: {output_file}")
    logger.info(f"  Open in browser to view detailed comparison")
    
    return output_file


def export_data_for_comparison():
    """Export data in multiple formats"""
    
    df, filename = load_latest_scan_results()
    
    if df is None:
        return
    
    date_part = filename.split('_')[1]
    scan_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
    
    # Filter passed
    df_passed = df[df['passes_filter'] == True].copy()
    df_passed = df_passed.sort_values('price', ascending=False)
    
    # Export CSV for comparison
    csv_export = f'verification_data_{scan_date.replace("-", "")}.csv'
    df_passed[['symbol', 'name', 'price', 'change', 'volume']].to_csv(csv_export, index=False)
    logger.info(f"✓ Exported CSV: {csv_export}")
    
    # Export JSON
    json_export = f'verification_data_{scan_date.replace("-", "")}.json'
    json_data = {
        'scan_date': scan_date,
        'total_signals': len(df_passed),
        'signals': df_passed[['symbol', 'name', 'price', 'change', 'volume']].to_dict('records')
    }
    with open(json_export, 'w') as f:
        json.dump(json_data, f, indent=2)
    logger.info(f"✓ Exported JSON: {json_export}")
    
    return df_passed, scan_date


def send_telegram_verification_alert():
    """Send verification alert to Telegram"""
    try:
        from bot.telegram_bot import ScannerBot
        import os
        
        token = os.getenv('TG_BOT_TOKEN')
        chat_id = os.getenv('TG_CHAT_ID')
        
        if not token or not chat_id:
            logger.warning("⚠ Telegram credentials not set")
            return
        
        df, filename = load_latest_scan_results()
        if df is None:
            return
        
        date_part = filename.split('_')[1]
        scan_date = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
        
        df_passed = df[df['passes_filter'] == True]
        
        bot = ScannerBot(token, chat_id)
        
        message = f"""
✅ **SCANNER RESULTS - VERIFICATION MODE**

📅 Scan Date: {scan_date}
📊 Total Signals: {len(df_passed)}
🔍 Status: Ready for verification

**Top 5 Signals:**
"""
        
        for idx, (_, row) in enumerate(df_passed.head(5).iterrows(), 1):
            message += f"\n{idx}. **{row['symbol']}** - ₹{row['price']:.2f} ({row['change']:+.2f}%)"
        
        message += f"""

**Next Steps:**
1️⃣ Open Charting.in
2️⃣ Check each symbol on {scan_date}
3️⃣ Verify prices & volume match
4️⃣ Confirm pattern matches your setup

✓ Verification dashboard created
✓ Data exported to CSV & JSON
"""
        
        bot.send_message(message)
        logger.info("✓ Telegram verification alert sent!")
        
    except Exception as e:
        logger.warning(f"Could not send Telegram alert: {e}")


def main():
    """Main execution"""
    logger.info("\n" + "="*80)
    logger.info("NSE SCANNER RESULTS - VERIFICATION MODE")
    logger.info("="*80 + "\n")
    
    # Load and display results
    df_passed, scan_date = verify_against_charking_format()
    
    if df_passed is None or len(df_passed) == 0:
        logger.error("No signals found!")
        return
    
    # Create dashboard
    dashboard_file = create_verification_html(df_passed, scan_date)
    
    # Export data
    export_data_for_comparison()
    
    # Send Telegram alert
    send_telegram_verification_alert()
    
    # Final instructions
    logger.info("\n" + "="*80)
    logger.info("VERIFICATION COMPLETE - NEXT STEPS")
    logger.info("="*80)
    logger.info(f"\n1. Open {dashboard_file} in your browser")
    logger.info(f"2. Visit charting.in and select each symbol")
    logger.info(f"3. Check date: {scan_date}")
    logger.info(f"4. Verify prices match the dashboard")
    logger.info(f"5. Check if patterns align with your criteria")
    logger.info(f"\nFiles created:")
    logger.info(f"  • {dashboard_file}")
    logger.info(f"  • verification_data_{scan_date.replace('-', '')}.csv")
    logger.info(f"  • verification_data_{scan_date.replace('-', '')}.json")
    logger.info("\n✓ All data ready for comparison!\n")


if __name__ == '__main__':
    main()
