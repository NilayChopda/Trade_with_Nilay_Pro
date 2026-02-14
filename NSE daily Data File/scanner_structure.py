"""
SCANNER STRUCTURE - Shows how your full scanner will work
"""
import pandas as pd
from scanner_core import WMACalculator
from datetime import datetime

class StockScanner:
    """
    Main scanner class - will scan all 2773 stocks
    """
    
    def __init__(self):
        self.calculator = WMACalculator()
        print("📊 Stock Scanner Initialized")
    
    def load_stocks(self):
        """Load your 2773 NSE stocks"""
        try:
            # Load from your symbols file
            with open('nse_scanner_symbols.txt', 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            
            # Load from your CSV for names
            df = pd.read_csv('nse_scanner_current.csv')
            
            print(f"✅ Loaded {len(symbols)} stocks")
            print(f"Sample: {symbols[:5]}")
            
            return symbols, df
            
        except Exception as e:
            print(f"❌ Error loading stocks: {e}")
            return [], pd.DataFrame()
    
    def get_sample_prices(self, symbol):
        """
        TODO: This will fetch real prices from TradingView
        For now, returns sample data
        """
        # Sample price data (in real scanner, fetch from TradingView)
        import random
        base_price = random.randint(50, 5000)
        prices = [base_price + random.randint(-20, 20) for _ in range(30)]
        return prices
    
    def scan_single_stock(self, symbol, name=""):
        """
        Scan one stock with scanner logic
        """
        # Get prices (will be from TradingView on Feb 6th)
        prices = self.get_sample_prices(symbol)
        
        # Calculate WMAs
        wmas = self.calculator.calculate_all_wmas(prices)
        
        if not wmas:
            return None
        
        # Check conditions
        passes = self.calculator.check_scanner_conditions(wmas)
        
        # Calculate % change (for post-filter)
        if len(prices) >= 2:
            price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100
        else:
            price_change = 0
        
        return {
            'symbol': symbol,
            'name': name,
            'passes': passes,
            'current_price': prices[-1] if prices else 0,
            'price_change': round(price_change, 2),
            'wmas': wmas
        }
    
    def post_filter(self, results):
        """
        Apply post-filter: Price change between -1% and +2%
        """
        filtered = []
        for result in results:
            if result and -1 <= result['price_change'] <= 2:
                filtered.append(result)
        
        print(f"Post-filter: {len(filtered)}/{len(results)} stocks remain")
        return filtered
    
    def scan_all_stocks(self, test_mode=True):
        """
        Main scanning function
        test_mode=True: Scan only 10 stocks for testing
        """
        print("\n" + "="*50)
        print("🚀 STARTING STOCK SCANNER")
        print("="*50)
        
        # Load stocks
        symbols, df = self.load_stocks()
        
        if test_mode:
            symbols = symbols[:10]  # Test with 10 stocks
            print(f"🧪 TEST MODE: Scanning {len(symbols)} stocks")
        
        results = []
        passing_stocks = []
        
        print(f"\n📈 Scanning {len(symbols)} stocks...")
        
        for i, symbol in enumerate(symbols, 1):
            # Get stock name
            name_row = df[df['SYMBOL'] == symbol]
            name = name_row['NAME'].iloc[0] if not name_row.empty else symbol
            
            # Scan
            result = self.scan_single_stock(symbol, name)
            
            if result:
                results.append(result)
                if result['passes']:
                    passing_stocks.append(result)
            
            # Progress every 100 stocks
            if i % 100 == 0:
                print(f"  Scanned {i}/{len(symbols)} stocks...")
        
        # Apply post-filter
        final_results = self.post_filter(passing_stocks)
        
        # Print summary
        print("\n" + "="*50)
        print("📊 SCANNER RESULTS")
        print("="*50)
        print(f"Total stocks scanned: {len(symbols)}")
        print(f"Passed scanner logic: {len(passing_stocks)}")
        print(f"After post-filter (-1% to +2%): {len(final_results)}")
        
        # Show passing stocks
        if final_results:
            print("\n✅ PASSING STOCKS:")
            for stock in final_results[:5]:  # Show first 5
                print(f"  {stock['symbol']} - {stock['name']}")
                print(f"    Price: ₹{stock['current_price']}, Change: {stock['price_change']}%")
                print(f"    WMAs: D1={stock['wmas']['daily_wma_1']}, M2={stock['wmas']['monthly_wma_2']}")
                print()
        
        return final_results

# RUN THE SCANNER
if __name__ == "__main__":
    scanner = StockScanner()
    
    # Quick test
    print("🧪 Quick test on 1 stock...")
    test_result = scanner.scan_single_stock("RELIANCE", "Reliance Industries")
    if test_result:
        print(f"  Symbol: {test_result['symbol']}")
        print(f"  Passes: {test_result['passes']}")
        print(f"  Price: ₹{test_result['current_price']}")
        print(f"  Change: {test_result['price_change']}%")
    
    # Full test scan (10 stocks)
    print("\n" + "="*50)
    input("Press Enter to run full test scan (10 stocks)...")
    
    results = scanner.scan_all_stocks(test_mode=True)
    
    print("\n🎯 READY FOR FEB 6TH!")
    print("On Feb 6th, we'll:")
    print("1. Replace sample prices with REAL TradingView data")
    print("2. Scan ALL 2773 stocks")
    print("3. Add Telegram alerts")
    print("4. Add web dashboard")