import requests
import re
from bs4 import BeautifulSoup
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chartink_api")

def fetch_chartink_api(url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    logger.info(f"Step 1: Getting CSRF token and cookies from {url}...")
    r = session.get(url)
    r.raise_for_status()
    
    # Extract CSRF token
    soup = BeautifulSoup(r.text, 'lxml')
    csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
    logger.info(f"Found CSRF Token: {csrf_token}")
    
    # The scan_clause is usually in the URL for saved screeners, 
    # but the process endpoint needs the actual logic.
    # For saved screeners, Chartink handles it if we send the right headers.
    
    # The process endpoint is /screener/process
    process_url = "https://chartink.com/screener/process"
    
    # For a saved screener, we need to find the scan_clause in the page.
    # It's usually in a script tag.
    # Let's try to find 'var scan_clause = ...'
    match = re.search(r'var scan_clause = ["\']([^"\']+)["\']', r.text)
    if not match:
        logger.error("Could not find scan_clause in page!")
        return []
    
    scan_clause = match.group(1)
    logger.info(f"Found scan_clause: {scan_clause[:50]}...")
    
    payload = {
        'scan_clause': scan_clause
    }
    
    headers = {
        'x-csrf-token': csrf_token,
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    
    logger.info("Step 2: POSTing to /screener/process...")
    r = session.post(process_url, data=payload, headers=headers)
    r.raise_for_status()
    
    data = r.json()
    stocks = data.get('data', [])
    
    logger.info(f"Successfully fetched {len(stocks)} stocks via API")
    return stocks

if __name__ == "__main__":
    url = "https://chartink.com/screener/nilay-swing-pick-algo"
    stocks = fetch_chartink_api(url)
    if stocks:
        print(f"Sample: {stocks[0]}")
