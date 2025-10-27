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

# --- Custom Dark Theme ---
st.markdown("""
    <style>
        body {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stApp {
            background-color: #0E1117;
        }
        h1, h2, h3, h4, h5 {
            color: #FFD700 !important;
        }
        .css-1v0mbdj, .css-10trblm, .css-1d391kg {
            color: #FAFAFA !important;
        }
        a {
            color: #FFD700 !important;
        }
        hr {
            border: 1px solid #FFD700;
        }
    </style>
""", unsafe_allow_html=True)

# --- Auto Refresh ---
REFRESH_MINUTES = 3
st.markdown(f"⏱️ Auto-refreshing every **{REFRESH_MINUTES} minutes**")
st_autorefresh(interval=REFRESH_MINUTES * 60 * 1000, key="gold_refresh")

# --- Header ---
st.title("🟡 Gold (XAU/USD) Live Dashboard")
st.caption("Auto-Updating • Technical Summary • Sentiment • News • Chart")

# --- Fetch Gold Data ---
gold = yf.Ticker("XAUUSD=X")
data = gold.history(period="1mo", interval="1h")

# Fallback: if empty, use Gold Futures
if data.empty:
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1mo", interval="1h")

if data.empty:
    st.error("Failed to fetch data. Try again later.")
    st.stop()

# --- Calculate Indicators ---
data["RSI"] = 100 - (100 / (1 + data["Close"].diff().apply(lambda x: np.nan if x == 0 else x).rolling(14).mean()))

# --- Display Overview ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Price (USD)", f"{data['Close'].iloc[-1]:,.2f}")
col2.metric("Change (1h)", f"{((data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100):.2f} %")
col3.metric("RSI (14)", f"{data['RSI'].iloc[-1]:.2f}")
col4.metric("Summary", "🟩 Buy" if data['RSI'].iloc[-1] < 30 else "🟥 Sell" if data['RSI'].iloc[-1] > 70 else "🟨 Neutral")

# --- Sentiment (simple logic) ---
rsi_val = data['RSI'].iloc[-1]
sentiment = "🟩 Bullish" if rsi_val < 30 else "🟥 Bearish" if rsi_val > 70 else "🟨 Neutral"

st.subheader("📊 Market Sentiment")
st.markdown(f"**Current sentiment:** {sentiment}")

# --- TradingView Chart Embed ---
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
    soup = BeautifulSoup(r.text, "xml")
    items = soup.find_all("item")

    for item in items[:6]:
        title = item.title.text
        link = item.link.text
        pub = item.pubDate.text
        st.markdown(f"**[{title}]({link})**")
        st.caption(pub)
        st.write("---")

except Exception as e:
    st.error(f"Couldn't fetch news feed. Try again later. ({e})")
