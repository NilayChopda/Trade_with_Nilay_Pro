"""
Main Scanner with KITE API Integration
Scans ALL 2700+ NSE securities with real-time prices
Sends alerts to Telegram bot immediately upon signal detection
"""

import logging
import os
import argparse
from datetime import datetime
from core.kite_fetcher import KITEDataFetcher, YAMLConfigKITE
from scanner_kite_enhanced import KITEScannerEnhanced
from bot.telegram_bot import ScannerBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner_kite.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_kite_fetcher():
    """Initialize KITE API fetcher"""
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key or not access_token:
        raise ValueError(
            "Set environment variables:\n"
            "  KITE_API_KEY = Your Zerodha API Key\n"
            "  KITE_ACCESS_TOKEN = Your KITE Access Token\n\n"
            "Get these from: https://console.zerodha.com"
        )
    
    return KITEDataFetcher(api_key, access_token)


def run_scan_all_nse(limit: int = None):
    """Scan ALL NSE securities"""
    logger.info("="*70)
    logger.info("NSE SCANNER WITH KITE API - SCAN ALL SECURITIES")
    logger.info("="*70)
    
    try:
        # Initialize KITE fetcher
        fetcher = get_kite_fetcher()
        logger.info("✓ KITE API connection established")
        
        # Initialize scanner with Telegram bot
        telegram_token = os.getenv('TG_BOT_TOKEN')
        telegram_chat_id = os.getenv('TG_CHAT_ID')
        
        scanner = KITEScannerEnhanced(
            fetcher,
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat_id
        )
        logger.info("✓ Scanner initialized")
        
        if telegram_token and telegram_chat_id:
            logger.info("✓ Telegram bot connected for real-time alerts")
            scanner.bot.send_message(
                f"🚀 <b>NSE Scanner Started</b>\n\n"
                f"Scanning Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Data Source: Zerodha KITE API\n"
                f"Price Accuracy: LIVE\n"
            )
        
        # Run scan for all NSE securities
        logger.info("Fetching all NSE securities...")
        symbols = fetcher.get_all_nse_symbols()
        
        if limit:
            logger.info(f"Limiting scan to {limit} symbols for testing")
            symbols = symbols[:limit]
        
        logger.info(f"Starting scan for {len(symbols)} NSE securities...")
        results_df = scanner.run_scan(symbols, max_workers=15)
        
        # Rank results
        if not results_df.empty:
            logger.info("Ranking signals...")
            ranked_df = scanner.rank_results(results_df, top_n=20)
            
            logger.info(f"\n{'='*70}")
            logger.info(f"TOP {len(ranked_df)} SIGNALS")
            logger.info(f"{'='*70}")
            
            print(ranked_df[[
                'symbol', 'score', 'close', 'current_ltp', 
                'ob_low', 'ob_high', 'volume'
            ]].to_string())
            
            # Save results
            output_file = f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            ranked_df.to_csv(output_file)
            logger.info(f"\n✓ Results saved to {output_file}")
            
            # Send summary to Telegram
            if telegram_token and telegram_chat_id:
                summary = (
                    f"✅ <b>Scan Complete!</b>\n\n"
                    f"Total Symbols: {len(symbols)}\n"
                    f"Signals Found: {len(results_df)}\n"
                    f"Top 20 Ranked: Sent above\n"
                )
                scanner.bot.send_message(summary)
        else:
            logger.warning("No signals found in this scan")
            if telegram_token and telegram_chat_id:
                scanner.bot.send_message(
                    f"⚠️ <b>Scan Complete</b>\n\n"
                    f"Symbols Scanned: {len(symbols)}\n"
                    f"Signals Found: 0\n"
                )
        
        logger.info("="*70)
        logger.info("Scan completed successfully!")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"Error during scan: {e}", exc_info=True)
        raise


def run_scan_symbols(symbols_list: list):
    """Scan specific symbols"""
    logger.info("="*70)
    logger.info("NSE SCANNER - SCAN SPECIFIC SYMBOLS")
    logger.info("="*70)
    logger.info(f"Scanning: {', '.join(symbols_list)}")
    
    try:
        fetcher = get_kite_fetcher()
        
        telegram_token = os.getenv('TG_BOT_TOKEN')
        telegram_chat_id = os.getenv('TG_CHAT_ID')
        
        scanner = KITEScannerEnhanced(
            fetcher,
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat_id
        )
        
        results_df = scanner.run_scan(symbols_list)
        
        if not results_df.empty:
            ranked_df = scanner.rank_results(results_df)
            print(ranked_df.to_string())
        else:
            logger.info("No signals found in selected symbols")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(
        description='NSE Scanner with KITE API - Real-time Prices from Zerodha'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Scan ALL NSE securities (2700+)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit scan to N symbols (for testing)'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Scan specific symbols: --symbols INFY TCS WIPRO'
    )
    
    args = parser.parse_args()
    
    if args.all:
        run_scan_all_nse(limit=args.limit)
    elif args.symbols:
        run_scan_symbols(args.symbols)
    else:
        # Default: scan all
        run_scan_all_nse()


if __name__ == '__main__':
    main()
