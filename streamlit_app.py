# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, time as dt_time

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

# -------------------------
# secrets.json 불러오기
# -------------------------
SECRETS_PATH = "./secrets.json"
API_KEYS = {}
if st.secrets:
    API_KEYS = st.secrets
elif os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH, "r") as f:
        API_KEYS = json.load(f)

BINANCE_API_KEY = API_KEYS.get("BINANCE_API_KEY")
ALPHA_VANTAGE_API = API_KEYS.get("ALPHA_VANTAGE_API")
FRED_API_KEY = API_KEYS.get("FRED_API_KEY")

# -------------------------
# Session State 초기화
# -------------------------
if "report_result" not in st.session_state:
    st.session_state.report_result = ""

# -------------------------
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Helper Functions
# -------------------------
def fetch_alpha_vantage(symbol):
    """전일 종가 데이터"""
    if not ALPHA_VANTAGE_API:
        return pd.DataFrame()
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_API}&outputsize=compact"
        resp = requests.get(url, timeout=10)
        data = resp.json().get("Time Series (Daily)", {})
        df = pd.DataFrame.from_dict(data, orient="index").astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    except:
        return pd.DataFrame()

def fetch_binance(symbol="BTCUSDT"):
    """전일 종가 데이터"""
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=30"
        resp = requests.get(url, timeout=10)
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
    """GEMINI 데이터 기반 Report 생성"""
    now = datetime.now()
    report_lines = []
    report_lines.append(f"작성일: {now.strftime('%Y-%m-%d %A %H:%M:%S')}")
    
    # 1. 자본시장 이벤트 / 경제지표 요약
    report_lines.append("\n### 1. 전일까지의 자본시장 이벤트/경제지표 요약")
    # GEMINI 내부 모니터링 기반 데이터 참조 (예시)
    report_lines.append("- 주요 경제지표 발표 요약")
    report_lines.append("- 기업 실적, 정책 이벤트 요약")
    
    # 2. NASDAQ/BTC 전일까지 상황
    report_lines.append("\n### 2. 전일까지 NASDAQ/비트코인 상황")
    nasdaq = fetch_alpha_vantage("^IXIC")
    btc = fetch_binance("BTCUSDT")
    if not nasdaq.empty:
        report_lines.append(f"- NASDAQ 전일 종가: {nasdaq['4. close'].iloc[-1]:,.2f} USD")
    if not btc.empty:
        report_lines.append(f"- BTC 전일 종가: {btc['Close'].iloc[-1]:,.2f} USD")
    
    # 3. 종합 분석 / 예측
    report_lines.append("\n### 3. 종합 분석/예측")
    report_lines.append("#### Stock 시장 분석/예측")
    report_lines.append("- 기술적 분석: GEMINI 내부 판단 기준")
    report_lines.append("- 상승/하락/횡보 가능성 제시")
    report_lines.append("- 전략 추천: 장기/중기/단기 유리 전략")
    
    report_lines.append("\n#### Crypto 시장 분석/예측")
    report_lines.append("- 기술적 분석: GEMINI 내부 판단 기준")
    report_lines.append("- 상승/하락/횡보 가능성 제시")
    report_lines.append("- 전략 추천: 장기/중기/단기 유리 전략")
    
    return "\n".join(report_lines)

# -------------------------
# Report 화면
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")
    if st.button("보고서 생성 (전일까지 데이터 기준, 오전 8시까지)"):
        st.session_state.report_result = generate_report()
    if st.session_state.report_result:
        st.text_area("Generated Report", st.session_state.report_result, height=600)
