# streamlit_app.py
import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, time

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
    st.session_state.reports = []

# -------------------------
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Helper Functions
# -------------------------
def fetch_alpha_vantage(symbol):
    """전일 종가 기준 주식 지수"""
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
    """전일 종가 기준 BTC/ETH"""
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
    """FRED 지표 데이터"""
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
    """CoinGecko 전일 데이터"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except:
        return {}

# -------------------------
# 보고서 생성 함수
# -------------------------
def generate_stock_report():
    now = datetime.now()
    report = {
        "title": f"Stock Report — {now.strftime('%Y-%m-%d %A %H:%M:%S')}",
        "headline": "Stock Report",
        "market_issues": "미국채, 금리, 정책, 뉴스 등 전일 자본시장 주요 요인 요약",
        "liquidity": "DXY, M2, 미국채장단기 금리, 발행량 등 기반 유동성 평가",
        "index_summary": "나스닥/코스피 상승/횡보/하락 확률 표시",
        "strategy": "장기/중기/단기 유리 전략 확률 표시"
    }
    return report

def generate_crypto_report():
    now = datetime.now()
    report = {
        "title": f"Crypto Report — {now.strftime('%Y-%m-%d %A %H:%M:%S')}",
        "headline": "Crypto Report",
        "market_issues": "암호화폐 시장 유의미한 이벤트/뉴스 요약",
        "impact_summary": "NASDAQ, 금리, 정책 등 전일 암호화폐시장 영향 요약",
        "liquidity": "스테이블코인 증감량, 대규모 입출금, 타거래소 움직임 등 유동성 평가",
        "index_summary": "BTC/ETH 상승/횡보/하락 확률 표시",
        "strategy": "장기/중기/단기, Spot/Futures 유리 전략 확률 표시"
    }
    return report

# -------------------------
# Report 메뉴
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("증권보고서 생성"):
            stock_report = generate_stock_report()
            st.session_state.reports.append(stock_report)
    
    with col2:
        if st.button("암호화폐보고서 생성"):
            crypto_report = generate_crypto_report()
            st.session_state.reports.append(crypto_report)

    if st.session_state.reports:
        titles = [r["title"] for r in st.session_state.reports]
        selected = st.selectbox("보고서 선택", titles)
        report = next(r for r in st.session_state.reports if r["title"] == selected)
        st.markdown(f"### {report['headline']}")
        st.markdown(f"**작성일:** {report['title'].split(' — ')[1]}")
        st.markdown(f"### 1. 전일까지의 자본시장/암호화폐 이슈\n{report.get('market_issues','')}")
        if "impact_summary" in report:
            st.markdown(f"### 2. 전일까지의 영향 요약\n{report['impact_summary']}")
        st.markdown(f"### 3. 유동성 평가\n{report.get('liquidity','')}")
        st.markdown(f"### 4. 지수/가격 가능성\n{report.get('index_summary','')}")
        st.markdown(f"### 5. 전략 추천\n{report.get('strategy','')}")
