
import sys
import logging
from nsepython import nse_optionchain_scrapper

logging.basicConfig(level=logging.DEBUG)

print("Testing nsepython direct fetch...")
try:
    data = nse_optionchain_scrapper("NIFTY")
    if not data:
        print("Data is empty/None")
    elif 'records' not in data:
        print(f"Data has no 'records' key. Keys found: {list(data.keys())}")
        print(f"Raw data excerpt: {str(data)[:200]}")
    else:
        print("Success! Data fetched.")
        print(f"Expiry dates: {data['records']['expiryDates']}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
