import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime, time as dtime

# ------------------------------------------------
# Config
# ------------------------------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

# ------------------------------------------------
# secrets.json 불러오기 (절대 앱 죽지 않게 처리)
# ------------------------------------------------
SECRETS_PATH = "./secrets.json"
API_KEYS = {}
try:
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH, "r") as f:
            API_KEYS = json.load(f)
except:
    API_KEYS = {}

BINANCE_API_KEY = API_KEYS.get("BINANCE_API_KEY")
ALPHA_VANTAGE_API = API_KEYS.get("ALPHA_VANTAGE_API")
FRED_API_KEY = API_KEYS.get("FRED_API_KEY")
COINGECKO_API_KEY = API_KEYS.get("COINGECKO_API_KEY")
KOSIS_API_KEY = API_KEYS.get("KOSIS_API_KEY")
GEMINI_API_KEY = API_KEYS.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

# ------------------------------------------------
# Gemini 설정 (없어도 에러 없이 진행)
# ------------------------------------------------
import google.generativeai as genai
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except:
        pass

def ask_gemini(prompt: str):
    """Gemini 불러오는 함수 — 실패해도 앱 절대 안 죽음"""
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key 없음 — 기본 텍스트로 보고서 생성됨."
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Gemini 호출 오류: {str(e)}\n기본 보고서로 대체합니다."


# ------------------------------------------------
# Session State 초기화
# ------------------------------------------------
if "reports" not in st.session_state:
    st.session_state.reports = {}

# ------------------------------------------------
# 메뉴
# ------------------------------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# ------------------------------------------------
# Helper Functions
# ------------------------------------------------
def fetch_alpha_vantage(symbol):
    if not ALPHA_VANTAGE_API:
        return pd.DataFrame()
    try:
        url = (
            f"https://www.alphavantage.co/query?"
            f"function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_API}&outputsize=compact"
        )
        resp = requests.get(url, timeout=10)
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
        data = resp.json()
        df = pd.DataFrame(data, columns=[
            "Open time","Open","High","Low","Close","Volume","Close time",
            "Quote asset volume","Num trades","Taker buy base","Taker buy quote","Ignore"
        ])
        df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
        df[["Open","High","Low","Close","Volume"]] = df[["Open","High","Low","Close","Volume"]].astype(float)
        return df[["Open time","Open","High","Low","Close","Volume"]]
    except:
        return pd.DataFrame()


def fetch_fred(series_id):
    if not FRED_API_KEY:
        return pd.DataFrame()
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
        resp = requests.get(url, timeout=10)
        data = resp.json().get("observations", [])
        df = pd.DataFrame(data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df
    except:
        return pd.DataFrame()


# ------------------------------------------------
# 보고서 생성 (너 구조 그대로 유지)
# ------------------------------------------------
def generate_reports():
    today = datetime.now()
    cutoff_time = dtime(8, 0)

    if today.time() > cutoff_time:
        st.warning("보고서는 오전 8시 이전 데이터를 기준으로 생성해야 합니다.")
        return

    reports = {}

    # ======================
    # Stock Report
    # ======================
    base_stock = (
        "### Stock Report\n"
        f"작성일: {today.strftime('%Y-%m-%d %A %H:%M:%S')}\n\n"
        "1. 전일까지 주목 요인 요약\n"
        "2. 유동성 평가 (DXY, M2, 장단기 금리 등)\n"
        "3. 나스닥/코스피 상승·횡보·하락 가능성\n"
        "4. 장기/중기/단기 전략 추천\n"
    )

    stock_ai = ask_gemini(
        f"""
당신은 자본시장 분석가다.
다음 형식으로 매우 간결하고 정교한 Stock Report를 작성하라.

{base_stock}
"""
    )

    reports["Stock Report"] = stock_ai or base_stock

    # ======================
    # Crypto Report
    # ======================
    base_crypto = (
        "### Crypto Report\n"
        f"작성일: {today.strftime('%Y-%m-%d %A %H:%M:%S')}\n\n"
        "1. 전일 주요 암호화폐 뉴스/이슈\n"
        "2. 주식시장·금리·정책 상호 영향\n"
        "3. 스테이블코인 유동성 평가\n"
        "4. BTC/ETH 상승·횡보·하락 가능성\n"
        "5. 장기/중기/단기 전략\n"
    )

    crypto_ai = ask_gemini(
        f"""
당신은 암호화폐 전문 애널리스트다.
다음 형식에 따라 정교한 Crypto Report를 작성하라.

{base_crypto}
"""
    )

    reports["Crypto Report"] = crypto_ai or base_crypto

    st.session_state.reports = reports
    st.success("📄 보고서가 생성되었습니다!")


# ------------------------------------------------
# Report 메뉴
# ------------------------------------------------
if selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")

    if st.button("보고서 생성"):
        try:
            generate_reports()
        except Exception as e:
            st.error(f"보고서 생성 중 오류 발생: {str(e)}")

    if st.session_state.reports:
        report_choice = st.selectbox("생성된 보고서 선택", list(st.session_state.reports.keys()))
        st.markdown(st.session_state.reports[report_choice])
