import os
import sys
import logging
import argparse
from scanner import Scanner
from bot.telegram_bot import ScannerBot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_symbols(filepath='symbols.txt'):
    if not os.path.exists(filepath):
        logger.error(f"Symbols file not found: {filepath}")
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description='NSE TradingView Scanner with Signal Ranking')
    parser.add_argument('--rank', action='store_true', help='Enable signal ranking system')
    parser.add_argument('--top-n', type=int, default=10, help='Return top N ranked stocks (default: 10)')
    parser.add_argument('--ob-symbols', type=str, help='CSV of symbols where OB tapped')
    parser.add_argument('--swing-symbols', type=str, help='CSV of symbols with swing condition')
    parser.add_argument('--doji-symbols', type=str, help='CSV of symbols with doji pattern')
    parser.add_argument('--cons-symbols', type=str, help='CSV of symbols with consolidation')
    parser.add_argument('--vol-symbols', type=str, help='CSV of symbols with volume spike')
    
    args = parser.parse_args()
    
    logger.info("Starting NSE TradingView Scanner...")
    
    # Credentials from Env
    tv_username = os.getenv('TV_USERNAME')
    tv_password = os.getenv('TV_PASSWORD')
    
    # 1. Initialize Scanner
    scanner = Scanner(username=tv_username, password=tv_password)
    
    # 2. Load Symbols
    symbols = load_symbols()
    if not symbols:
        logger.error("No symbols to scan. Exiting.")
        return

    # 3. Run Scan
    # Adjust max_workers based on env or default (2 for free tier/local to be safe, 5-10 for cloud)
    results_df = scanner.run_scan(symbols, max_workers=5)
    
    # 4. Rank results if requested
    if args.rank and not results_df.empty:
        logger.info("Ranking signals...")
        
        # Parse signal symbols
        ob_symbols = args.ob_symbols.split(',') if args.ob_symbols else []
        swing_symbols = args.swing_symbols.split(',') if args.swing_symbols else []
        doji_symbols = args.doji_symbols.split(',') if args.doji_symbols else []
        cons_symbols = args.cons_symbols.split(',') if args.cons_symbols else []
        vol_symbols = args.vol_symbols.split(',') if args.vol_symbols else []
        
        results_df = scanner.rank_results(
            results_df,
            ob_tapped_symbols=ob_symbols,
            swing_valid_symbols=swing_symbols,
            doji_symbols=doji_symbols,
            consolidation_symbols=cons_symbols,
            volume_spike_symbols=vol_symbols,
            top_n=args.top_n
        )
        
        # Print ranking report
        print(scanner.ranking_engine.format_ranking_report(
            scanner.ranking_engine.ranked_signals
        ))
        
        # Print summary stats
        stats = scanner.ranking_engine.get_summary_stats(scanner.ranking_engine.ranked_signals)
        logger.info(f"Summary Stats: {stats}")
    
    # Save results for Dashboard/History
    if not results_df.empty:
        results_df.to_csv('results.csv', index=False)
        logger.info("Saved results to results.csv")
    else:
        # Create empty file or do nothing? Better to have file for dashboard
        with open('results.csv', 'w') as f:
            f.write("symbol,close,pct_change,volume,d_wma1,m_wma2\n")

    # 5. Send Results via Telegram
    bot = ScannerBot()
    if not results_df.empty:
        logger.info(f"Found {len(results_df)} matches. Sending to Telegram...")
        bot.send_results(results_df)
    else:
        logger.info("No matches found.")
        bot.send_message("Scanner finished. No stocks matched both Logic and Post-Filter (+- 1-2%).")

    logger.info("Scan completed successfully.")

if __name__ == "__main__":
    main()
