import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, time as dtime
import google.generativeai as genai

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
GEMINI_API_KEY = API_KEYS.get("GEMINI_API_KEY")

# Gemini 설정
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

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
# Gemini 호출 함수
# -------------------------
def ask_gemini(prompt: str) -> str:
    if not model:
        return "❌ Gemini API KEY가 없습니다. secrets.json을 확인하세요."

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini 분석 실패: {str(e)}"

# -------------------------
# 데이터 수집 Helper (기본 유지)
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
# 보고서 생성
# -------------------------
def generate_reports():
    today = datetime.now()
    cutoff_time = dtime(8, 0)

    if today.time() > cutoff_time:
        st.warning("보고서는 오전 8시 이전 데이터를 기준으로 생성해야 합니다.")
        return

    date_str = today.strftime("%Y-%m-%d")

    # 시장 데이터 기본 수집
    nasdaq = fetch_alpha_vantage("NDX")
    kospi = fetch_alpha_vantage("KS11")
    btc = fetch_binance("BTCUSDT")

    # Gemini 분석 프롬프트
    stock_prompt = f"""
다음 데이터를 기반으로 자본시장 뉴스, 정책, 경제지표를 분석하고
전문가 수준의 Stock Report를 작성해라:

[데이터]
NASDAQ 최근 30일:
{nasdaq.tail(5).to_string()}

KOSPI 최근 30일:
{kospi.tail(5).to_string()}

요구사항:
- 뉴스·정책·지표를 종합적으로 분석
- 상승/횡보/하락 확률을 수치로 제시
- 장기/중기/단기 전략 제시
- Markdown 형식으로 작성
"""

    crypto_prompt = f"""
다음 데이터를 기반으로 암호화폐 시장 뉴스, 금융시장 영향, 유동성 흐름을 분석하고
전문가 수준의 Crypto Report를 작성해라:

[데이터]
BTC 최근 30일:
{btc.tail(5).to_string()}

요구사항:
- 주요 이벤트·정책·매크로 영향 분석
- BTC/ETH 방향성 확률 제시
- Spot/Futures 전략 제시
- Markdown 형식으로 작성
"""

    # Gemini 호출
    stock_report = ask_gemini(stock_prompt)
    crypto_report = ask_gemini(crypto_prompt)

    # 파일 생성
    stock_filename = f"Stock_Report_{date_str}.md"
    crypto_filename = f"Crypto_Report_{date_str}.md"

    with open(stock_filename, "w", encoding="utf-8") as f:
        f.write(stock_report)

    with open(crypto_filename, "w", encoding="utf-8") as f:
        f.write(crypto_report)

    # 세션 저장
    st.session_state.reports = {
        "Stock Report": {
            "filename": stock_filename,
            "content": stock_report
        },
        "Crypto Report": {
            "filename": crypto_filename,
            "content": crypto_report
        }
    }

    st.success("보고서가 생성되었습니다!")

# -------------------------
# Report 메뉴
# -------------------------
if selected_menu == "Report":
    st.subheader("📊 Report — Automated Market & Crypto Analysis")

    if st.button("보고서 생성"):
        generate_reports()

    if st.session_state.reports:
        report_choice = st.selectbox(
            "생성된 보고서 선택",
            list(st.session_state.reports.keys())
        )

        report = st.session_state.reports[report_choice]

        # 다운로드 버튼
        with open(report["filename"], "r", encoding="utf-8") as f:
            st.download_button(
                label=f"📥 {report['filename']} 다운로드",
                data=f.read(),
                file_name=report["filename"]
            )

        # 본문 펼치기
        with st.expander("본문 펼치기"):
            st.markdown(report["content"])
