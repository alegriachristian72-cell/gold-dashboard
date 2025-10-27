import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- Page Config ---
st.set_page_config(page_title="Gold Dashboard", page_icon="🟡", layout="wide")

# --- Auto refresh settings ---
REFRESH_MINUTES = 3  # You can change this to 1, 2, 5, etc.
st.markdown(f"⏱️ Auto-refreshing every **{REFRESH_MINUTES} minutes**")
st_autorefresh(interval=REFRESH_MINUTES * 60 * 1000, key="gold_refresh")

# --- Header ---
st.title("🟡 Gold (XAU/USD) Live Dashboard")
st.caption("Auto-Updating • Technical Summary • Sentiment • News • Chart")

# --- Fetch Gold Data (Spot + Fallback) ---
try:
    gold = yf.Ticker("XAUUSD=X")
    data = gold.history(period="1mo", interval="1h")

    # Fallback if empty
    if data.empty:
        gold = yf.Ticker("GC=F")  # Gold Futures fallback
        data = gold.history(period="1mo", interval="1h")

except Exception as e:
    data = pd.DataFrame()

if data.empty:
    st.error("Failed to fetch gold data. Try again later.")
    st.stop()

# --- Calculate Values ---
price = data["Close"].iloc[-1]
change = round((data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2] * 100, 2)

# --- Indicators ---
rsi = ta.rsi(data["Close"], length=14).iloc[-1]
macd = ta.macd(data["Close"])
macd_hist = macd["MACDh_12_26_9"].iloc[-1]
ema_fast = ta.ema(data["Close"], length=12).iloc[-1]
ema_slow = ta.ema(data["Close"], length=26).iloc[-1]

# --- Technical Votes ---
votes = []
if rsi < 30:
    votes.append("buy")
elif rsi > 70:
    votes.append("sell")
else:
    votes.append("neutral")

if macd_hist > 0:
    votes.append("buy")
elif macd_hist < 0:
    votes.append("sell")

if ema_fast > ema_slow:
    votes.append("buy")
else:
    votes.append("sell")

# --- Summary Logic ---
buy_votes = votes.count("buy")
sell_votes = votes.count("sell")
bullish_percent = int((buy_votes / len(votes)) * 100)
bearish_percent = 100 - bullish_percent

if buy_votes >= 3:
    summary = "🟢 Strong Buy"
elif buy_votes == 2:
    summary = "🟩 Buy"
elif sell_votes >= 3:
    summary = "🔴 Strong Sell"
elif sell_votes == 2:
    summary = "🟥 Sell"
else:
    summary = "⚪ Neutral"

# --- Overview ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Price (USD)", f"{price:,.2f}")
col2.metric("Change (1h)", f"{change} %")
col3.metric("RSI (14)", f"{rsi:.2f}")
col4.metric("Summary", summary)

st.divider()

# --- Sentiment Gauge ---
st.subheader("📊 Market Sentiment")
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=bullish_percent,
    delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
    title={'text': "Bullish Sentiment (%)"},
    gauge={
        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
        'bar': {'color': "gold"},
        'bgcolor': "white",
        'steps': [
            {'range': [0, 20], 'color': '#ff4d4d'},
            {'range': [20, 40], 'color': '#ff9999'},
            {'range': [40, 60], 'color': '#f2f2f2'},
            {'range': [60, 80], 'color': '#a3ffa3'},
            {'range': [80, 100], 'color': '#33cc33'}
        ],
        'threshold': {
            'line': {'color': "black", 'width': 4},
            'thickness': 0.75,
            'value': bullish_percent
        }
    }
))
fig.update_layout(margin={'t': 50, 'b': 0, 'l': 0, 'r': 0}, height=300, paper_bgcolor="white")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- TradingView Chart ---
st.subheader("📈 Live TradingView Chart")
st.markdown("""
<iframe src="https://s.tradingview.com/widgetembed/?symbol=OANDA:XAUUSD&interval=60&theme=light&style=1"
        width="100%" height="500" frameborder="0"></iframe>
""", unsafe_allow_html=True)

st.divider()

# --- News Section ---
st.subheader("📰 Latest Gold News (via Investing.com RSS)")
rss_url = "https://www.investing.com/rss/news_301.rss"
try:
    r = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "xml")
    items = soup.find_all("item")

    for item in items[:5]:
        title = item.title.text
        link = item.link.text
        pub = item.pubDate.text
        st.markdown(f"**[{title}]({link})**")
        st.caption(pub)
        st.write("---")

except Exception:
    st.error("Couldn't fetch news feed. Try again later.")
