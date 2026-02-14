import requests
from bs4 import BeautifulSoup
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_chartink")

def test_fetch_via_clause():
    scan_clause = "( {33489} ( daily avg true range( 14 ) < 10 days ago avg true range( 14 ) and daily avg true range( 14 ) / daily close < 0.08 and daily close > ( weekly max( 52 , weekly close ) * 0.75 ) and daily ema( daily close , 50 ) > daily ema( daily close , 150 ) and daily ema( daily close , 150 ) > daily ema( daily close , 200 ) and daily close > daily ema( daily close , 50 ) and daily close > 10 and daily close * daily volume > 1000000 ) )"
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info("Fetching CSRF token...")
        response = session.get("https://chartink.com/screener/nilay-swing-pick-algo")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
        logger.info(f"CSRF Token: {csrf_token}")

        process_url = "https://chartink.com/screener/process"
        data = {
            'scan_clause': scan_clause,
            '_token': csrf_token
        }
        
        logger.info("Sending POST request...")
        resp = session.post(process_url, data=data)
        logger.info(f"Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            json_data = resp.json()
            if 'data' in json_data:
                logger.info(f"Success! Found {len(json_data['data'])} records.")
                # print(json.dumps(json_data['data'][:2], indent=2))
            else:
                logger.error(f"No 'data' in response: {json_data}")
        else:
            logger.error(f"Request failed with status {resp.status_code}")
            # logger.error(resp.text)

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    test_fetch_via_clause()
