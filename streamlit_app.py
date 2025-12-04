# streamlit_home.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime
import websocket
import threading
import time

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
if "btc_price" not in st.session_state:
    st.session_state.btc_price = None
if "ws_started" not in st.session_state:
    st.session_state.ws_started = False

# -------------------------
# Helper Functions
# -------------------------
def fetch_alpha_vantage(symbol):
    """Alpha Vantage 전일 종가 데이터"""
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

def fetch_fng_crypto():
    """Crypto Fear & Greed Index"""
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1&crypto=1", timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [{}])[0]
        return {"value": int(data.get("value",0)), "classification": data.get("value_classification","Unknown")}
    except:
        return {"value":0,"classification":"Unknown"}

def fetch_fng_stock():
    """Stock Fear & Greed Index"""
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [{}])[0]
        return {"value": int(data.get("value",0)), "classification": data.get("value_classification","Unknown")}
    except:
        return {"value":0,"classification":"Unknown"}

def fetch_fred(series_id):
    """FRED 지표"""
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
# Binance WebSocket
# -------------------------
def on_message(ws, message):
    import json
    data = json.loads(message)
    price = float(data["p"])
    st.session_state.btc_price = price

def start_binance_ws(symbol="btcusdt"):
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    ws.run_forever()

# WebSocket 시작
if not st.session_state.ws_started:
    st.session_state.ws_started = True
    threading.Thread(target=start_binance_ws, daemon=True).start()
    time.sleep(1)  # 연결 안정화

# -------------------------
# Home 화면
# -------------------------
st.subheader("Home — Market Overview & Indicators")

# NASDAQ / KOSPI / BTC 전일 종가
col1, col2, col3 = st.columns(3)
with col1:
    nasdaq = fetch_alpha_vantage("^IXIC")
    if not nasdaq.empty:
        st.line_chart(nasdaq["4. close"])
        st.write(f"NASDAQ 전일 종가: {nasdaq['4. close'].iloc[-1]:,.2f} USD")
    else:
        st.write("NASDAQ 데이터 없음")

with col2:
    kospi = fetch_alpha_vantage("^KS11")
    if not kospi.empty:
        st.line_chart(kospi["4. close"])
        st.write(f"KOSPI 전일 종가: {kospi['4. close'].iloc[-1]:,.0f} KRW")
    else:
        st.write("KOSPI 데이터 없음")

with col3:
    btc_price = st.session_state.btc_price
    if btc_price:
        st.metric("BTC 현재가", f"{btc_price:,.2f} USD")
    else:
        st.write("BTC WebSocket 연결 대기 중...")

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
        st.write(f"{name}: {df['value'].iloc[-1]:,.2f}")
    else:
        st.write(f"{name} 데이터 없음")

st.caption("데이터는 전일 종가/실시간 WebSocket BTC 가격, REST API 기준으로 가져옵니다.")
