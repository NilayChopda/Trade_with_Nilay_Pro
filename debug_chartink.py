import logging
import time
from pathlib import Path
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.scanner.chartink_scanner import ChartinkScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_scanner")

def debug_fetch():
    url = "https://chartink.com/screener/nilay-swing-pick-algo"
    scanner = ChartinkScanner(url)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        logger.info(f"Loading {url}...")
        driver.get(url)
        time.sleep(10) # Wait for potential redirects/loads
        
        page_source = driver.page_source
        with open("chartink_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        logger.info(f"Page source saved to chartink_debug.html (Length: {len(page_source)})")
        
        # Take a screenshot to see if Cloudflare is there
        driver.save_screenshot("chartink_screenshot.png")
        logger.info("Screenshot saved to chartink_screenshot.png")
        
        if "Cloudflare" in page_source or "Just a moment" in page_source:
            logger.error("Deteched by Cloudflare!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_fetch()
