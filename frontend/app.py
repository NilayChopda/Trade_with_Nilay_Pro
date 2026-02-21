"""
Trade With Nilay - Dashboard v2.1
Fixes: Live Chartink data, no charts, working research report
"""

import streamlit as st
import pandas as pd
import time
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twn.frontend")

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load env
env_path = Path(__file__).resolve().parent.parent / "backend" / "config" / "keys.env"
load_dotenv(env_path)

from backend.database.db import get_conn
from backend.utils.market_data import MarketData

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trade With Nilay Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    html, body, .main { background-color: #020617; color: #E2E8F0; font-family: 'Outfit', sans-serif; }
    h1 { background: linear-gradient(to right, #60A5FA, #A78BFA);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
         font-weight: 800; text-transform: uppercase; letter-spacing: 2px; }
    h2, h3 { color: #F8FAFC; font-weight: 600; }

    div[data-testid="stMetric"] {
        background: rgba(15,23,42,0.85); border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; padding: 18px !important; transition: 0.3s;
    }
    div[data-testid="stMetric"]:hover { border-color: #3B82F6; }

    .premium-table { width:100%; border-collapse:separate; border-spacing:0 6px; }
    .premium-table th { color:#94A3B8; text-align:left; padding:10px 14px;
        font-size:0.76rem; text-transform:uppercase; letter-spacing:1px; }
    .premium-table tr { background:rgba(30,41,59,0.7); transition:0.2s; }
    .premium-table tr:hover { background:rgba(51,65,85,0.9); }
    .premium-table td { padding:14px; color:#F8FAFC; font-weight:500;
        border-top:1px solid rgba(255,255,255,0.04); }
    .premium-table td:first-child { border-radius:10px 0 0 10px; border-left:3px solid #3B82F6; }
    .premium-table td:last-child { border-radius:0 10px 10px 0; }

    .badge { padding:3px 9px; border-radius:6px; font-weight:800;
        font-size:0.68rem; display:inline-block; }
    .badge-up { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
    .badge-dn { background:rgba(239,68,68,0.15); color:#EF4444; border:1px solid rgba(239,68,68,0.3); }
    .chg-pos { color:#10B981; font-weight:bold; }
    .chg-neg { color:#EF4444; font-weight:bold; }

    .report-box {
        background:linear-gradient(165deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
        border:1px solid rgba(59,130,246,0.3); padding:32px; border-radius:20px;
        line-height:1.8; box-shadow:0 20px 50px rgba(0,0,0,0.5);
    }

    section[data-testid="stSidebar"] { background-color:#020617 !important;
        border-right:1px solid rgba(255,255,255,0.05); }
    .stButton>button { background:linear-gradient(145deg,#1e293b,#0f172a);
        color:#94A3B8; border:1px solid rgba(255,255,255,0.06); border-radius:10px;
        padding:9px 20px; font-weight:600; transition:0.3s; }
    .stButton>button:hover { color:#3B82F6; border-color:#3B82F6; }
    #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
    ::-webkit-scrollbar { width:6px; }
    ::-webkit-scrollbar-thumb { background:#334155; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Trade With Nilay")
    st.caption("Advanced Analytics Pro v2.1")
    st.markdown("---")
    page = st.radio("Navigation", [
        "Dashboard",
        "Antigravity Research",
        "Scanner Results",
        "Stock Analysis",
        "Chartink Live",
        "FnO Dashboard",
        "System Health",
    ])
    st.markdown("---")
    if st.button("🔄 Clear Cache & Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def is_nse_cash(sym: str) -> bool:
    sym = str(sym).upper()
    exclude = ['NIFTY', 'BANKNIFTY', 'BEES', 'ETF', 'FUND', 'GOLD',
               'REIT', 'INVIT', 'INDEX', 'LIQUID', 'SILVER', 'NASDAQ']
    return not (any(k in sym for k in exclude) or '-' in sym)


def render_table(df: pd.DataFrame):
    """Render styled stock table — no charts, no links."""
    html = """<table class="premium-table">
    <thead><tr>
        <th>#</th><th>Symbol</th><th>Price (₹)</th>
        <th>Change %</th><th>Volume</th><th>Setup</th><th>Date</th>
    </tr></thead><tbody>"""

    for i, (_, row) in enumerate(df.iterrows(), 1):
        chg = float(row.get('change_pct', 0) or 0)
        chg_cls = "chg-pos" if chg >= 0 else "chg-neg"
        arrow = "▲" if chg >= 0 else "▼"
        badge_cls = "badge-up" if chg >= 0 else "badge-dn"
        badge_txt = f"{chg:+.2f}%"

        price = row.get('price', 0)
        try:
            price_str = f"₹{float(price):,.2f}"
        except Exception:
            price_str = str(price)

        vol = row.get('volume', 0)
        try:
            vol_str = f"{int(float(vol)):,}"
        except Exception:
            vol_str = str(vol)

        setup = str(row.get('patterns', '-') or '-')
        if '|' in setup:
            setup = setup.split('|')[-1].strip()
        if len(setup) > 20:
            setup = setup[:20] + "…"

        ts = row.get('timestamp', None)
        try:
            date_str = pd.to_datetime(ts, unit='s').strftime('%d/%m/%y')
        except Exception:
            date_str = str(ts)[:10] if ts else '-'

        html += f"""
        <tr>
            <td style="opacity:0.4;font-size:0.78rem;">{i}</td>
            <td style="color:#60A5FA;font-weight:700;">{row.get('symbol','?')}</td>
            <td>{price_str}</td>
            <td><span class="badge {badge_cls}">{arrow} {badge_txt}</span></td>
            <td style="opacity:0.65;font-size:0.83rem;">{vol_str}</td>
            <td style="color:#94A3B8;font-size:0.8rem;">{setup}</td>
            <td style="opacity:0.45;font-size:0.75rem;">{date_str}</td>
        </tr>"""

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


def render_live_table(results: list):
    """Render live Chartink results (list of dicts)."""
    html = """<table class="premium-table">
    <thead><tr>
        <th>#</th><th>Symbol</th><th>Price (₹)</th><th>Change %</th><th>Volume</th>
    </tr></thead><tbody>"""

    for i, r in enumerate(results, 1):
        chg = float(r.get('change_pct', 0) or 0)
        arrow = "▲" if chg >= 0 else "▼"
        badge_cls = "badge-up" if chg >= 0 else "badge-dn"
        price = r.get('price', 0)
        try:
            price_str = f"₹{float(price):,.2f}"
        except Exception:
            price_str = str(price)
        vol = r.get('volume', 0)
        try:
            vol_str = f"{int(float(vol)):,}"
        except Exception:
            vol_str = str(vol)

        html += f"""
        <tr>
            <td style="opacity:0.4;font-size:0.78rem;">{i}</td>
            <td style="color:#60A5FA;font-weight:700;">{r.get('symbol','?')}</td>
            <td>{price_str}</td>
            <td><span class="badge {badge_cls}">{arrow} {chg:+.2f}%</span></td>
            <td style="opacity:0.65;font-size:0.83rem;">{vol_str}</td>
        </tr>"""

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


# ─── LIVE CHARTINK FETCH (shared across Dashboard & Chartink Live) ─────────────
SCANNERS = {
    "NILAY SWING PICK - ALGO": {"url": "https://chartink.com/screener/nilay-swing-pick-algo"},
    "NILAY SWING PICK 2.0":    {"url": "https://chartink.com/screener/nilay-swing-pick-2-0"},
    "NILAY FNO AUTOPICK":      {"url": "https://chartink.com/screener/nilay-fno-autopick-scanner"},
}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_chartink(url: str, name: str, clause: str = None, _refresh_key: int = 0):
    """Fetch results from Chartink. Cached for 5 min."""
    from backend.scanner.chartink_scanner import ChartinkScanner
    scanner = ChartinkScanner(url, name)
    results = scanner.fetch_results(use_cache=False, scan_clause=clause)
    if results:
        results = [r for r in results if is_nse_cash(r.get('symbol', ''))]
        results = [r for r in results if -25.0 <= r.get('change_pct', 0) <= 25.0]
    return results or []


# ─── PAGE: DASHBOARD ──────────────────────────────────────────────────────────
def show_dashboard():
    st.markdown("## 📡 Live Scanner Dashboard")
    st.caption("Real-time stocks from Nilay's Chartink scanners · Refreshes every 5 minutes")

    col_sel, col_ref = st.columns([2, 1])
    with col_sel:
        scanner_name = st.selectbox("Select Scanner", list(SCANNERS.keys()), label_visibility="collapsed")
    with col_ref:
        if st.button("🔄 Force Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    refresh_key = int(time.time() // 300)  # changes every 5 min
    config = SCANNERS[scanner_name]

    with st.spinner(f"Loading {scanner_name}..."):
        results = fetch_live_chartink(config['url'], scanner_name, _refresh_key=refresh_key)

    if not results:
        st.warning("⚠️ No results returned. Market may be closed or Chartink blocked the request.")
        st.info("Market hours: **9:15 AM – 3:30 PM IST, Mon–Fri**")
        return

    # Search filter
    search = st.text_input("🔍 Filter symbol", placeholder="e.g. RELIANCE", label_visibility="collapsed")
    if search:
        results = [r for r in results if search.upper() in r.get('symbol', '').upper()]

    # Metrics
    bullish = [r for r in results if r.get('change_pct', 0) > 0]
    sweet = [r for r in results if 0 <= r.get('change_pct', 0) <= 3]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Total Stocks", len(results))
    c2.metric("🟢 Bullish", len(bullish))
    c3.metric("🔴 Bearish", len(results) - len(bullish))
    c4.metric("🎯 Sweet Spot 0–3%", len(sweet))

    st.write("")
    render_live_table(results)

    # CSV
    csv_df = pd.DataFrame(results)
    csv = csv_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, f"{scanner_name}.csv", "text/csv")

    next_refresh = 300 - (int(time.time()) % 300)
    st.caption(f"⏱ Auto-refreshes in ~{next_refresh}s | Source: Chartink.com")


# ─── PAGE: ANTIGRAVITY RESEARCH ───────────────────────────────────────────────
def show_research_page():
    st.title("🚀 Antigravity AI Research")
    st.caption("Instant AI fundamental analysis for any NSE stock")

    # API Key — check env first, then ask user
    gemini_key = os.getenv("GEMINI_API_KEY") or ""
    if not gemini_key:
        gemini_key = st.text_input(
            "🔑 Google Gemini API Key (get free at [aistudio.google.com](https://aistudio.google.com))",
            type="password",
            placeholder="AIza..."
        )
        if not gemini_key:
            st.info("Enter your Gemini API key above to enable AI reports.")
            st.markdown("""
            **How to get a free key:**
            1. Go to [aistudio.google.com](https://aistudio.google.com)
            2. Sign in with Google
            3. Click **Get API key** → Create API Key
            4. Paste it above
            """)
            return

    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input(
            "Stock Symbol",
            placeholder="e.g. RELIANCE, TCS, TATAMOTORS, HDFC",
            label_visibility="collapsed"
        ).upper().strip()
    with col2:
        go = st.button("✨ Generate Report", type="primary", use_container_width=True)

    if not symbol:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;opacity:0.45;">
            <h2>🔬 Enter a stock symbol to begin</h2>
            <p>AI-powered analysis · Yahoo Finance data · Google Gemini</p>
        </div>""", unsafe_allow_html=True)
        return

    if not go and len(symbol) < 3:
        return

    # ── Fetch fundamentals ──
    import yfinance as yf

    with st.spinner(f"Fetching data for {symbol}..."):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info or {}
        except Exception as e:
            info = {}
            logger.warning(f"yfinance failed for {symbol}: {e}")

    company = info.get("longName") or info.get("shortName") or symbol
    price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    mktcap = info.get("marketCap", 0)
    mktcap_cr = round(mktcap / 1e7, 1) if mktcap else "N/A"
    pe = info.get("trailingPE", "N/A")
    pb = info.get("priceToBook", "N/A")
    roe = round(info.get("returnOnEquity", 0) * 100, 1) if info.get("returnOnEquity") else "N/A"
    de = info.get("debtToEquity", "N/A")
    margin = round(info.get("profitMargins", 0) * 100, 1) if info.get("profitMargins") else "N/A"
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    desc = info.get("longBusinessSummary", "")[:600]

    # ── Display metrics ──
    st.markdown(f"## 🏆 {company} `({symbol})`")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"₹{price:,.2f}" if price else "N/A")
    c2.metric("Market Cap", f"₹{mktcap_cr} Cr" if mktcap_cr != "N/A" else "N/A")
    c3.metric("P/E Ratio", str(pe))
    c4.metric("ROE %", str(roe))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Sector", sector)
    c6.metric("P/Book", str(pb))
    c7.metric("Debt/Equity", str(de))
    c8.metric("Net Margin %", str(margin))

    if desc:
        with st.expander("📖 Company Description", expanded=False):
            st.write(desc)

    # ── AI Report ──
    st.markdown("---")
    st.markdown("### 🤖 AI Fundamental Report")

    with st.spinner("Generating AI report... (takes 10–20 seconds)"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')

            prompt = f"""
You are a top-tier Indian equity research analyst. Generate a structured research report for:

**Stock:** {company} ({symbol}) | NSE India
**Sector:** {sector} | {industry}
**Price:** ₹{price} | **Market Cap:** ₹{mktcap_cr} Cr
**PE:** {pe} | **PB:** {pb} | **ROE:** {roe}% | **Net Margin:** {margin}%
**Debt/Equity:** {de}

Brief Description:
{desc}

Generate a comprehensive research report in this exact format:

## 🏢 Business Overview
[Explain the business model simply. What is their moat/competitive advantage?]

## 📊 Financial Health
[Comment on valuation (cheap/expensive?), profitability, debt levels. Be specific.]

## 🚀 Growth Drivers (3 reasons to be Bullish)
1. ...
2. ...
3. ...

## ⚠️ Key Risks (3 reasons to be Cautious)
1. ...
2. ...
3. ...

## 🎯 Antigravity Verdict
**Rating:** [STRONG BUY / BUY / HOLD / AVOID]
**Quality Score:** X/10
**Growth Score:** X/10
**Summary:** [1-line investment thesis]

Be concise, insightful, and suitable for a retail investor. Use markdown formatting.
"""
            response = model.generate_content(prompt)
            report_text = response.text

            st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)
            st.caption(f"Generated at {pd.Timestamp.now().strftime('%d %b %Y %H:%M')} IST | Antigravity Research v2.1")

        except Exception as e:
            st.error(f"❌ AI report failed: {e}")
            logger.error(f"Gemini error for {symbol}: {e}", exc_info=True)
            if "API_KEY" in str(e).upper() or "INVALID" in str(e).upper():
                st.warning("Your API key may be invalid. Please re-enter it above.")
            elif "QUOTA" in str(e).upper() or "LIMIT" in str(e).upper():
                st.warning("Gemini free quota hit. Wait a minute and try again.")


# ─── PAGE: SCANNER RESULTS (from DB) ─────────────────────────────────────────
def show_scanner_results():
    st.title("📡 Scanner Results")
    st.caption("Historical results stored in database — run a fresh scan to update")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Filter by symbol", placeholder="e.g. TCS", label_visibility="collapsed")
    with col2:
        if st.button("🔄 Run Fresh Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning Chartink scanners and saving to DB..."):
                try:
                    from backend.scanner.scanner_engine import ScannerEngine
                    engine = ScannerEngine()
                    engine.run_once(send_alerts=False)
                    st.cache_data.clear()
                    st.success("✅ Scan complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Scan failed: {e}")

    try:
        conn = get_conn()
        df = pd.read_sql_query(
            "SELECT symbol, price, change_pct, volume, patterns, timestamp "
            "FROM scanner_results ORDER BY timestamp DESC LIMIT 200",
            conn
        )
        conn.close()

        if search:
            df = df[df['symbol'].str.contains(search, case=False, na=False)]
        df = df[df['symbol'].apply(is_nse_cash)]

        if not df.empty:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df))
            c2.metric("Bullish", len(df[df['change_pct'] > 0]))
            c3.metric("Sweet Spot", len(df[(df['change_pct'] >= 0) & (df['change_pct'] <= 3)]))
            try:
                last = pd.to_datetime(df['timestamp'].iloc[0], unit='s').strftime('%d %b %H:%M')
                c4.metric("Last Scan", last)
            except Exception:
                c4.metric("Last Scan", "–")

            st.write("")
            render_table(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "scanner_results.csv", "text/csv")
        else:
            st.info("📭 No results in database. Click **Run Fresh Scan** to populate.")

    except Exception as e:
        st.error(f"DB error: {e}")


# ─── PAGE: STOCK ANALYSIS ─────────────────────────────────────────────────────
def show_stock_analysis():
    st.title("📈 Stock Analysis")
    st.caption("AI trade scoring for any NSE stock")

    symbol = st.text_input("Enter Stock Symbol", placeholder="e.g. RELIANCE, INFY, TCS").upper().strip()
    if not symbol:
        return

    import yfinance as yf

    with st.spinner(f"Scoring {symbol}..."):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info or {}
            stock_data = {
                'symbol': symbol,
                'price': info.get('currentPrice', 0),
                'change_pct': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0)
            }

            from backend.scanner.scanner_engine import ScannerEngine
            engine = ScannerEngine()
            analysis = engine.get_ai_analysis(stock_data)

        except Exception as e:
            st.error(f"Error: {e}")
            return

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Setup Score", f"{analysis.get('score', 0):.1f}/10")
        st.metric("Rating", analysis.get('rating', 'N/A'))
    with c2:
        st.markdown("**Analysis Breakdown:**")
        for r in analysis.get('reasons', []):
            st.write(f"• {r}")

    if analysis.get('explanation'):
        st.success(f"**AI Guidance:** {analysis['explanation']}")


# ─── PAGE: CHARTINK LIVE ─────────────────────────────────────────────────────
def show_chartink_live_scanner():
    st.title("🎯 Chartink Live Scanner")
    st.caption("Live stocks from Nilay's Chartink screeners · NSE Cash only")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        scanner_name = st.selectbox("Select Scanner", list(SCANNERS.keys()))
    with col2:
        auto_ref = st.selectbox("Auto Refresh", ["5 Minutes", "1 Minute", "Off"], index=0)
    with col3:
        st.write("")
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    ttl_map = {"5 Minutes": 300, "1 Minute": 60, "Off": 86400}
    ttl = ttl_map[auto_ref]
    refresh_key = int(time.time() // ttl) if auto_ref != "Off" else 0

    if auto_ref != "Off":
        next_r = ttl - (int(time.time()) % ttl)
        st.caption(f"⏱ Auto-refreshing every {auto_ref} · Next refresh in ~{next_r}s")

    config = SCANNERS[scanner_name]
    with st.spinner(f"Fetching {scanner_name}..."):
        results = fetch_live_chartink(config['url'], scanner_name, _refresh_key=refresh_key)

    if not results:
        st.error("❌ No results. Chartink may have blocked the request or market is closed.")
        return

    search = st.text_input("🔍 Filter", label_visibility="collapsed", placeholder="Filter symbol...")
    if search:
        results = [r for r in results if search.upper() in r.get('symbol', '').upper()]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Stocks", len(results))
    c2.metric("Bullish", len([r for r in results if r.get('change_pct', 0) > 0]))
    c3.metric("0–3% Sweet Spot", len([r for r in results if 0 <= r.get('change_pct', 0) <= 3]))

    st.write("")
    render_live_table(results)

    csv = pd.DataFrame(results).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export CSV", csv, f"{scanner_name}.csv", "text/csv")


# ─── PAGE: FNO DASHBOARD ─────────────────────────────────────────────────────
def show_fno_dashboard():
    st.title("📊 FnO Scanner")
    st.caption("F&O segment picks from Nilay's Chartink screeners")

    fno_scanners = {
        "NILAY FNO AUTOPICK": {"url": "https://chartink.com/screener/nilay-fno-autopick-scanner"},
        "NILAY FNO VOLATILITY SCAN": {
            "url": "https://chartink.com/screener/process",
            "clause": "( {33489} ( daily avg true range( 14 ) < 10 days ago avg true range( 14 ) and daily avg true range( 14 ) / daily close < 0.08 and daily close > ( weekly max( 52 , weekly close ) * 0.75 ) and daily ema( daily close , 50 ) > daily ema( daily close , 150 ) and daily ema( daily close , 150 ) > daily ema( daily close , 200 ) and daily close > daily ema( daily close , 50 ) and daily close > 10 and daily close * daily volume > 1000000 ) )"
        },
    }

    col1, col2 = st.columns([2, 1])
    with col1:
        scanner_name = st.selectbox("Select F&O Scanner", list(fno_scanners.keys()))
    with col2:
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    config = fno_scanners[scanner_name]
    refresh_key = int(time.time() // 300)

    with st.spinner("Fetching F&O results..."):
        results = fetch_live_chartink(config['url'], scanner_name,
                                      clause=config.get('clause'), _refresh_key=refresh_key)

    if not results:
        st.info("📭 No F&O candidates found. Market may be closed.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(results))
    c2.metric("Bullish", len([r for r in results if r.get('change_pct', 0) > 0]))
    c3.metric("0–3% Range", len([r for r in results if 0 <= r.get('change_pct', 0) <= 3]))

    st.write("")
    render_live_table(results)

    csv = pd.DataFrame(results).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export CSV", csv, f"{scanner_name}.csv", "text/csv")


# ─── PAGE: SYSTEM HEALTH ─────────────────────────────────────────────────────
def show_system_health():
    st.title("🩺 System Health")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Database")
        try:
            conn = get_conn()
            count = conn.execute("SELECT COUNT(*) FROM scanner_results").fetchone()[0]
            latest = conn.execute("SELECT MAX(timestamp) FROM scanner_results").fetchone()[0]
            conn.close()
            st.metric("Records", count)
            if latest:
                st.metric("Last Scan", pd.to_datetime(latest, unit='s').strftime('%d %b %Y %H:%M'))
            st.success("✅ Database OK")
        except Exception as e:
            st.error(f"❌ DB error: {e}")

    with c2:
        st.subheader("Environment")
        key = os.getenv("GEMINI_API_KEY", "")
        tg_tok = os.getenv("TELEGRAM_BOT_TOKEN", "")
        st.write(f"Gemini Key: {'✅ Set' if key else '❌ Missing'}")
        st.write(f"Telegram Token: {'✅ Set' if tg_tok else '❌ Missing'}")
        st.write(f"keys.env path: `{env_path}`")
        st.write(f"keys.env exists: {'✅' if env_path.exists() else '❌'}")


# ─── ROUTING ──────────────────────────────────────────────────────────────────
if page == "Dashboard":
    show_dashboard()
elif page == "Antigravity Research":
    show_research_page()
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


# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="background:linear-gradient(90deg,#0f172a,#1e293b);padding:24px;border-radius:18px;
     border:1px solid rgba(59,130,246,0.2);margin-top:24px;">
    <div style="display:flex;justify-content:space-around;text-align:center;margin-bottom:20px;">
        <div><h2 style="color:#3b82f6;margin:0;">1,240+</h2><p style="color:#94a3b8;font-size:0.82rem;">Active Traders</p></div>
        <div style="border-left:1px solid rgba(255,255,255,0.08);border-right:1px solid rgba(255,255,255,0.08);padding:0 32px;">
            <h2 style="color:#10b981;margin:0;">68.4%</h2><p style="color:#94a3b8;font-size:0.82rem;">AI Win Rate</p></div>
        <div><h2 style="color:#f59e0b;margin:0;">15.8k</h2><p style="color:#94a3b8;font-size:0.82rem;">Daily AI Scans</p></div>
    </div>
    <div style="text-align:center;">
        <a href="https://t.me/Trade_with_Nilay" target="_blank" style="text-decoration:none;">
            <button style="background:#3b82f6;color:white;border:none;padding:11px 28px;
                border-radius:10px;font-weight:800;cursor:pointer;">
                📲 JOIN ON TELEGRAM
            </button>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

st.caption("Trade With Nilay Terminal | v2.1 | NSE Cash Segment | AI-Powered")
