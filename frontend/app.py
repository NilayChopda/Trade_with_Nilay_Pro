"""
Trade With Nilay - Dashboard
A professional trading dashboard built with Streamlit

Features:
- Live Market Overview
- Scanner Results (Real-time)
- AI Stock Analysis (Fundamental + Technical)
- Chartink Live Replica
- FnO Dashboard (Index OI Analytics)
- System Health Monitoring
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import get_conn, get_scanner_results, get_historical_data
from backend.services.symbol_manager import get_equity_symbols

# Page Config
st.set_page_config(
    page_title="Trade With Nilay - Pro Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://t.me/your_channel',
        'About': """
        # Trade With Nilay v2.0
        Professional Indian Stock Market Analysis Platform
        
        Features: Real-time scanning • AI patterns • Telegram alerts • FnO analysis
        """
    }
)

# PWA Manifest for mobile app experience
st.markdown("""
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#F59E0B">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Trade With Nilay">
""", unsafe_allow_html=True)

# Mobile-Optimized CSS
st.markdown("""
    <style>
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Mobile Padding Optimization */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 5rem;
        }
        
        /* Better Table Scrolling on Mobile */
        .stDataFrame {
            overflow-x: auto;
        }
    </style>
""", unsafe_allow_html=True)

# Auto-refresh every 5 minutes with countdown
refresh_interval = 5 * 60  # 300 seconds
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Calculate time until next refresh
time_since_refresh = time.time() - st.session_state.last_refresh
time_until_refresh = refresh_interval - time_since_refresh

# Auto-rerun when time is up
if time_until_refresh <= 0:
    st.session_state.last_refresh = time.time()
    st.rerun()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🎯 Nilay's Scanner")
    st.caption("Advanced Analytics Pro")
    
    page = st.radio("Navigation", ["Dashboard", "Scanner Results", "Stock Analysis", "Chartink Live", "FnO Dashboard", "System Health"])
    
    st.markdown("---")
    st.info("Mobile access: Use the Localtunnel URL provided by share_dashboard.bat")

def show_chartink_live_scanner():
    """Replica of Chartink Scanner with Live Prices"""
    st.title("🎯 Chartink Live Scanner")
    st.caption("Exact replica of Chartink scanner with 1-minute live price updates")
    
    # Scanner Selection
    scanners = {
        "NILAY SWING PICK - ALGO": {"url": "https://chartink.com/screener/nilay-swing-pick-algo"},
        "NILAY SWING PICK 2.0": {"url": "https://chartink.com/screener/nilay-swing-pick-2-0"},
        "NILAY FNO VOLATILITY SCAN": {
            "url": "https://chartink.com/screener/process",
            "clause": "( {33489} ( daily avg true range( 14 ) < 10 days ago avg true range( 14 ) and daily avg true range( 14 ) / daily close < 0.08 and daily close > ( weekly max( 52 , weekly close ) * 0.75 ) and daily ema( daily close , 50 ) > daily ema( daily close , 150 ) and daily ema( daily close , 150 ) > daily ema( daily close , 200 ) and daily close > daily ema( daily close , 50 ) and daily close > 10 and daily close * daily volume > 1000000 ) )"
        },
        "NILAY FNO AUTOPICK": {"url": "https://chartink.com/screener/nilay-fno-autopick-scanner"}
    }
    
    col1, col2 = st.columns([2, 1])
    with col1:
        scanner_name = st.selectbox("Select Scanner", list(scanners.keys()))
    with col2:
        refresh_rate = st.selectbox("Auto Refresh", ["1 Minute", "5 Minutes", "Manual"], index=0)

    # Trigger Refresh
    if refresh_rate != "Manual":
        st.info(f"Auto-refreshing every {refresh_rate}")

    from backend.scanner.chartink_scanner import ChartinkScanner
    import yfinance as yf
    
    # Cache data to avoid constant scraping
    @st.cache_data(ttl=60)
    def fetch_chartink_data(url, name, scan_clause=None):
        scanner = ChartinkScanner(url, name)
        return scanner.fetch_results(use_cache=False, scan_clause=scan_clause)

    with st.spinner(f"Scraping {scanner_name}..."):
        config = scanners[scanner_name]
        results = fetch_chartink_data(config['url'], scanner_name, scan_clause=config.get('clause'))
        
    if not results:
        st.error("No results found or Chartink blocked the request. Please try again.")
        if st.button("Retry Scan"):
            st.rerun()
        return

    # Add Live Prices
    st.markdown(f"### Results ({len(results)} stocks)")
    
    show_all = st.checkbox("Show All Results (Live prices for 200+ stocks can be slow)", value=False)
    results_to_process = results if show_all else results[:50]
    
    # Process for display
    display_data = []
    
    with st.spinner(f"Fetching Live Prices for {len(results_to_process)} stocks..."):
        # Batch fetch symbols
        symbols = [f"{r['symbol']}.NS" for r in results_to_process]
        try:
            # Batch download is MUCH faster than individual ticker queries
            data = yf.download(symbols, period="1d", interval="1m", progress=False, group_by='ticker')
            
            for r in results_to_process:
                sym = r['symbol']
                yf_sym = f"{sym}.NS"
                live_price = r['price'] # Fallback
                
                try:
                    if len(symbols) > 1:
                        live_price = data[yf_sym]['Close'].iloc[-1]
                    else:
                        live_price = data['Close'].iloc[-1]
                except:
                    pass
                
                display_data.append({
                    "Symbol": sym,
                    "Scanner Price": r['price'],
                    "Live Price": live_price,
                    "Change %": r['change_pct'],
                    "Volume": r['volume'],
                    "Last Seen": r['timestamp'].strftime("%H:%M:%S")
                })
        except Exception as e:
            st.warning(f"Live Price fetch error: {e}. Showing scanner prices.")
            for r in results_to_process:
                 display_data.append({
                    "Symbol": r['symbol'],
                    "Scanner Price": r['price'],
                    "Live Price": r['price'],
                    "Change %": r['change_pct'],
                    "Volume": r['volume'],
                    "Last Seen": r['timestamp'].strftime("%H:%M:%S")
                })

    df = pd.DataFrame(display_data)
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Symbol": st.column_config.TextColumn("Symbol", help="NSE Stock Symbol"),
            "Scanner Price": st.column_config.NumberColumn("Scanner Price", format="₹%.2f"),
            "Live Price": st.column_config.NumberColumn("Live Price (YF)", format="₹%.2f"),
            "Change %": st.column_config.NumberColumn("Change %", format="%.2f%%"),
            "Volume": st.column_config.NumberColumn("Volume", format="%d"),
        },
        hide_index=True
    )
    
    if st.button("Manual Refresh"):
        st.rerun()

def show_fno_dashboard():
    """FnO Dashboard View - Stocks Focus"""
    st.title("📊 FnO Analysis (Stocks)")
    st.caption("Deep insights into F&O segment stocks with live price action")
    
    # Scanner Selection for FnO
    scanners = {
        "NILAY FNO VOLATILITY SCAN": {
            "url": "https://chartink.com/screener/process",
            "clause": "( {33489} ( daily avg true range( 14 ) < 10 days ago avg true range( 14 ) and daily avg true range( 14 ) / daily close < 0.08 and daily close > ( weekly max( 52 , weekly close ) * 0.75 ) and daily ema( daily close , 50 ) > daily ema( daily close , 150 ) and daily ema( daily close , 150 ) > daily ema( daily close , 200 ) and daily close > daily ema( daily close , 50 ) and daily close > 10 and daily close * daily volume > 1000000 ) )"
        },
        "NILAY FNO AUTOPICK": {"url": "https://chartink.com/screener/nilay-fno-autopick-scanner"}
    }
    
    col1, col2 = st.columns([2, 1])
    with col1:
        scanner_name = st.selectbox("Select F&O Scanner", list(scanners.keys()))
    with col2:
        if st.button("Refresh Results"):
            st.cache_data.clear()
            st.rerun()

    from backend.scanner.chartink_scanner import ChartinkScanner
    import yfinance as yf
    
    @st.cache_data(ttl=60)
    def fetch_fno_data(url, name):
        scanner = ChartinkScanner(url, name)
        return scanner.fetch_results(use_cache=False)

    with st.spinner(f"Scraping F&O results for {scanner_name}..."):
        config = scanners[scanner_name]
        results = fetch_fno_data(config['url'], scanner_name)
        
    if not results:
        st.info("No candidates found in this F&O scan currently.")
        return

    # Add Live Prices
    st.markdown(f"### F&O Candidates ({len(results)} stocks)")
    
    # Chartink-Style Display
    if config.get('clause'):
        with st.expander("📝 View Scan Clause", expanded=False):
            st.code(config['clause'], language="sql")
    
    # Process for display
    display_data = []
    
    with st.spinner(f"Fetching Live Prices..."):
        # Batch fetch symbols
        symbols = [f"{r['symbol']}.NS" for r in results[:50]] # Limit to 50 for speed
        try:
            data = yf.download(symbols, period="1d", interval="1m", progress=False, group_by='ticker')
            
            for r in results[:50]:
                sym = r['symbol']
                yf_sym = f"{sym}.NS"
                price = r['price']
                
                try:
                    if len(symbols) > 1:
                        price = data[yf_sym]['Close'].iloc[-1]
                    else:
                        price = data['Close'].iloc[-1]
                except:
                    pass
                
                # Create Chartink Link
                chart_link = f"https://chartink.com/stocks/{sym}.html"
                
                display_data.append({
                    "Symbol": sym,
                    "Link": chart_link,  # Hidden column for link
                    "Price": price,
                    "Change %": r['change_pct'],
                    "Volume": r['volume'],
                    "Trend": "🟢" if r['change_pct'] > 0 else "🔴",
                })
        except Exception as e:
            # Fallback if yfinance fails
            for r in results[:50]:
                 display_data.append({
                    "Symbol": r['symbol'],
                    "Link": f"https://chartink.com/stocks/{r['symbol']}.html",
                    "Price": r['price'],
                    "Change %": r['change_pct'],
                    "Volume": r['volume'],
                    "Trend": "🟢" if r['change_pct'] > 0 else "🔴",
                })

    df = pd.DataFrame(display_data)
    
    # metrics
    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric("Total Stocks", len(df))
    c2.metric("Bullish", len(df[df['Change %'] > 0]))
    
    # Export Button (Like Chartink's Excel button)
    csv = df.drop(columns=['Link']).to_csv(index=False).encode('utf-8')
    c3.download_button(
        "📥 Download CSV",
        csv,
        f"{scanner_name}.csv",
        "text/csv",
        key='download-csv'
    )

    # Link symbols to Chartink (Must be done BEFORE display)
    # We want to display the Symbol but link to the URL
    # So we replace 'Symbol' column data with the URL
    df['Symbol'] = df['Link']

    # Chartink-Style Table
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "Symbol": st.column_config.LinkColumn(
                "Stock Name", 
                help="Click to open chart",
                display_text="https://chartink.com/stocks/(.*).html"  # Extract symbol from URL
            ),
            "Link": None, # Hide raw link
            "Price": st.column_config.NumberColumn("Price", format="₹%.2f"),
            "Change %": st.column_config.NumberColumn("Chg%", format="%.2f%%"),
            "Volume": st.column_config.NumberColumn("Volume", format="%.0f"),
            "Trend": st.column_config.TextColumn("Trend", width="small"),
        },
        hide_index=True,
        height=500
    )
    
    # Optional: Pattern detection (only if historical data exists)
    if not df.empty and st.checkbox("🔍 Show Pattern Analysis (Requires Historical Data)", value=False):
        with st.spinner("Detecting patterns..."):
            try:
                from backend.strategy.pattern_detector import PatternDetector
                from backend.database.db import get_historical_data
                
                detector = PatternDetector()
                patterns_found = []
                
                for symbol in df['Symbol'].tolist()[:5]:  # Limit to 5 for performance
                    try:
                        hist_data = get_historical_data(symbol, days=30)
                        if hist_data and len(hist_data) > 20:
                            hist_df = pd.DataFrame(hist_data)
                            result = detector.analyze(hist_df, symbol)
                            if result['primary_pattern']:
                                patterns_found.append({
                                    'Symbol': symbol,
                                    'Pattern': result['primary_pattern'],
                                    'Confidence': f"{result['confidence']*100:.0f}%"
                                })
                    except Exception as e:
                        continue
                
                if patterns_found:
                    st.success(f"Found {len(patterns_found)} patterns!")
                    st.dataframe(pd.DataFrame(patterns_found), use_container_width=True, hide_index=True)
                else:
                    st.info("No historical data available for pattern detection. Run the scanner for a few days to build data.")
            except Exception as e:
                st.warning(f"Pattern detection unavailable: {str(e)}")
    
    # Quick Analysis Integration
    if not df.empty:
        st.markdown("---")
        selected_stock = st.selectbox("Quick Technical Score Check", df['Symbol'].tolist())
        if selected_stock:
             from backend.scanner.scanner_engine import ScannerEngine
             engine = ScannerEngine()
             row = df[df['Symbol'] == selected_stock].iloc[0]
             
             with st.spinner("AI analyzing setup..."):
                 analysis = engine.get_ai_analysis({'symbol': selected_stock, 'price': row['Live Price'], 'change_pct': row['Change %'], 'volume': row['Volume']})
                 
             c1, c2 = st.columns([1, 2])
             with c1:
                 st.metric("Setup Score", f"{analysis['score']}/10", analysis['rating'])
             with c2:
                 st.write("**Analysis:**")
                 for r in analysis['reasons']:
                     st.write(f"- {r}")

def show_dashboard():
    """Main Dashboard View with Auto-Refresh"""
    # Header with refresh countdown
    col_title, col_refresh = st.columns([3, 1])
    with col_title:
        st.title("🚀 Pro Dashboard")
        st.caption(f"Status: Live | Market: NSE India")
    with col_refresh:
        # Show countdown timer
        time_since_refresh = time.time() - st.session_state.last_refresh
        time_until_refresh = max(0, 300 - time_since_refresh)
        mins, secs = divmod(int(time_until_refresh), 60)
        st.metric("Next Refresh", f"{mins:02d}:{secs:02d}")
        if st.button("🔄 Refresh Now"):
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    conn = get_conn()
    try:
        total_symbols = conn.execute("SELECT COUNT(*) FROM symbols WHERE symbol_type='equity'").fetchone()[0]
        
        # Fix: Get today's scans with proper date handling
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        scanned_today = conn.execute(
            "SELECT COUNT(*) FROM scanner_results WHERE timestamp >= ?",
            (today_start,)
        ).fetchone()[0]
        
        alerts_today = conn.execute(
            "SELECT COUNT(DISTINCT symbol) FROM scanner_results WHERE alerted=1 AND timestamp >= ?",
            (today_start,)
        ).fetchone()[0]
        
        data_points = conn.execute("SELECT COUNT(*) FROM minute_data").fetchone()[0]
    finally:
        conn.close()
    
    col1.metric("Tracked Stocks", f"{total_symbols:,}")
    col2.metric("Scanned Today", f"{scanned_today:,}")
    col3.metric("Alerts Sent", f"{alerts_today:,}", "Telegram")
    col4.metric("Data Points", f"{data_points/1000:.1f}K")

    # --- PRO SETUPS ---
    st.markdown("---")
    st.header("🎯 Best Setups Today (0% to +3%)")
    
    # Try to get from database first
    conn = get_conn()
    try:
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        
        query = """
            SELECT DISTINCT sr.symbol, sr.price, sr.change_pct, sr.volume, sr.timestamp
            FROM scanner_results sr
            WHERE sr.timestamp >= ?
            AND sr.change_pct >= 0 AND sr.change_pct <= 3.0
            ORDER BY sr.timestamp DESC LIMIT 20
        """
        pro_setups = pd.read_sql_query(query, conn, params=(today_start,))
        
        # If database is empty, fetch live from Chartink
        if pro_setups.empty:
            st.info("📡 Fetching live data from Chartink...")
            try:
                from backend.scanner.chartink_scanner import ChartinkScanner
                
                # Use one of the main scanners
                scanner = ChartinkScanner(
                    "https://chartink.com/screener/nilay-swing-pick-algo",
                    "Main Scanner"
                )
                
                results = scanner.fetch_results(use_cache=False)
                
                # Filter for 0-3% range
                filtered = [r for r in results if 0 <= r.get('change_pct', 0) <= 3.0]
                
                if filtered:
                    pro_setups = pd.DataFrame(filtered[:20])
                    pro_setups['timestamp'] = pd.to_datetime(pro_setups['timestamp'])
                    st.success(f"✅ Found {len(filtered)} live stocks in 0-3% range!")
                else:
                    st.warning("No stocks currently in the 0-3% momentum zone.")
            except Exception as e:
                st.error(f"Error fetching live data: {e}")
        
    finally:
        conn.close()

    if not pro_setups.empty:
        col_list, col_chart = st.columns([1, 1.5])
        with col_list:
            st.dataframe(pro_setups[['symbol', 'price', 'change_pct']], use_container_width=True, hide_index=True)
            selected_symbol = st.selectbox("Quick View Chart", pro_setups['symbol'].tolist())
        with col_chart:
            if selected_symbol:
                tv_symbol = selected_symbol.split(' ')[0].split('(')[0].strip()
                st.components.v1.html(f"""
                    <div class="tradingview-widget-container" style="height:500px">
                        <div id="tradingview_12345"></div>
                        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                        <script type="text/javascript">
                        new TradingView.widget({{
                            "autosize": true,
                            "symbol": "NSE:{tv_symbol}",
                            "interval": "5",
                            "theme": "dark",
                            "style": "1",
                            "locale": "in",
                            "container_id": "tradingview_12345"
                        }});
                        </script>
                    </div>
                """, height=500)
    else:
        st.info("No stocks currently in the 0-3%momentum zone.")

def show_scanner_results():
    """Scanner Results View"""
    st.title("🎯 Scanner Results")
    limit = st.slider("Rows to show", 10, 500, 50)
    df = get_scanner_results(limit=limit)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No scanner results found.")

def show_stock_analysis():
    """Comprehensive Stock Analysis Page"""
    st.title("📈 AI Stock Analysis")
    st.caption("Deep technical and fundamental analysis for all 2600+ NSE stocks")
    
    symbols = get_equity_symbols()
    symbol = st.selectbox("Search Stock Symbol", symbols, placeholder="Type symbol e.g. Reliance")
    
    if symbol:
        st.markdown(f"## {symbol}")
        tab1, tab2, tab3 = st.tabs(["Technical Chart", "AI Fundamentals", "AI Trade Scorer"])
        
        with tab1:
            st.subheader("Price Action")
            st.components.v1.html(f"""
                <div class="tradingview-widget-container" style="height:600px">
                  <div id="tv_chart"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                  <script type="text/javascript">
                  new TradingView.widget({{
                    "width": "100%", "height": 600,
                    "symbol": "NSE:{symbol}", "interval": "D",
                    "theme": "dark", "style": "1",
                    "locale": "en", "container_id": "tv_chart"
                  }});
                  </script>
                </div>
            """, height=600)
            
        with tab2:
            st.subheader("Fundamental Analysis")
            import yfinance as yf
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.info
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", f"₹{info.get('marketCap', 0):,.0f}")
                c2.metric("LTP", f"₹{info.get('currentPrice', 0):,.2f}")
                c3.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
                c4.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
                
                st.markdown("---")
                st.markdown("**Business Summary:**")
                st.write(info.get('longBusinessSummary', 'No summary available.'))
                
                st.markdown("**Financial Highlights:**")
                f1, f2, f3 = st.columns(3)
                f1.write(f"- ROE: {info.get('returnOnEquity', 0)*100:.2f}%")
                f2.write(f"- Profit Margin: {info.get('profitMargins', 0)*100:.2f}%")
                f3.write(f"- Debt/Equity: {info.get('debtToEquity', 'N/A')}")
            except Exception as e:
                st.error(f"Fundamental data not available for this ticker: {e}")

        with tab3:
            st.subheader("AI System Scoring")
            try:
                from backend.scanner.scanner_engine import ScannerEngine
                engine = ScannerEngine()
                
                # Fetch recent data for AI
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.info
                
                stock_data = {
                    'symbol': symbol,
                    'price': info.get('currentPrice', 0),
                    'change_pct': info.get('regularMarketChangePercent', 0),
                    'volume': info.get('regularMarketVolume', 0)
                }
                
                with st.spinner("Analyzing setup requirements..."):
                    analysis = engine.get_ai_analysis(stock_data)
                
                st.metric("Setup Score", f"{analysis['score']}/10", analysis['rating'])
                st.markdown("### Analysis Breakdown")
                for reason in analysis['reasons']:
                    st.write(f"- {reason}")
                
                if 'explanation' in analysis:
                    st.success(f"**AI Guidance:** {analysis['explanation']}")
            except Exception as e:
                st.error(f"AI Scorer error: {e}")

def show_system_health():
    """System Health View"""
    st.title("🩺 System Health")
    conn = get_conn()
    logs = conn.execute("SELECT * FROM system_health ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()
    if logs:
        st.table(logs)
    else:
        st.info("No health logs found.")

# Routing Logic
if page == "Dashboard":
    show_dashboard()
elif page == "Scanner Results":
    show_scanner_results()
elif page == "Stock Analysis":
    show_stock_analysis()
elif page == "Chartink Live":
    show_chartink_live_scanner()
elif page == "FnO Dashboard":
    show_fno_dashboard()
elif page == "System Health":
    show_system_health()

st.markdown("---")
st.caption("Trade With Nilay Terminal | Build v1.4")
