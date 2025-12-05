import streamlit as st
import json
import os
from datetime import datetime
import requests

# =========================================
# ✔ 안전한 secrets 로딩 (Streamlit Cloud 호환)
# =========================================
def load_secrets():
    # 1) Streamlit Cloud secrets 우선
    if "GEMINI_API_KEY" in st.secrets:
        return {
            "FRED_API_KEY": st.secrets.get("FRED_API_KEY", ""),
            "ALPHA_VANTAGE_API_KEY": st.secrets.get("ALPHA_VANTAGE_API_KEY", ""),
            "COINGECKO_API_KEY": st.secrets.get("COINGECKO_API_KEY", ""),
            "BINANCE_API_KEY": st.secrets.get("BINANCE_API_KEY", ""),
            "KOSIS_API_KEY": st.secrets.get("KOSIS_API_KEY", ""),
            "GEMINI_API_KEY": st.secrets.get("GEMINI_API_KEY", ""),
        }

    # 2) Local secrets.json
    paths = ["secrets.json", "/mount/src/ynance-analyst/secrets.json"]
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)

    # 3) no file
    return {}

secrets = load_secrets()

FRED_KEY = secrets.get("FRED_API_KEY", "")
ALPHA_KEY = secrets.get("ALPHA_VANTAGE_API_KEY", "")
COINGECKO_KEY = secrets.get("COINGECKO_API_KEY", "")
BINANCE_KEY = secrets.get("BINANCE_API_KEY", "")
KOSIS_KEY = secrets.get("KOSIS_API_KEY", "")
GEMINI_KEY = secrets.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

# =========================================
# ✔ Gemini
# =========================================
import google.generativeai as genai
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text if response else "내용 없음"
    except Exception as e:
        return f"[Gemini 오류] {str(e)}"


# =========================================
# ✔ 시장데이터 수집
# =========================================
def get_alpha_daily(symbol):
    try:
        url = (
            f"https://www.alphavantage.co/query?"
            f"function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_KEY}"
        )
        r = requests.get(url)
        data = r.json()
        series = data.get("Time Series (Daily)")
        if not series:
            return None
        sorted_keys = sorted(series.keys(), reverse=True)
        latest = sorted_keys[0]
        close = float(series[latest]["4. close"])
        return close
    except:
        return None


def get_binance_close(symbol="BTCUSDT"):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "limit": 2}
        r = requests.get(url)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[-1][4])
    except:
        pass
    return None


# =========================================
# ✔ 보고서 생성
# =========================================
def generate_stock_report(date_str, nasdaq_close, kospi_close):
    prompt = f"""
당신은 20년 경력의 자본시장 분석가다.

다음 형식의 'Stock Report'를 작성하라.

1. 헤드라인 = Stock Report
2. 전일 자본시장 핵심요인 요약
3. 유동성 평가 (DXY, M2, 장단기금리)
4. 나스닥/코스피 상승·횡보·하락 확률 분석
5. 장기/중기/단기 전략 제시

데이터:
- 날짜: {date_str}
- NASDAQ 전일 종가: {nasdaq_close}
- KOSPI 전일 종가: {kospi_close}
"""
    return ask_gemini(prompt)


def generate_crypto_report(date_str, btc_close, eth_close):
    prompt = f"""
당신은 20년 경력의 암호화폐 시장 분석가다.

다음 형식의 'Crypto Report'를 작성하라.

1. 헤드라인 = Crypto Report
2. 암호화폐 시장 핵심 이슈
3. 나스닥/금리/정책과의 연동 분석
4. 유동성 분석 (스테이블코인 흐름 등)
5. BTC/ETH 상승·횡보·하락 확률 분석
6. 장기/중기/단기 전략 제시

데이터:
- 날짜: {date_str}
- BTC 종가: {btc_close}
- ETH 종가: {eth_close}
"""
    return ask_gemini(prompt)


# =========================================
# ✔ 파일 저장
# =========================================
def save_report(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


# =========================================
# ✔ UI 시작
# =========================================
st.set_page_config(page_title="Ynance Analyst", layout="wide")

st.sidebar.title("📌 Menu")
menu = st.sidebar.radio(
    "탭 선택",
    ["Home", "Report", "Status"]
)

# ============================
# HOME
# ============================
if menu == "Home":
    st.title("🏠 Home")
    st.write("전체 메뉴 정상 복구됨.")

# ============================
# STATUS
# ============================
elif menu == "Status":
    st.title("🔧 Status Check")
    st.json({
        "Gemini Key 감지": bool(GEMINI_KEY),
        "AlphaVantage Key 감지": bool(ALPHA_KEY),
        "Binance API Key 감지": bool(BINANCE_KEY)
    })

# ============================
# REPORT
# ============================
elif menu == "Report":

    st.title("📊 Report — Automated Market & Crypto Analysis")
    st.write("---")

    if st.button("📄 보고서 생성"):

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        nasdaq = get_alpha_daily("NDX") or "N/A"
        kospi = get_alpha_daily("KS11") or "N/A"
        btc = get_binance_close("BTCUSDT") or "N/A"
        eth = get_binance_close("ETHUSDT") or "N/A"

        stock_report = generate_stock_report(date_str, nasdaq, kospi)
        crypto_report = generate_crypto_report(date_str, btc, eth)

        stock_filename = f"Stock_Report_{date_str}.md"
        crypto_filename = f"Crypto_Report_{date_str}.md"

        save_report(stock_filename, stock_report)
        save_report(crypto_filename, crypto_report)

        st.success("보고서가 생성되었습니다.")

        with open(stock_filename, "rb") as f:
            st.download_button("📥 Stock Report 다운로드", f, file_name=stock_filename)

        with open(crypto_filename, "rb") as f:
            st.download_button("📥 Crypto Report 다운로드", f, file_name=crypto_filename)

        with st.expander("📄 생성된 보고서 본문 보기"):
            st.subheader("Stock Report")
            st.markdown(stock_report)

            st.subheader("Crypto Report")
            st.markdown(crypto_report)
