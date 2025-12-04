# streamlit_app_home.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
from binance.client import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE Home Dashboard", layout="wide")
st.markdown("# YNANCE Home Dashboard", unsafe_allow_html=True)

# -------------------------
# Load secrets.json
# -------------------------
import json, os
SECRETS_PATH = "./secrets.json"
with open(SECRETS_PATH, "r") as f:
    secrets = json.load(f)

ALPHA_API = secrets.get("ALPHA_VANTAGE_API")
BINANCE_API = secrets.get("BINANCE_API_KEY")
BINANCE_SECRET = secrets.get("BINANCE_SECRET_KEY")
FRED_API = secrets.get("FRED_API_KEY")
COINGECKO_API = secrets.get("COINGECKO_API")
# -------------------------
# Helper functions
# -------------------------
def get_alpha_weekly(symbol):
    ts = TimeSeries(key=ALPHA_API, output_format='pandas')
    data, _ = ts.get_weekly(symbol=symbol)
    data = data.sort_index()
    data['MA20'] = data['4. close'].rolling(20).mean()
    data['EMA20'] = data['4. close'].ewm(span=20, adjust=False).mean()
    delta = data['4. close'].diff()
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    roll_up, roll_down = up.rolling(14).mean(), down.rolling(14).mean()
    RS = roll_up / roll_down
    data['RSI'] = 100 - (100 / (1 + RS))
    data['MACD'] = data['4. close'].ewm(span=12, adjust=False).mean() - data['4. close'].ewm(span=26, adjust=False).mean()
    return data.tail(52)

def get_binance_weekly(symbol):
    client = Client(BINANCE_API, BINANCE_SECRET)
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1WEEK, limit=52)
    df = pd.DataFrame(klines, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","trades",
        "taker_base_vol","taker_quote_vol","ignore"
    ])
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['MA20'] = df['close'].rolling(20).mean()
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    delta = df['close'].diff()
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    roll_up, roll_down = up.rolling(14).mean(), down.rolling(14).mean()
    RS = roll_up / roll_down
    df['RSI'] = 100 - (100 / (1 + RS))
    df['MACD'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    return df

def get_fred_series(series_id):
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API}&file_type=json"
    r = requests.get(url)
    data = r.json().get("observations", [])
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df

def get_crypto_sentiment():
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    r = requests.get(url)
    data = r.json().get("data", [{}])[0]
    return int(data.get("value",0)), data.get("value_classification","Unknown")

def plot_candlestick(df, title="Candlestick"):
    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(df.index, df['close'], label='Close', color='blue')
    ax.plot(df.index, df['MA20'], label='MA20', color='orange')
    ax.plot(df.index, df['EMA20'], label='EMA20', color='green')
    ax.set_title(title)
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)

# -------------------------
# Home Layout
# -------------------------
st.subheader("📊 상단 영역: NASDAQ / KOSPI / BTC")
col1, col2, col3 = st.columns(3)

with col1:
    nasdaq = get_alpha_weekly("^IXIC")  # Alpha Vantage NASDAQ symbol
    last_close = nasdaq['4. close'].iloc[-1]
    prev_close = nasdaq['4. close'].iloc[-2]
    vol_change = (nasdaq['5. volume'].iloc[-1] - nasdaq['5. volume'].iloc[-2]) / nasdaq['5. volume'].iloc[-2] * 100
    st.metric("NASDAQ Close", f"{last_close:.2f}", delta=f"{last_close-prev_close:.2f}")
    st.metric("Volume Change (%)", f"{vol_change:.2f}%")
    plot_candlestick(nasdaq, "NASDAQ 주봉(52주)")

with col2:
    kospi = get_alpha_weekly("KOSPI")  # Alpha Vantage KOSPI symbol placeholder
    last_close = kospi['4. close'].iloc[-1]
    prev_close = kospi['4. close'].iloc[-2]
    vol_change = (kospi['5. volume'].iloc[-1] - kospi['5. volume'].iloc[-2]) / kospi['5. volume'].iloc[-2] * 100
    st.metric("KOSPI Close", f"{last_close:.2f}", delta=f"{last_close-prev_close:.2f}")
    st.metric("Volume Change (%)", f"{vol_change:.2f}%")
    plot_candlestick(kospi, "KOSPI 주봉(52주)")

with col3:
    btc = get_binance_weekly("BTCUSDT")
    last_close = btc['close'].iloc[-1]
    prev_close = btc['close'].iloc[-2]
    vol_change = (btc['volume'].iloc[-1] - btc['volume'].iloc[-2]) / btc['volume'].iloc[-2] * 100
    st.metric("BTC Close", f"{last_close:.2f}", delta=f"{last_close-prev_close:.2f}")
    st.metric("Volume Change (%)", f"{vol_change:.2f}%")
    plot_candlestick(btc, "BTC 주봉(52주)")

st.subheader("📈 중단 영역: 미국 본원통화, 미국채 금리, DXY")
col1, col2, col3 = st.columns(3)
with col1:
    m2 = get_fred_series("M2SL")  # M2 예시
    st.metric("M2 통화량", f"{m2['value'].iloc[-1]:,.0f}", delta=f"{m2['value'].iloc[-1]-m2['value'].iloc[-2]:,.0f}")
with col2:
    treasury_10y = get_fred_series("DGS10")
    treasury_2y = get_fred_series("DGS2")
    spread = treasury_10y['value'].iloc[-1] - treasury_2y['value'].iloc[-1]
    st.metric("10Y-2Y 금리차", f"{spread:.2f}%")
with col3:
    dxy = get_fred_series("DTWEXBGS")
    st.metric("DXY", f"{dxy['value'].iloc[-1]:.2f}")

st.subheader("🧠 하단 영역: 심리지표")
nasdaq_fng, nasdaq_class = get_crypto_sentiment()
st.metric("NASDAQ Fear & Greed", nasdaq_fng, nasdaq_class)
