# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime
from alpha_vantage.timeseries import TimeSeries

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

# -------------------------
# secrets.json 불러오기
# -------------------------
SECRETS_PATH = "./secrets.json"
BINANCE_API_KEY = None
BINANCE_SECRET_KEY = None
FRED_API_KEY = None
ALPHA_VANTAGE_API = None
COINGECKO_API = None
if os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH, "r") as f:
        secrets = json.load(f)
        BINANCE_API_KEY = secrets.get("BINANCE_API_KEY")
        BINANCE_SECRET_KEY = secrets.get("BINANCE_SECRET_KEY")
        FRED_API_KEY = secrets.get("FRED_API_KEY")
        ALPHA_VANTAGE_API = secrets.get("ALPHA_VANTAGE_API")
        COINGECKO_API = secrets.get("COINGECKO_API")

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
body {background-color: #f5f5f5;}
</style>
""", unsafe_allow_html=True)
st.markdown("# YNANCE ANALYST", unsafe_allow_html=True)

# -------------------------
# Session State 초기화
# -------------------------
if "home_data" not in st.session_state:
    st.session_state.home_data = {}

# -------------------------
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Helper Functions
# -------------------------

def fetch_alpha_vantage(symbol="^IXIC", interval="Daily"):
    """Alpha Vantage 시세 가져오기"""
    if not ALPHA_VANTAGE_API:
        return pd.DataFrame()
    ts = TimeSeries(key=ALPHA_VANTAGE_API, output_format='pandas')
    data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
    data = data.rename(columns={"1. open":"open","2. high":"high","3. low":"low","4. close":"close","5. volume":"volume"})
    data.index = pd.to_datetime(data.index)
    return data

def fetch_fred(series_id):
    """FRED 데이터 가져오기"""
    if not FRED_API_KEY:
        return None
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json().get("observations", [])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors='coerce')
        return df[["date","value"]].dropna()
    return None

def fetch_binance(symbol="BTCUSDT"):
    """Binance 전일 종가 가져오기"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=2"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        last_close = float(data[-2][4])
        return last_close
    return None

def fetch_coingecko(coin_id="bitcoin"):
    """CoinGecko 시세"""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json()
        return data.get(coin_id, {}).get("usd")
    return None

def fetch_fear_greed_index():
    """암호화폐 공포&탐욕지수"""
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    resp = requests.get(url)
    if resp.ok:
        data = resp.json().get("data", [{}])[0]
        return int(data.get("value",0)), data.get("value_classification","Unknown")
    return None, None

# -------------------------
# Home 메뉴
# -------------------------
if selected_menu == "Home":
    st.subheader("Home — Market Overview")

    st.write("### 주요 자산 시세 (전일 종가 기준)")

    # Alpha Vantage: NASDAQ
    nasdaq_data = fetch_alpha_vantage("^IXIC")
    nasdaq_close = nasdaq_data["close"].iloc[-1] if not nasdaq_data.empty else None

    # Alpha Vantage: KOSPI
    kospi_data = fetch_alpha_vantage("^KS11")
    kospi_close = kospi_data["close"].iloc[-1] if not kospi_data.empty else None

    # Binance: BTC
    btc_close = fetch_binance("BTCUSDT")
    eth_close = fetch_binance("ETHUSDT")

    # CoinGecko: BTC/ETH
    btc_price_cg = fetch_coingecko("bitcoin")
    eth_price_cg = fetch_coingecko("ethereum")

    # FRED: DXY, M2, US short/long term rates
    dxy = fetch_fred("DTWEXBGS")  # Dollar Index
    m2 = fetch_fred("M2SL")       # M2 통화량
    us_2y = fetch_fred("DGS2")    # 2Y Treasury
    us_10y = fetch_fred("DGS10")  # 10Y Treasury

    # Fear & Greed Index
    crypto_fg_value, crypto_fg_class = fetch_fear_greed_index()

    # Display
    col1, col2, col3 = st.columns(3)
    col1.metric("NASDAQ (^IXIC)", nasdaq_close)
    col2.metric("KOSPI (^KS11)", kospi_close)
    col3.metric("BTC/USD", btc_close)

    col1.metric("ETH/USD", eth_close)
    col2.metric("BTC/USD (CoinGecko)", btc_price_cg)
    col3.metric("ETH/USD (CoinGecko)", eth_price_cg)

    st.write("### 주요 경제 지표")
    col1, col2, col3 = st.columns(3)
    col1.metric("DXY", dxy["value"].iloc[-1] if dxy is not None else "N/A")
    col2.metric("M2 통화량", m2["value"].iloc[-1] if m2 is not None else "N/A")
    col3.metric("US 2Y Treasury", us_2y["value"].iloc[-1] if us_2y is not None else "N/A")
    col1.metric("US 10Y Treasury", us_10y["value"].iloc[-1] if us_10y is not None else "N/A")

    st.write("### Crypto Fear & Greed Index")
    if crypto_fg_value:
        st.metric("Crypto F&G Index", crypto_fg_value, crypto_fg_class)
    else:
        st.info("Crypto F&G Index 데이터 없음")

# -------------------------
# Markets 메뉴
# -------------------------
elif selected_menu == "Markets":
    st.subheader("Markets (전일 종가 기준)")
    st.info("실시간 WebSocket 제거, REST 기반 전일 데이터 표시")

# -------------------------
# Trading 메뉴
# -------------------------
elif selected_menu == "Trading":
    st.subheader("Trading")
    st.info("실시간 차트는 제거, 전일 종가 기준 데이터만 표시")

# -------------------------
# Talk / Report 메뉴
# -------------------------
elif selected_menu in ["Talk","Report"]:
    st.subheader(selected_menu)
    st.info("GEMINI API 연동 데이터 표시")

# -------------------------
# Assets 메뉴
# -------------------------
elif selected_menu == "Assets":
    st.subheader("Assets — 자리 (읽기 전용)")
    st.info("REST API 없음")

st.write("---")
st.caption("Home 메뉴: 전일 종가 / 주요 경제지표 / Crypto F&G Index 표시")
