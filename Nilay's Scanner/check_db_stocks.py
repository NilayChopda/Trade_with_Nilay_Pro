import sqlite3
import os

db_path = r"g:\My Drive\Trade_with_Nilay\backend\database\trade_with_nilay.db"

def check_stocks():
    if not os.path.exists(db_path):
        print(f"Error: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for specific stocks mentioned by user
    search_terms = ['SHRIRAM', 'BMW', 'LENSKART']
    
    print("--- Searching for symbols ---")
    for term in search_terms:
        cursor.execute("SELECT DISTINCT symbol, price, change_pct, timestamp FROM scanner_results WHERE symbol LIKE ?", (f'%{term}%',))
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} results for {term}:")
            for r in results:
                print(f"  {r}")
        else:
            print(f"No results found for {term}")
    
    # Check latest 10 entries
    print("\n--- Latest 10 entries (any date) ---")
    cursor.execute("SELECT symbol, price, change_pct, volume, timestamp FROM scanner_results ORDER BY timestamp DESC LIMIT 10")
    for r in cursor.fetchall():
        print(f"  {r}")
    
    # Check today's count without date() function for debugging
    cursor.execute("SELECT COUNT(*) FROM scanner_results")
    total_count = cursor.fetchone()[0]
    print(f"\nTotal stocks in DB: {total_count}")
    
    conn.close()

if __name__ == "__main__":
    check_stocks()
