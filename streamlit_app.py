# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime

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

def fetch_binance(symbol="BTCUSDT"):
    """Binance 전일 종가 데이터"""
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

# -------------------------
# Home 화면
# -------------------------
if selected_menu == "Home":
    st.subheader("Home — Market Overview & Indicators")

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

# -------------------------
# Report 메뉴
# -------------------------
elif selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")

    # 전일 날짜/요일/시간
    report_date = datetime.now() - pd.Timedelta(days=1)
    report_info = f"보고서 작성일: {report_date.strftime('%Y-%m-%d %A %H:%M')}"
    st.markdown(f"### {report_info}")

    # GEMINI 기반 데이터 모니터링 참고 (실제 데이터는 호출하지 않음)
    st.markdown("#### Stock Market Analysis")
    st.write("- 전일까지의 자본시장 이슈 요약")
    st.write("- 전일까지 이벤트 요약")
    st.write("- 전일까지 나스닥 상황 요약")
    st.write("- 다방면의 변수 종합 분석 및 예측 (Stock)")

    st.markdown("#### Crypto Market Analysis")
    st.write("- 전일까지의 암호화폐 주요 이슈 요약")
    st.write("- 전일까지 이벤트 요약")
    st.write("- 전일까지 BTC/ETH 등 주요 코인 상황 요약")
    st.write("- 다방면의 변수 종합 분석 및 예측 (Crypto)")

    st.caption("데이터는 GEMINI 모니터링 기반이며, 시각화나 외부 URL은 포함하지 않습니다.")

# -------------------------
# 기타 메뉴는 빈 구조 유지
# -------------------------
else:
    st.write(f"{selected_menu} 메뉴는 준비 중입니다.")
