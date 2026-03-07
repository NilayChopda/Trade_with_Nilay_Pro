import requests
import io
import pandas as pd
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_bhavcopy(date):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/all-reports",
        "Origin": "https://www.nseindia.com"
    })

    date_str = date.strftime("%d-%m-%Y")
    url = f"https://www.nseindia.com/api/reports?archives=cm&date={date_str}&type=equities"

    try:
        print(f"Downloading for {date_str}...")

        session.get("https://www.nseindia.com", timeout=10)
        r = session.get(url, timeout=15)

        if r.status_code != 200:
            print("Not available")
            return None

        df = pd.read_csv(io.BytesIO(r.content))

        print("Columns:", df.columns.tolist())
        print(df.head())

        return df

    except Exception as e:
        print("Error:", e)
        return None


if __name__ == "__main__":
    today = datetime.today()
    download_bhavcopy(today)