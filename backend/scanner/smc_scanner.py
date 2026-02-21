
import logging
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.services.symbol_manager import get_equity_symbols
from backend.strategy.smc import SMCEngine
from backend.database.db import insert_scanner_result, get_conn, insert_scanner

logger = logging.getLogger(__name__)

class SMCScanner:
    def __init__(self):
        self.engine = SMCEngine()
        # Ensure scanner entry exists
        self.scanner_id = insert_scanner(
            name="SMC_DEMAND_ZONE",
            url="internal",
            scanner_type="equity",
            description="Stocks tapping unmitigated Daily Demand Zones (Bullish OB)"
        )

    def scan_market(self, symbols: list = None, workers: int = 20):
        """
        Scan the market for SMC setups
        """
        if not symbols:
            symbols = get_equity_symbols()
            
        logger.info(f"Starting SMC Scan for {len(symbols)} symbols...")
        
        chunk_size = 100
        results = []
        
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i+chunk_size]
            chunk_results = self.process_chunk(chunk)
            results.extend(chunk_results)
            logger.info(f"Processed {i + len(chunk)}/{len(symbols)} symbols")
            
        return results

    def process_chunk(self, symbols: list):
        """
        Process a batch of symbols with internal parallelization
        """
        valid_setups = []
        yf_symbols = [f"{s}.NS" for s in symbols]
        
        # 1. Batch Download
        data = pd.DataFrame()
        try:
            data = yf.download(yf_symbols, period="6mo", interval="1d", group_by='ticker', progress=False, threads=True)
        except Exception as e:
            logger.warning(f"Batch download failed for chunk: {e}")

        def analyze_single(symbol):
            try:
                df = pd.DataFrame()
                if not data.empty:
                    try:
                        if len(symbols) > 1:
                            df = data[f"{symbol}.NS"].copy()
                        else:
                            df = data.copy()
                    except:
                        pass

                if df.empty or 'Close' not in df.columns:
                    df = yf.download(f"{symbol}.NS", period="6mo", interval="1d", progress=False)

                if df.empty or len(df) < 30:
                    return None

                df.columns = [c.lower() for c in df.columns]
                df['timestamp'] = df.index
                
                setup = self.engine.check_setup(df)
                if setup and setup['score'] >= 6:
                    current_price = float(df['close'].iloc[-1])
                    insert_scanner_result(
                        scanner_id=self.scanner_id,
                        symbol=symbol,
                        price=current_price,
                        change_pct=0.0,
                        volume=int(df['volume'].iloc[-1]),
                        sector="SMC Analysis"
                    )
                    return {
                        'symbol': symbol,
                        'price': current_price,
                        'volume': int(df['volume'].iloc[-1]),
                        'setup': setup
                    }
            except:
                pass
            return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_sym = {executor.submit(analyze_single, sym): sym for sym in symbols}
            for future in as_completed(future_to_sym):
                res = future.result()
                if res:
                    valid_setups.append(res)
                    
        return valid_setups

if __name__ == "__main__":
    scanner = SMCScanner()
    test_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "TATAMOTORS", "SBIN"] 
    results = scanner.scan_market(test_symbols)
    print(f"Found {len(results)} setups")
    for r in results:
        print(r)
