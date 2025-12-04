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

if hasattr(st, "secrets") and st.secrets:
    API_KEYS = st.secrets
else:
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
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

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
    except:
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
    except:
        return pd.DataFrame()

def generate_report():
    """GEMINI 기반 가상 보고서 생성"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %A %H:%M:%S")

    # 전일까지 데이터 불러오기
    nasdaq = fetch_alpha_vantage("^IXIC")
    btc = fetch_binance("BTCUSDT")
    
    report = f"### Report — Market & Crypto Analysis\n**작성일:** {date_str}\n\n"
    
    # 1. 자본시장 이슈
    report += "### 1. 전일까지의 자본시장 이슈\nGEMINI 모니터링 기반 자본시장 뉴스, 이벤트 요약\n\n"
    
    # 2. 이벤트
    report += "### 2. 전일까지의 이벤트\n경제지표 발표, 기업 실적, 정책 이벤트 등 요약\n\n"
    
    # 3. NASDAQ/BTC 전일 상황
    if not nasdaq.empty:
        report += f"### 3. 전일까지 나스닥/비트코인 상황\nNASDAQ 전일 종가: {nasdaq['4. close'].iloc[-1]:,.2f} USD\n"
    else:
        report += "NASDAQ 데이터 없음\n"
    if not btc.empty:
        report += f"BTC 전일 종가: {btc['Close'].iloc[-1]:,.2f} USD\n"
    else:
        report += "BTC 데이터 없음\n\n"
    
    # 4. 종합 분석/예측
    report += "### 4. 종합 분석/예측\n- Stock 시장 분석/예측: GEMINI 기반 기술적/시장 변수 종합\n- Crypto 시장 분석/예측: GEMINI 기반 기술적/시장 변수 종합\n"
    report += "\n- 상승/하락/횡보 가능성 및 장기/중기/단기 전략 추천 포함\n"
    
    return report

# -------------------------
# Report 메뉴
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")
    
    if st.button("보고서 생성"):
        st.session_state.report_generated = True
    
    if st.session_state.report_generated:
        report_content = generate_report()
        st.markdown(report_content)
