
import os
import requests
import pandas as pd
import yfinance as yf
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("twn.market_data")

class MarketData:
    """
    Unified Data Provider with fallbacks.
    Prioritizes free/scrapable sources for Indian Market.
    """
    
    @staticmethod
    def get_live_price(symbol: str) -> Optional[float]:
        """
        Get real-time price for a single symbol with multiple fallbacks.
        """
        # Clean symbol
        clean_sym = symbol.split('.')[0].split('(')[0].strip().upper()
        
        # 1. Google Finance Scraper (Fast & Reliable for basic price)
        price = MarketData._fetch_google_finance(clean_sym)
        if price: return price
        
        # 2. Yahoo Finance (Standard Fallback)
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            price = ticker.fast_info.get('last_price')
            if price: return price
        except:
            pass
            
        return None

    @staticmethod
    def get_batch_prices(symbols: List[str]) -> Dict[str, float]:
        """
        Efficiently fetch multiple prices.
        """
        results = {}
        # Try YFinance batch first as it's efficient for 50+ stocks
        try:
            yf_syms = [f"{s.split('.')[0]}.NS" for s in symbols]
            data = yf.download(yf_syms, period="1d", interval="1m", progress=False, group_by='ticker')
            
            for s in symbols:
                clean_s = s.split('.')[0]
                yf_s = f"{clean_s}.NS"
                try:
                    if len(symbols) > 1:
                        results[s] = data[yf_s]['Close'].iloc[-1]
                    else:
                        results[s] = data['Close'].iloc[-1]
                except:
                    # Individual fallback
                    p = MarketData.get_live_price(s)
                    if p: results[s] = p
        except:
            for s in symbols:
                p = MarketData.get_live_price(s)
                if p: results[s] = p
                
        return results

    @staticmethod
    def _fetch_google_finance(symbol: str) -> Optional[float]:
        """Scrape price from Google Finance"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = f"https://www.google.com/finance/quote/{symbol}:NSE"
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Google changes classes often, try a few common ones
                price_div = soup.find('div', {'class': 'YMlS7e'}) # Current class as of Feb 2024
                if not price_div:
                    price_div = soup.find('div', {'data-last-price': True})
                
                if price_div:
                    p_text = price_div.text.replace('₹', '').replace(',', '').strip()
                    return float(p_text)
        except Exception as e:
            logger.debug(f"Google Finance failed for {symbol}: {e}")
        return None

    @staticmethod
    def get_historical_data(symbol: str, days: int = 60) -> pd.DataFrame:
        """Fetch historical candles"""
        clean_sym = symbol.split('.')[0].upper()
        try:
            ticker = yf.Ticker(f"{clean_sym}.NS")
            df = ticker.history(period=f"{days}d", interval="1d")
            return df
        except:
            return pd.DataFrame()
