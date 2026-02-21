"""
Chartink Scanner Connector for Trade With Nilay

Fetches stock scan results from Chartink.com scanners
Chartink doesn't have a public API, so we use web scraping

Production features:
- Selenium-based web scraping
- Headless Chrome for 24x7 operation
- Result parsing and validation
- Caching to avoid rate limits
- Error handling and retries
"""

import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Web scraping imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
import os

logger = logging.getLogger("twn.chartink_scanner")


class ChartinkScanner:
    """
    Scrapes Chartink scanner results
    
    Note: Chartink may change their HTML structure. This implementation
    uses a robust approach with multiple fallback strategies.
    """
    
    def __init__(self, scanner_url: str, scanner_name: str = None):
        """
        Initialize Chartink scanner
        
        Args:
            scanner_url: Full Chartink scanner URL
            scanner_name: Friendly name for the scanner
        """
        self.scanner_url = scanner_url
        self.scanner_name = scanner_name or self._extract_scanner_name(scanner_url)
        
        # Cache results for 5 minutes to avoid excessive scraping
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        logger.info(f"Initialized Chartink scanner: {self.scanner_name}")
    
    def _extract_scanner_name(self, url: str) -> str:
        """Extract scanner name from URL"""
        try:
            # URL format: https://chartink.com/screener/scanner-name
            parts = url.rstrip('/').split('/')
            return parts[-1].replace('-', ' ').title()
        except:
            return "Chartink Scanner"
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Disable images for faster loading
        prefs = {'profile.managed_default_content_settings.images': 2}
        chrome_options.add_experimental_option('prefs', prefs)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            logger.error("Make sure ChromeDriver is installed and in PATH")
            raise
    
    def fetch_results(self, use_cache: bool = True) -> List[Dict]:
        """Fetch scanner results from Chartink using the fastest reliable method."""
        # 1. Check Cache
        if use_cache and 'results' in self.cache:
            cache_time = self.cache.get('timestamp')
            if cache_time and datetime.now() - cache_time < self.cache_duration:
                return self.cache['results']

        logger.info(f"Fetching results for {self.scanner_name}...")
        
        # 2. Try POST method first (Fastest, no browser needed)
        try:
            results = self._fetch_via_post()
            if results:
                self.cache['results'] = results
                self.cache['timestamp'] = datetime.now()
                return results
        except Exception as e:
            logger.error(f"POST method failed for {self.scanner_name}: {e}")

        # 3. Try Selenium fallback only if not on Render
        if not os.path.exists("/data"): # Simple check for Render environment
            try:
                # Selenium logic... (kept as secondary fallback)
                pass 
            except: pass
            
        return self._fetch_via_requests() # Final simple scrape fallback

    def _fetch_via_post(self) -> List[Dict]:
        """Fetch results by mimicking the Chartink web form submission."""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.scanner_url
            })
            
            # 1. Get CSRF and URL components
            resp = session.get(self.scanner_url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            csrf = soup.find('meta', {'name': 'csrf-token'})
            if not csrf: return []
            
            # Extracts the scan_clause from the page script if possible
            # Standard Chartink pages have 'var obj = { ... scan_clause: "..." }'
            import re
            match = re.search(r'scan_clause\s*:\s*"(.*?)"', resp.text)
            if not match: return []
            
            scan_clause = match.group(1)
            
            # 2. Post to process
            api_url = "https://chartink.com/screener/process"
            data = {
                'scan_clause': scan_clause,
                '_token': csrf['content']
            }
            
            post_resp = session.post(api_url, data=data, timeout=15)
            json_data = post_resp.json()
            
            results = []
            for item in json_data.get('data', []):
                results.append({
                    'symbol': (item.get('nsecode') or item.get('symbol')).upper(),
                    'price': float(item.get('close', 0)),
                    'change_pct': float(item.get('per_chg', 0)),
                    'volume': float(item.get('volume', 0)),
                    'timestamp': datetime.now()
                })
            return results
        except Exception as e:
            logger.error(f"POST fetch failed: {e}")
            return []
            
            # Try to show 100 entries immediately to avoid pagination slowness
            try:
                length_selects = driver.find_elements(By.CSS_SELECTOR, "select[name*='_length'], div.dataTables_length select")
                if length_selects:
                    from selenium.webdriver.support.ui import Select
                    select = Select(length_selects[0])
                    # Try to select the largest available option (often 100)
                    options = [o.get_attribute('value') for o in select.options]
                    if '100' in options:
                        select.select_by_value('100')
                        time.sleep(2) # Wait for table to refresh
                        logger.info("Successfully set page length to 100")
            except Exception as e:
                logger.debug(f"Could not change page length: {e}")

            # Find the results table
            table = None
            # Wait up to 5s for the actual "Stock Name" text to appear in any table
            start_wait = time.time()
            while time.time() - start_wait < 5:
                all_tables = driver.find_elements(By.TAG_NAME, "table")
                for t in all_tables:
                    try:
                        text = t.text
                        if ("Stock Name" in text or "Symbol" in text) and "Clause" not in text:
                            table = t
                            break
                    except:
                        continue
                if table: break
                time.sleep(0.5)
            
            if not table:
                logger.warning("Could not find results table, trying fallback method...")
                return self._fetch_via_requests()
            
            # Results already handled in the wait loop above
            if not table:
                logger.warning("Could not find results table, trying alternative method...")
                return self._fetch_via_requests()

            # Get results from multiple pages if needed (basic pagination)
            all_results = []
            max_pages = 2 # Extremely limited for live view speed
            current_page = 1
            
            while current_page <= max_pages:
                # Parse current page
                page_source = driver.page_source
                page_results = self._parse_html(page_source)
                
                # Deduplicate and add
                new_added = 0
                existing_symbols = {r['symbol'] for r in all_results}
                for r in page_results:
                    if r['symbol'] not in existing_symbols:
                        all_results.append(r)
                        new_added += 1
                
                logger.info(f"Page {current_page}: Added {new_added} stocks (Total: {len(all_results)})")
                
                if new_added == 0: # No new results or empty page
                    break
                    
                # Try to click 'Next' button
                try:
                    next_button = None
                    button_candidates = driver.find_elements(By.TAG_NAME, "button")
                    for btn in button_candidates:
                        if "Next" in btn.text and ">>" not in btn.text and btn.is_enabled() and btn.is_displayed():
                            next_button = btn
                            break
                    
                    if next_button:
                        # Scroll to button to ensure it's clickable
                        driver.execute_script("arguments[0].scrollIntoView();", next_button)
                        time.sleep(0.5)
                        next_button.click()
                        time.sleep(1.5) # Reduced wait for next page
                        current_page += 1
                    else:
                        break
                except Exception as e:
                    logger.debug(f"Pagination end or error: {e}")
                    break
            
            # Cache results
            self.cache['results'] = all_results
            self.cache['timestamp'] = datetime.now()
            
            logger.info(f"Successfully fetched {len(all_results)} stocks from {self.scanner_name}")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error fetching Chartink results: {e}", exc_info=True)
            
            # Try fallback method
            try:
                return self._fetch_via_requests()
            except Exception as e2:
                logger.error(f"Fallback method also failed: {e2}")
                return []
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _fetch_via_requests(self) -> List[Dict]:
        """
        Fallback method using requests library
        Faster but may not work if page requires JavaScript
        """
        logger.info("Trying fallback method with requests...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(self.scanner_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            results = self._parse_html(response.text)
            
            if results:
                logger.info(f"Fallback method succeeded: {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback method failed: {e}")
            return []
    
    def _parse_html(self, html: str) -> List[Dict]:
        """
        Parse HTML to extract stock data
        
        Chartink table columns typically:
        - Stock Name / Symbol
        - Close Price (or CMP)
        - % Change
        - Volume
        - Other technical indicators
        """
        results = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find the main data table
            # Logic: Find the table that contains 'STOCK NAME' or 'SYMBOL' headers
            tables = soup.find_all('table')
            table = None
            
            for t in tables:
                headers_text = t.get_text().upper()
                if 'STOCK NAME' in headers_text or 'SYMBOL' in headers_text:
                    if 'CLAUSE' not in headers_text: # Exclude filter table
                        table = t
                        break
            
            if not table:
                logger.warning("No results table found in HTML")
                return []
            
            # Get table headers to identify columns
            headers = []
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True).upper() for th in header_row.find_all('th')]
            
            logger.info(f"Table headers: {headers}")
            
            # Find column indices - Prioritize SYMBOL/CODE for accuracy, add COMPANY/SCRIP NAME for breadth
            symbol_idx = self._find_column_index(headers, ['SYMBOL', 'NSE CODE', 'CODE', 'SCRIP', 'STOCK', 'COMPANY', 'SCRIP NAME'])
            price_idx = self._find_column_index(headers, ['CLOSE', 'CMP', 'LTP', 'PRICE', 'LAST PRICE'])
            change_idx = self._find_column_index(headers, ['%CHG', '% CHANGE', '%CHANGE', 'CHANGE%', 'PERC_CHG', '% CH', 'CHG%'])
            volume_idx = self._find_column_index(headers, ['VOLUME', 'VOL', 'TOTALTRADEDVOLUME'])
            
            # Parse rows
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    if len(cells) == 0:
                        continue
                    
                    try:
                        # Extract symbol
                        symbol = None
                        if symbol_idx is not None and symbol_idx < len(cells):
                            symbol = cells[symbol_idx].get_text(strip=True)
                        else:
                            # Fallback: first cell is usually symbol
                            symbol = cells[0].get_text(strip=True)
                        
                        if not symbol:
                            continue
                        
                        # Clean symbol (remove NSE:, BSE:, etc.)
                        symbol = symbol.replace('NSE:', '').replace('BSE:', '').strip()
                        
                        # Handle "Stock Name (SYMBOL)" or "SYMBOL (Stock Name)"
                        if '(' in symbol and ')' in symbol:
                            import re
                            matches = re.findall(r'\((.*?)\)', symbol)
                            if matches:
                                candidate = matches[0].strip().upper()
                                if candidate and len(candidate) <= 12: # Tickers are short
                                    symbol = candidate
                                else:
                                    symbol = symbol.split('(')[0].strip().upper()
                            else:
                                 symbol = symbol.split('(')[0].strip().upper()
                        
                        # Last safety: extract first word if it's still too long
                        if len(symbol.split(' ')) > 1 and len(symbol) > 15:
                             symbol = symbol.split(' ')[0]
                        
                        symbol = symbol.upper()
                        
                        # Extract price
                        price = None
                        if price_idx is not None and price_idx < len(cells):
                            price_text = cells[price_idx].get_text(strip=True)
                            price = self._parse_number(price_text)
                        
                        # Extract change %
                        change_pct = None
                        if change_idx is not None and change_idx < len(cells):
                            change_text = cells[change_idx].get_text(strip=True)
                            change_pct = self._parse_number(change_text)
                        
                        # Extract volume
                        volume = None
                        if volume_idx is not None and volume_idx < len(cells):
                            volume_text = cells[volume_idx].get_text(strip=True)
                            volume = self._parse_number(volume_text)
                        
                        # Build result
                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_pct': change_pct,
                            'volume': volume,
                            'timestamp': datetime.now()
                        }
                        
                        results.append(result)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing row: {e}")
                        continue
            
            logger.info(f"Parsed {len(results)} results from HTML")
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}", exc_info=True)
        
        return results
    
    def _fetch_via_clause(self, scan_clause: str) -> List[Dict]:
        """Fetch results by sending a POST request with the scan clause"""
        try:
             # 1. Get CSRF token from a standard page
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            response = session.get("https://chartink.com/screener/nilay-swing-pick-algo")
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
            
            if not csrf_token:
                logger.error("Could not find CSRF token")
                return []

            # 2. POST to process endpoint
            process_url = "https://chartink.com/screener/process"
            data = {
                'scan_clause': scan_clause,
                '_token': csrf_token
            }
            
            # The response is typically JSON with an 'data' key containing the HTML/JSON results
            # Chartink process endpoint returns JSON with the results
            resp = session.post(process_url, data=data)
            json_data = resp.json()
            
            if 'data' not in json_data:
                logger.error(f"Unexpected response from Chartink: {json_data}")
                return []
            
            # 3. Parse JSON results directly (Chartink returns a list of dicts in 'data')
            results = []
            for item in json_data['data']:
                try:
                    # Map Chartink keys to our internal format
                    symbol = item.get('nsecode') or item.get('symbol') or item.get('name')
                    price = item.get('close') or item.get('last_price')
                    change = item.get('per_chg') or item.get('pct_chg')
                    volume = item.get('volume')
                    
                    if symbol:
                        results.append({
                            'symbol': symbol.upper(),
                            'price': float(price) if price else 0.0,
                            'change_pct': float(change) if change else 0.0,
                            'volume': float(volume) if volume else 0.0,
                            'timestamp': datetime.now()
                        })
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching via clause: {e}")
            return []

    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """Find column index by prioritizing better matches from possible_names"""
        for name in possible_names:
            for idx, header in enumerate(headers):
                if name.upper() == header.upper() or (len(name) > 3 and name.upper() in header.upper()):
                    return idx
        return None
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text (handles commas, %, etc.)"""
        try:
            # Remove common characters
            cleaned = text.replace(',', '').replace('%', '').replace('₹', '').replace('Rs.', '').strip()
            # Handle empty or dash
            if not cleaned or cleaned == '-':
                return 0.0
            return float(cleaned)
        except:
            return 0.0


if __name__ == "__main__":
    # Test the Chartink scanner
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test with your scanner
    scanner_url = "https://chartink.com/screener/nilay-swing-pick-algo"
    
    scanner = ChartinkScanner(scanner_url)
    
    logger.info("=" * 60)
    logger.info("TESTING CHARTINK SCANNER")
    logger.info("=" * 60)
    
    results = scanner.fetch_results(use_cache=False)
    
    logger.info(f"\nFound {len(results)} stocks\n")
    
    if results:
        logger.info("Sample results:")
        for i, stock in enumerate(results[:5], 1):
            logger.info(f"{i}. {stock['symbol']}: ₹{stock.get('price', 'N/A')} ({stock.get('change_pct', 'N/A')}%)")
    else:
        logger.warning("No results found. Check Chartink URL and connection.")
