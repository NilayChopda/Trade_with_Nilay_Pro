"""
Trade With Nilay - Backend API Server
Serves market data, scanner results, and manages background tasks using FastAPI

Endpoints:
- GET /api/health
- GET /api/stocks (List all tradable stocks)
- GET /api/stocks/{symbol} (Detailed stock info with OHLC)
- GET /api/scanners (List active scanners)
- GET /api/scanner-results (Latest results from all scanners)
- GET /api/fno/chain (Get option chain for a symbol)
- GET /api/indices (Get major indices status)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_conn, get_latest_price, get_historical_data, get_scanner_results
from services.symbol_manager import get_equity_symbols, get_fno_symbols, get_indices

# Initialize App
app = FastAPI(
    title="Trade With Nilay API",
    description="Backend API for Trade With Nilay Trading Platform",
    version="1.0.0"
)

# CORS Configuration (Allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twn.api")


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Trade With Nilay API"}


@app.get("/api/stocks")
def list_stocks(limit: int = 100, page: int = 1, search: Optional[str] = None):
    """List all available stocks with pagination"""
    all_symbols = get_equity_symbols()
    
    if search:
        search = search.upper()
        all_symbols = [s for s in all_symbols if search in s]
    
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "total": len(all_symbols),
        "page": page,
        "limit": limit,
        "data": all_symbols[start:end]
    }


@app.get("/api/stocks/{symbol}")
def get_stock_detail(symbol: str):
    """Get detailed stock information including latest price"""
    symbol = symbol.upper()
    latest = get_latest_price(symbol)
    
    if not latest:
        # Check if valid symbol
        all_symbols = get_equity_symbols()
        if symbol not in all_symbols:
            raise HTTPException(status_code=404, detail="Stock not found")
        return {"symbol": symbol, "status": "No data available"}
    
    return {
        "symbol": symbol,
        "latest_price": latest[0],
        "last_updated": latest[1]
    }


@app.get("/api/stocks/{symbol}/history")
def get_stock_history(symbol: str, days: int = 1):
    """Get historical OHLCV data"""
    import time
    end_ts = int(time.time())
    start_ts = end_ts - (days * 24 * 60 * 60)
    
    df = get_historical_data(symbol, start_ts, end_ts)
    
    if df.empty:
        return {"symbol": symbol, "data": []}
    
    return {
        "symbol": symbol,
        "count": len(df),
        "data": df.to_dict(orient="records")
    }


@app.get("/api/scanners")
def list_scanners():
    """List all configured scanners"""
    conn = get_conn()
    try:
        scanners = conn.execute("SELECT id, name, url, scanner_type, description FROM scanners").fetchall()
        return [
            {
                "id": s[0],
                "name": s[1],
                "url": s[2],
                "type": s[3],
                "description": s[4]
            }
            for s in scanners
        ]
    finally:
        conn.close()


@app.get("/api/scanner-results")
def get_latest_scanner_results(limit: int = 50):
    """Get latest results from all scanners"""
    df = get_scanner_results(limit=limit)
    
    if df.empty:
        return []
    
    # Convert to list of dicts
    results = df.to_dict(orient="records")
    return results


@app.get("/api/indices")
def get_market_indices():
    """Get major market indices status"""
    indices = get_indices()
    # TODO: Fetch live values for indices (currently static list)
    return indices

# FnO Endpoints
from services.fno_fetcher import FnoFetcher
fno_fetcher = FnoFetcher()
# Simple in-memory cache
fno_cache = {}
last_fno_fetch = {}

@app.get("/api/fno/overview/{symbol}")
def get_fno_overview(symbol: str):
    """Get FnO Overview (PCR, Max Pain) for an index"""
    symbol = symbol.upper()
    if symbol not in ['NIFTY', 'BANKNIFTY']:
        raise HTTPException(status_code=400, detail="Only NIFTY and BANKNIFTY supported")
        
    # Check cache (1 minute)
    import time
    now = time.time()
    if symbol in fno_cache and now - last_fno_fetch.get(symbol, 0) < 60:
        return fno_cache[symbol]
        
    try:
        data = fno_fetcher.get_analysis(symbol)
        if "error" in data:
             raise HTTPException(status_code=500, detail=data["error"])
             
        fno_cache[symbol] = data
        last_fno_fetch[symbol] = now
        return data
    except Exception as e:
        logger.error(f"Error fetching FnO data: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run("backend.api.server:app", host="0.0.0.0", port=8000, reload=True)
