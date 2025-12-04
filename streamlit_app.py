# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import os

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

# -------------------------
# secrets.json 불러오기
# -------------------------
SECRETS_PATH = "./secrets.json"
API_KEYS = {}
if os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH, "r") as f:
        API_KEYS = json.load(f)

BINANCE_API_KEY = API_KEYS.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = API_KEYS.get("BINANCE_SECRET_KEY")
FRED_API_KEY = API_KEYS.get("FRED_API_KEY")
ALPHA_VANTAGE_API = API_KEYS.get("ALPHA_VANTAGE_API")

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
def fetch_alpha_vantage(symbol):
    if not ALPHA_VANTAGE_API:
        return pd.DataFrame()
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_API}&outputsize=compact"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("Time Series (Daily)", {})
        df = pd.DataFrame.from_dict(data, orient="index").astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    except Exception as e:
        st.warning(f"Alpha Vantage API 호출 실패 ({symbol}): {e}")
        return pd.DataFrame()

def fetch_binance(symbol="BTCUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=30"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data, columns=[
            "Open time","Open","High","Low","Close","Volume","Close time",
            "Quote asset volume","Num trades","Taker buy base","Taker buy quote","Ignore"
        ])
        df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
        numeric_cols = ["Open","High","Low","Close","Volume"]
        df[numeric_cols] = df[numeric_cols].astype(float)
        return df[["Open time"] + numeric_cols]
    except Exception as e:
        st.warning(f"Binance API 호출 실패 ({symbol}): {e}")
        return pd.DataFrame()

def fetch_fng_crypto():
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1&crypto=1", timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [{}])[0]
        return {"value": int(data.get("value",0)), "classification": data.get("value_classification","Unknown")}
    except:
        return {"value":0,"classification":"Unknown"}

def fetch_fng_stock():
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [{}])[0]
        return {"value": int(data.get("value",0)), "classification": data.get("value_classification","Unknown")}
    except:
        return {"value":0,"classification":"Unknown"}

def fetch_fred(series_id):
    if not FRED_API_KEY:
        return pd.DataFrame()
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("observations", [])
        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df
    except Exception as e:
        st.warning(f"FRED API 호출 실패 ({series_id}): {e}")
        return pd.DataFrame()

# -------------------------
# Home 화면
# -------------------------
if selected_menu == "Home":
    st.subheader("Home — Market Overview & Indicators")

    # NASDAQ / KOSPI / BTC 전일 종가
    col1, col2, col3 = st.columns(3)
    with col1:
        nasdaq = fetch_alpha_vantage("^IXIC")
        if not nasdaq.empty:
            st.line_chart(nasdaq["4. close"])
        st.write("NASDAQ 전일 종가")

    with col2:
        kospi = fetch_alpha_vantage("^KS11")
        if not kospi.empty:
            st.line_chart(kospi["4. close"])
        st.write("KOSPI 전일 종가")

    with col3:
        btc = fetch_binance("BTCUSDT")
        if not btc.empty:
            st.line_chart(btc["Close"])
        st.write("BTC 전일 종가")

    # Fear & Greed Index
    col4, col5 = st.columns(2)
    fng_stock = fetch_fng_stock()
    fng_crypto = fetch_fng_crypto()
    with col4:
        st.metric("Stock F&G", f"{fng_stock['value']}", f"{fng_stock['classification']}")
    with col5:
        st.metric("Crypto F&G", f"{fng_crypto['value']}", f"{fng_crypto['classification']}")

    # FRED 주요 지표
    st.markdown("### FRED 주요 경제지표")
    fred_series = {
        "DXY": "DTWEXBGS",
        "M2": "M2SL",
        "US Federal Reserve Base Money": "BOGMBASE",
        "10Y Treasury Rate": "DGS10",
        "2Y Treasury Rate": "DGS2"
    }
    for name, series in fred_series.items():
        df = fetch_fred(series)
        if not df.empty:
            st.line_chart(df.set_index("date")["value"])
            st.write(name)

    st.caption("데이터는 전일 종가/전일 시점 기준으로 REST API에서 가져옵니다.")
