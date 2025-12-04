# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, time as dtime

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
ALPHA_VANTAGE_API = API_KEYS.get("ALPHA_VANTAGE_API")
FRED_API_KEY = API_KEYS.get("FRED_API_KEY")
COINGECKO_API_KEY = API_KEYS.get("COINGECKO_API_KEY")
KOSIS_API_KEY = API_KEYS.get("KOSIS_API_KEY")

# -------------------------
# Session State 초기화
# -------------------------
if "reports" not in st.session_state:
    st.session_state.reports = {}

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
    except:
        return pd.DataFrame()

# -------------------------
# 보고서 작성 함수
# -------------------------
def generate_reports():
    today = datetime.now()
    cutoff_time = dtime(8, 0)
    if today.time() > cutoff_time:
        st.warning("보고서는 오전 8시 이전 데이터를 기준으로 생성해야 합니다.")
        return
    
    reports = {}

    # Stock Report
    stock_report = "### Stock Report\n"
    stock_report += f"작성일: {today.strftime('%Y-%m-%d %A %H:%M:%S')}\n\n"
    stock_report += "1. 전일까지 주목 요인: GEMINI 모니터링 기반 자본시장 뉴스/정책/경제 이벤트 요약\n"
    stock_report += "2. 유동성 평가: DXY, M2, 미국채 장단기 금리, 발행량 등 종합\n"
    stock_report += "3. 나스닥/코스피 상승/횡보/하락 가능성 확률\n"
    stock_report += "4. 장기/중기/단기 전략 추천 확률\n"
    reports["Stock Report"] = stock_report

    # Crypto Report
    crypto_report = "### Crypto Report\n"
    crypto_report += f"작성일: {today.strftime('%Y-%m-%d %A %H:%M:%S')}\n\n"
    crypto_report += "1. 전일까지 유의미한 암호화폐 이벤트/뉴스 요약\n"
    crypto_report += "2. 전일 주식시장/금리/정책 영향을 받은 주요 사항 요약\n"
    crypto_report += "3. 유동성 평가: 스테이블코인 증감량, 거래소/지갑 입출금 대규모 이슈\n"
    crypto_report += "4. BTC/ETH 상승/횡보/하락 가능성 확률\n"
    crypto_report += "5. 장기/중기/단기, Spot/Futures 전략 추천 확률\n"
    reports["Crypto Report"] = crypto_report

    st.session_state.reports = reports
    st.success("보고서가 생성되었습니다!")

# -------------------------
# Report 메뉴
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")
    
    if st.button("보고서 생성"):
        generate_reports()
    
    if st.session_state.reports:
        report_choice = st.selectbox("생성된 보고서 선택", list(st.session_state.reports.keys()))
        st.markdown(st.session_state.reports[report_choice])
