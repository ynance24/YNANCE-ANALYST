# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta

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
if "report_data" not in st.session_state:
    st.session_state.report_data = {}

# -------------------------
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Helper Functions
# -------------------------
def get_yesterday():
    return (datetime.now() - timedelta(days=1)).date()

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

def fetch_coingecko(symbol="bitcoin"):
    if not COINGECKO_API_KEY:
        return pd.DataFrame()
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=7"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        prices = pd.DataFrame(data["prices"], columns=["timestamp","price"])
        prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
        return prices
    except:
        return pd.DataFrame()

# -------------------------
# Report 생성 함수
# -------------------------
def generate_report():
    today = datetime.now()
    yesterday = get_yesterday()
    
    # --- Stock Report ---
    stock_report = {}
    # 헤드라인
    stock_report["headline"] = "Stock Report"
    # 자본시장/경제지표/뉴스 요약 (Gemini 모니터링)
    stock_report["market_events"] = "GEMINI 모니터링 기반 전일 자본시장 이벤트 및 뉴스 요약"
    # 유동성 지표
    stock_report["liquidity"] = "DXY, M2, 장단기 금리, 미국채 수요/발행량 기반 유동성 평가"
    # 나스닥/코스피 상승/횡보/하락 확률
    stock_report["trend_prob"] = {"상승": 0.35, "횡보":0.45, "하락":0.20}
    # 전략 추천
    stock_report["strategy"] = {"장기":0.50, "중기":0.30, "단기":0.20}

    # --- Crypto Report ---
    crypto_report = {}
    crypto_report["headline"] = "Crypto Report"
    # 시장 이벤트 요약
    crypto_report["market_events"] = "GEMINI 모니터링 기반 전일 암호화폐 시장 이벤트 요약"
    # 주요 영향 요인
    crypto_report["influences"] = "NASDAQ, 금리, 정책 등 전일 암호화폐시장 영향 요약"
    # 유동성 평가
    crypto_report["liquidity"] = "스테이블코인 증감량, 타 거래소/지갑 입출금 등 유동성 평가"
    # 상승/횡보/하락 확률
    crypto_report["trend_prob"] = {"상승":0.40, "횡보":0.35, "하락":0.25}
    # 전략 추천
    crypto_report["strategy"] = {"장기":0.45, "중기":0.35, "단기":0.20}

    # 저장
    st.session_state.report_data = {"stock": stock_report, "crypto": crypto_report, "date":today}

# -------------------------
# Report 메뉴
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Automated Market & Crypto Analysis")
    if st.button("보고서 생성"):
        generate_report()
        st.success("보고서 생성 완료!")

    report_data = st.session_state.get("report_data", {})
    if report_data:
        # 작성일
        st.markdown(f"**작성일:** {report_data['date'].strftime('%Y-%m-%d %A %H:%M:%S')}")
        # Stock Report
        stock = report_data["stock"]
        st.markdown(f"### {stock['headline']}")
        st.markdown(f"- **자본시장 이벤트/뉴스 요약:** {stock['market_events']}")
        st.markdown(f"- **유동성 평가:** {stock['liquidity']}")
        st.markdown(f"- **상승/횡보/하락 확률:** {stock['trend_prob']}")
        st.markdown(f"- **장기/중기/단기 전략 확률:** {stock['strategy']}")
        # Crypto Report
        crypto = report_data["crypto"]
        st.markdown(f"### {crypto['headline']}")
        st.markdown(f"- **시장 이벤트 요약:** {crypto['market_events']}")
        st.markdown(f"- **주요 영향 요인:** {crypto['influences']}")
        st.markdown(f"- **유동성 평가:** {crypto['liquidity']}")
        st.markdown(f"- **상승/횡보/하락 확률:** {crypto['trend_prob']}")
        st.markdown(f"- **장기/중기/단기 전략 확률:** {crypto['strategy']}")
