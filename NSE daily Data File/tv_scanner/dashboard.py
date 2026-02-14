import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="NSE TV Scanner", layout="wide")

st.title("📈 NSE TradingView Scanner Results")

if os.path.exists('results.csv'):
    try:
        df = pd.read_csv('results.csv')
        
        st.subheader(f"Latest Scan Results ({len(df)} stocks found)")
        
        if not df.empty:
            # Filters
            st.sidebar.header("Filters")
            min_price = st.sidebar.number_input("Min Price", 0.0, float(df['close'].max()), 0.0)
            
            filtered_df = df[df['close'] >= min_price]
            
            st.dataframe(filtered_df)
            
            # Download
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "scanner_results.csv", "text/csv")
        else:
            st.info("No stocks matched criteria in the last run.")
            
    except Exception as e:
        st.error(f"Error reading results: {e}")
else:
    st.warning("No results found. Run the scanner first.")

st.markdown("---")
st.text("Automated by GitHub Actions / Local Scheduler")
