"""
Scanner Engine for Trade With Nilay
Orchestrates multiple Chartink scanners, AI scoring, and Telegram alerts.

Production features:
- Multi-scanner support (Swing Pick, VCP, FnO, Rocket)
- NSE Cash segment only (no ETFs, Indices, Funds)
- AI confidence filtering for Telegram (score >= 8.0)
- Automatic deduplication
- Continuous scanning mode
- Database storage
- Telegram notifications
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import (
    insert_scanner, insert_scanner_result, get_scanner_results,
    mark_scanner_alerted, get_conn, update_scanner_result_ai
)
from scanner.chartink_scanner import ChartinkScanner
from services.telegram_v2 import send_scanner_alert, send_equity_filter_alert, get_notifier
from ai.scorer import AIScorer
from ai.explainer import generate_explanation
from strategy.patterns import DojiStrategy, InsideBarStrategy, DeadVolumeStrategy, AdvancedPatternsStrategy
from strategy.breakout import BreakoutStrategy
import yfinance as yf
import pandas as pd

logger = logging.getLogger("twn.scanner_engine")


class ScannerEngine:
    """
    Main scanner orchestration engine
    
    Manages multiple Chartink scanners, applies filters, sends alerts
    """
    
    def __init__(self):
        """Initialize scanner engine"""
        self.scanners: List[Dict] = []
        self.alerted_symbols: Set[str] = set()  # Prevent duplicate alerts
        self.scan_interval = 60  # seconds between scans
        self.scorer = AIScorer()
        self.strategies = [DojiStrategy(), InsideBarStrategy(), DeadVolumeStrategy(), BreakoutStrategy(), AdvancedPatternsStrategy()]
        
        logger.info("Scanner Engine initialized with AI Scorer")
    
    def add_scanner(self, name: str, url: str, scanner_type: str = 'equity', description: str = None, scan_clause: str = None):
        """
        Add a Chartink scanner
        
        Args:
            name: Scanner name
            url: Full Chartink URL (or /process for clause-based)
            scanner_type: 'equity' or 'fno'
            description: Optional description
            scan_clause: Optional raw scan clause
        """
        # Store in database
        scanner_id = insert_scanner(name, url, scanner_type, description)
        
        # Create scanner object
        scanner_obj = ChartinkScanner(url, name)
        
        self.scanners.append({
            'id': scanner_id,
            'name': name,
            'url': url,
            'type': scanner_type,
            'scanner': scanner_obj,
            'scan_clause': scan_clause
        })
        
        logger.info(f"Added scanner: {name} (ID: {scanner_id})")
    
    def apply_equity_filter(self, stocks: List[Dict], min_change: float = 0.0, max_change: float = 3.0) -> List[Dict]:
        """
        Filter stocks by % change range
        
        Args:
            stocks: List of stock dicts
            min_change: Minimum % change (default: 0%)
            max_change: Maximum % change (default: 3%)
        
        Returns:
            Filtered list of stocks
        """
        filtered = []
        
        for stock in stocks:
            change_pct = stock.get('change_pct')
            
            if change_pct is None:
                continue
            
            # Check if within range
            if min_change <= change_pct <= max_change:
                filtered.append(stock)
        
        if filtered:
            logger.info(f"Equity filter: {len(filtered)}/{len(stocks)} stocks in range {min_change}% to {max_change}%")
        
        return filtered
    
    def run_scanner(self, scanner_config: Dict) -> List[Dict]:
        """
        Run a single scanner
        
        Args:
            scanner_config: Scanner configuration dict
        
        Returns:
            List of stock results
        """
        scanner_id = scanner_config['id']
        scanner_name = scanner_config['name']
        scanner_type = scanner_config['type']
        scanner_obj = scanner_config['scanner']
        
        logger.info(f"Running scanner: {scanner_name}")
        
        try:
            # Fetch results from Chartink
            scan_clause = scanner_config.get('scan_clause')
            results = scanner_obj.fetch_results(use_cache=True, scan_clause=scan_clause)
            
            if not results:
                logger.warning(f"No results from scanner: {scanner_name}")
                return []
            
            logger.info(f"Got {len(results)} results from {scanner_name}")
            
            # Store in database
            now_ts = int(time.time())
            for stock in results:
                stock['timestamp'] = now_ts
                try:
                    insert_scanner_result(
                        scanner_id=scanner_id,
                        symbol=stock['symbol'],
                        price=stock.get('price'),
                        change_pct=stock.get('change_pct'),
                        volume=stock.get('volume'),
                        timestamp=now_ts
                    )
                except Exception as e:
                    logger.debug(f"Error storing result for {stock.get('symbol')}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running scanner {scanner_name}: {e}", exc_info=True)
            return []
    
    def run_all_scanners(self) -> List[Dict]:
        """
        Run all configured scanners and return stocks with their scanner type
        
        Returns:
            List of stock dicts with 'scanner_type' added
        """
        all_stocks = []
        
        for scanner_config in self.scanners:
            results = self.run_scanner(scanner_config)
            # Tag each stock with its source scanner type for categorization later
            for stock in results:
                stock['scanner_type'] = scanner_config['type']
            all_stocks.extend(results)
        
        return all_stocks
    
    def deduplicate_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """Remove stocks that were already alerted"""
        new_stocks = []
        
        for stock in stocks:
            symbol = stock.get('symbol')
            if symbol and symbol not in self.alerted_symbols:
                new_stocks.append(stock)
                self.alerted_symbols.add(symbol)
        
        if len(new_stocks) < len(stocks):
            logger.info(f"Deduplication: {len(stocks) - len(new_stocks)} stocks already alerted")
        
        return new_stocks
    
    def get_ai_analysis(self, stock: Dict) -> Dict:
        """Fetch historical data and get AI score for a stock"""
        original_symbol = stock['symbol']
        # Clean symbol for yfinance
        clean_symbol = original_symbol.split(' ')[0].split('(')[0].strip().upper()
        
        df = pd.DataFrame()
        used_ticker = ""
        
        try:
            # 1. Try NSE first
            used_ticker = f"{clean_symbol}.NS"
            ticker = yf.Ticker(used_ticker)
            df = ticker.history(period="60d", interval="1d")
            
            # 2. Try BSE fallback if NSE empty
            if df.empty:
                used_ticker = f"{clean_symbol}.BO"
                ticker = yf.Ticker(used_ticker)
                df = ticker.history(period="60d", interval="1d")
                
            if df.empty or len(df) < 20:
                logger.warning(f"Insufficient history for {original_symbol}. Using fallback scoring.")
                # Fallback: Basic score based ONLY on live price/volume from scanner
                setup_data = {
                    "price_action": {
                        "change_pct": stock.get('change_pct', 0),
                        "volume_mult": 1.5, # Assume decent if scanner picked it up
                        "trend": "NEUTRAL",
                        "rsi": 50,
                        "partial_data": True
                    },
                    "strategies": [],
                    "fno": {}
                }
                analysis = self.scorer.score_setup(clean_symbol, setup_data)
                analysis['reasons'].append("Note: Full technicals skipped (No history)")
                return analysis
            
            # Lowercase columns for strategy compatibility
            df.columns = [c.lower() for c in df.columns]
            
            # 3. Calc Indicators
            df['rsi'] = calculate_rsi(df['close'])
            df['ema_20'] = calculate_ema(df['close'], 20)
            df['ema_50'] = calculate_ema(df['close'], 50)
            
            # 4. Strategy Confluence
            active_patterns = []
            for strat in self.strategies:
                signals = strat.analyze(df)
                if signals:
                    active_patterns.extend(signals)
            
            # 5. Build setup dict for scorer
            avg_vol = df['volume'].mean() if df['volume'].mean() > 0 else 1
            setup_data = {
                "price_action": {
                    "change_pct": stock.get('change_pct', 0),
                    "volume_mult": stock.get('volume', 0) / avg_vol,
                    "trend": "UPTREND" if df.iloc[-1]['close'] > df.iloc[-1]['ema_50'] else "DOWNTREND",
                    "rsi": df.iloc[-1]['rsi']
                },
                "strategies": active_patterns,
                "fno": {} # Add FnO bias later if needed
            }
            
            # 6. Get Primary Pattern for display
            from backend.strategy.pattern_detector import PatternDetector
            detector = PatternDetector()
            pattern_analysis = detector.analyze(df, clean_symbol)
            
            analysis = self.scorer.score_setup(clean_symbol, setup_data)
            analysis['primary_pattern'] = pattern_analysis.get('primary_pattern')
            
            return analysis
        except Exception as e:
            logger.error(f"AI Analysis failed for {original_symbol}: {e}")
            return {"score": 0.0, "rating": "ERROR", "reasons": [f"Runtime error: {str(e)}"]}

    def run_once(self, send_alerts: bool = True) -> Dict:
        """
        Run all scanners once
        
        Args:
            send_alerts: Send Telegram alerts for results
        
        Returns:
            Dict with statistics
        """
        logger.info("=" * 60)
        logger.info("Starting scanner run")
        logger.info("=" * 60)
        
        stats = {
            'total_scanners': len(self.scanners),
            'total_stocks': 0,
            'filtered_stocks': 0,
            'alerted_stocks': 0,
            'start_time': time.time()
        }
        
        # Run all scanners
        merged_stocks = self.run_all_scanners()
        
        # Remove duplicates by symbol (Keep priority to FnO or highest change)
        unique_stocks = {}
        for stock in merged_stocks:
            symbol = stock.get('symbol')
            if symbol:
                if symbol not in unique_stocks:
                    unique_stocks[symbol] = stock
                else:
                    # If duplicate, keep FnO type if available
                    if stock.get('scanner_type') == 'fno':
                        unique_stocks[symbol] = stock
        
        merged_stocks = list(unique_stocks.values())
        stats['total_stocks'] = len(merged_stocks)
        
        logger.info(f"Total unique stocks from all scanners: {stats['total_stocks']}")
        
        # --- NSE CASH FILTER ONLY (No SwingAlgo 0-3% restriction) ---
        def is_nse_cash(stock):
            sym = stock.get('symbol', '').upper()
            exclude_keywords = ['NIFTY', 'BANKNIFTY', 'BEES', 'ETF', 'FUND', 'GOLD',
                                'REIT', 'INVIT', 'INDEX', 'LIQUID', 'SILVER', 'NASDAQ']
            if any(k in sym for k in exclude_keywords):
                return False
            if '-' in sym:
                return False
            return True

        filtered_stocks = [s for s in merged_stocks if is_nse_cash(s)]
        stats['filtered_stocks'] = len(filtered_stocks)
        logger.info(f"NSE Cash filter: {len(filtered_stocks)}/{len(merged_stocks)} stocks passed")
        
        if filtered_stocks:
            # Deduplicate (don't alert same stock twice in one run)
            new_stocks = self.deduplicate_stocks(filtered_stocks)
            
            if new_stocks and send_alerts:
                logger.info(f"Scoring and alerting {len(new_stocks)} stocks...")
                notifier = get_notifier()
                
                for stock in new_stocks:
                    try:
                        # 1. AI Score
                        analysis = self.get_ai_analysis(stock)
                        stock['ai_analysis'] = analysis
                        stock['explanation'] = generate_explanation(analysis, stock['symbol'])
                        
                        # 2. Category
                        patterns = [s.get('pattern') for s in analysis.get('strategies', [])]
                        primary_pattern = analysis.get('primary_pattern') or (patterns[0] if patterns else "Market Setup")
                        
                        category = "Rocket"  # Default
                        if "IPO_BASE" in patterns or "IPB" in patterns:
                            category = "IPO"
                        elif "VCP" in patterns:
                            category = "VCP"
                        elif stock.get('scanner_type') == 'fno':
                            category = "FNO"
                        elif stock.get('change_pct', 0) > 4.0:
                            category = "Rocket"
                        
                        final_pattern = f"{category} | {primary_pattern}"
                        
                        # 3. Confidence gate — only alert high-conviction setups
                        is_high_confidence = analysis.get('score', 0) >= 8.0
                        
                        # 4. Always update database
                        update_scanner_result_ai(
                            symbol=stock['symbol'],
                            timestamp=stock.get('timestamp'),
                            ai_score=analysis.get('score'),
                            ai_rating=analysis.get('rating'),
                            patterns=final_pattern
                        )

                        # 5. Send Telegram only for high-confidence
                        if send_alerts and is_high_confidence:
                            header = f"AI {category.upper()} SETUP"
                            emojis = "🔔"
                            if category == "VCP":
                                header = "🏆 CONVICTION VCP SETUP"
                                emojis = "💎💎💎"
                            elif category == "IPO":
                                header = "💰 IPO BASE SETUP"
                                emojis = "🌟"
                            elif category == "Rocket":
                                header = "🚀 MOMENTUM ROCKET"
                                emojis = "🔥"
                            if "BREAKOUT" in patterns:
                                header = f"💥 BREAKOUT: {category}"
                                emojis = "⚡"
                            
                            message = (
                                f"{emojis} *{header}*\n"
                                f"🌐 *Symbol:* `{stock['symbol']}`\n\n"
                                f"📝 *Analysis:* {stock['explanation']}\n\n"
                                f"📊 *Stats:*\n"
                                f"├ Price: ₹{stock['price']:,.2f} ({stock['change_pct']:+.2f}%)\n"
                                f"├ Volume: {stock['volume']:,}\n"
                                f"└ Score: *{analysis['score']}/10* ({analysis['rating']})\n\n"
                                f"🔍 *Setup:* {final_pattern}\n"
                                f"⏰ *Time:* {datetime.now().strftime('%H:%M IST')}\n\n"
                                f"🎯 _Trade With Nilay Terminal_"
                            )
                            notifier.send_message(message)
                            stats['alerted_stocks'] += 1
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error scoring/alerting {stock.get('symbol')}: {e}")
        else:
            logger.info("No NSE Cash stocks found after filtering")
        
        stats['duration_sec'] = time.time() - stats['start_time']
        
        logger.info("=" * 60)
        logger.info("Scanner run complete")
        logger.info(f"  Total stocks:   {stats['total_stocks']}")
        logger.info(f"  After NSE Cash: {stats['filtered_stocks']}")
        logger.info(f"  Alerted:        {stats['alerted_stocks']}")
        logger.info(f"  Duration:       {stats['duration_sec']:.1f}s")
        logger.info("=" * 60)
        
        return stats
    
    def run_continuous(self, interval: int = None):
        """
        Run scanners continuously in a loop
        
        Args:
            interval: Seconds between scans (default: 60)
        """
        interval = interval or self.scan_interval
        
        logger.info("=" * 60)
        logger.info("SCANNER ENGINE - CONTINUOUS MODE")
        logger.info("=" * 60)
        logger.info(f"Scanners: {len(self.scanners)}")
        logger.info(f"Scan interval: {interval} seconds")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        cycle = 0
        
        while True:
            try:
                cycle += 1
                logger.info(f"\n>>> Scan Cycle {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                stats = self.run_once(send_alerts=True)
                
                # Wait before next scan
                logger.info(f"\nWaiting {interval} seconds before next scan...\n")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("\n\nScanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scanner loop: {e}", exc_info=True)
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
    
    def clear_alert_history(self):
        """Clear the alerted symbols set (for testing)"""
        self.alerted_symbols.clear()
        logger.info("Alert history cleared")


if __name__ == "__main__":
    # Test the scanner engine
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("TESTING SCANNER ENGINE")
    logger.info("=" * 60)
    
    # Create engine
    engine = ScannerEngine()
    
    # Add Nilay's scanners
    engine.add_scanner(
        name="Nilay Swing Pick Algo",
        url="https://chartink.com/screener/nilay-swing-pick-algo",
        scanner_type="equity"
    )
    
    engine.add_scanner(
        name="Nilay Swing Pick 2.0",
        url="https://chartink.com/screener/nilay-swing-pick-2-0",
        scanner_type="equity"
    )

    engine.add_scanner(
        name="NILAY FNO VOLATILITY SCAN",
        url="https://chartink.com/screener/process",
        scanner_type="fno",
        scan_clause="( {33489} ( daily avg true range( 14 ) < 10 days ago avg true range( 14 ) and daily avg true range( 14 ) / daily close < 0.08 and daily close > ( weekly max( 52 , weekly close ) * 0.75 ) and daily ema( daily close , 50 ) > daily ema( daily close , 150 ) and daily ema( daily close , 150 ) > daily ema( daily close , 200 ) and daily close > daily ema( daily close , 50 ) and daily close > 10 and daily close * daily volume > 1000000 ) ) "
    )
    
    engine.add_scanner(
        name="Nilay FnO Autopick",
        url="https://chartink.com/screener/nilay-fno-autopick-scanner",
        scanner_type="fno"
    )
    
    logger.info(f"\nConfigured scanners: {len(engine.scanners)}\n")
    
    # Run once for testing
    # stats = engine.run_once(send_alerts=True)
    
    # Run continuously in production
    engine.run_continuous(interval=60)
