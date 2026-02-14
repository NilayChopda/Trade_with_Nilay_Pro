"""
NilayChopdaScanner - Filtered Results (Price: 50-2000)
Live Scanner with Price Range Filter
"""

import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_filter_results(min_price=50, max_price=2000):
    """Load scanner results and filter by price range"""
    try:
        results_dir = '../scanner_results'
        csv_files = [f for f in os.listdir(results_dir) 
                    if f.startswith('results_') and f.endswith('.csv')]
        
        if not csv_files:
            logger.warning("No scanner results found")
            return None
        
        csv_files.sort()
        latest_file = os.path.join(results_dir, csv_files[-1])
        
        df = pd.read_csv(latest_file)
        
        # Filter: only signals that passed filter
        df = df[df['passes_filter'] == True].copy()
        
        # Filter: price range 50-2000
        df_filtered = df[(df['price'] >= min_price) & (df['price'] <= max_price)].copy()
        df_filtered = df_filtered.sort_values('price', ascending=False)
        
        logger.info(f"Total signals found: {len(df)}")
        logger.info(f"After price filter (50-2000): {len(df_filtered)}")
        logger.info(f"Removed (high price >2000): {len(df[df['price'] > max_price])}")
        logger.info(f"Removed (low price <50): {len(df[df['price'] < min_price])}")
        
        return df_filtered
        
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return None


def display_filtered_results(df):
    """Display filtered results"""
    if df is None or len(df) == 0:
        logger.warning("No results to display")
        return
    
    print('\n' + '='*100)
    print('NILAYCHOPDASCANNER - FILTERED RESULTS (Price Range: 50-2000)')
    print('='*100)
    print(f'\nTotal Filtered Signals: {len(df)}')
    print('\n' + '-'*100)
    print(f'{"Rank":<6} {"Symbol":<15} {"Price":<15} {"Change":<12} {"Volume":<15}')
    print('-'*100)
    
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        print(
            f"{idx:<6} {row['symbol']:<15} "
            f"₹{row['price']:<14.2f} {row['change']:>6.2f}% {'':<4} {int(row['volume']):>12,}"
        )
    
    print('-'*100)
    
    # Statistics
    print('\nPrice Range Analysis:')
    print(f"  Highest Price: ₹{df['price'].max():.2f}")
    print(f"  Lowest Price: ₹{df['price'].min():.2f}")
    print(f"  Average Price: ₹{df['price'].mean():.2f}")
    print(f"  Average Change: {df['change'].mean():.2f}%")
    print(f"  Total Volume: {int(df['volume'].sum()):,} shares")
    
    print('\n' + '='*100)


def save_filtered_results(df):
    """Save filtered results"""
    if df is None:
        return
    
    filename = 'nilaychopda_filtered_50_2000.csv'
    df.to_csv(filename, index=False)
    logger.info(f"Filtered results saved: {filename}")
    
    # Also save as JSON
    json_filename = 'nilaychopda_filtered_50_2000.json'
    df.to_json(json_filename, orient='records', indent=2)
    logger.info(f"JSON saved: {json_filename}")


def main():
    logger.info("\n" + "="*100)
    logger.info("NILAYCHOPDASCANNER - PRICE FILTER (50-2000)")
    logger.info("="*100)
    
    # Load and filter
    df = load_and_filter_results(min_price=50, max_price=2000)
    
    if df is not None and len(df) > 0:
        display_filtered_results(df)
        save_filtered_results(df)
    else:
        logger.warning("No signals found in price range 50-2000")


if __name__ == '__main__':
    main()
