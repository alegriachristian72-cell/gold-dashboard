import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
from streamlit_autorefresh import st_autorefresh

# --- Page setup ---
st.set_page_config(
    page_title="Gold (XAU/USD) Dashboard",
    page_icon="🟡",
    layout="wide",
)

# --- Dark Theme Styling ---
st.markdown("""
    <style>
        body, .stApp {background-color:#0E1117; color:#FAFAFA;}
        h1, h2, h3, h4, h5 {color:#FFD700 !important;}
        a {color:#FFD700 !important;}
        hr {border:1px solid #FFD700;}
    </style>
""", unsafe_allow_html=True)

# --- Auto Refresh (LIVE MODE) ---
REFRESH_SECONDS = 30  # refresh every 30 seconds
st.markdown(f"⏱️ Auto-refreshing every **{REFRESH_SECONDS} seconds**")
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="gold_live_refresh")

# --- Header ---
st.title("🟡 Gold (XAU/USD) Live Dashboard")
st.caption("Live Auto-Updating • Technical Summary • Sentiment • News • Chart")

# --- Fetch Gold Data ---
gold = yf.Ticker("XAUUSD=X")
data = gold.history(period="1mo", interval="1h")

# Fallback: if empty, try Gold Futures
if data.empty:
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1mo", interval="1h")

if data.empty:
    st.error("Failed to fetch data. Try again later.")
    st.stop()

# --- Compute RSI properly ---
delta = data["Close"].diff()
gain = delta.where(delta > 0, 0).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

# --- Display Metrics ---
col1, col2, col3, col4 = st.columns(4)
price = data["Close"].iloc[-1]
change = (price / data["Close"].iloc[-2] - 1) * 100
rsi_val = data["RSI"].iloc[-1]
summary = "🟩 Buy" if rsi_val < 30 else "🟥 Sell" if rsi_val > 70 else "🟨 Neutral"

col1.metric("Price (USD)", f"{price:,.2f}")
col2.metric("Change (1h)", f"{change:.2f} %")
col3.metric("RSI (14)", f"{rsi_val:.2f}")
col4.metric("Summary", summary)

# --- Sentiment ---
sentiment = "🟩 Bullish" if rsi_val < 30 else "🟥 Bearish" if rsi_val > 70 else "🟨 Neutral"
st.subheader("📊 Market Sentiment")
st.markdown(f"**Current sentiment:** {sentiment}")

# --- TradingView Chart ---
st.subheader("📈 Live TradingView Chart")
st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_gold&symbol=OANDA%3AXAUUSD&interval=60&theme=dark&style=1&locale=en&utm_source=&utm_medium=widget&utm_campaign=chart&utm_term=OANDA%3AXAUUSD"
width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
""", unsafe_allow_html=True)

# --- News Section ---
st.subheader("📰 Latest Gold News (via Google Finance)")

rss_url = "https://news.google.com/rss/search?q=gold+OR+XAUUSD+OR+Gold+price&hl=en-US&gl=US&ceid=US:en"

try:
    r = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.find_all("item")

    for item in items[:6]:
        title = item.title.text if item.title else "Untitled"
        link = item.link.text if item.link else "#"
        pub = item.pubDate.text if item.pubDate else ""
        st.markdown(f"**[{title}]({link})**")
        if pub:
            st.caption(pub)
        st.write("---")

except Exception as e:
    st.error(f"Couldn't fetch news feed. Try again later. ({e})")
