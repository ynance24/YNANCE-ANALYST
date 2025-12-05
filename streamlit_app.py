import streamlit as st
import json
import os
from datetime import datetime
import requests

# ===============================
# secrets.json 자동 로드
# ===============================
SECRETS_PATH = "/mount/src/ynance-analyst/secrets.json"
if os.path.exists("secrets.json"):
    with open("secrets.json") as f:
        secrets = json.load(f)
elif os.path.exists(SECRETS_PATH):
    with open(SECRETS_PATH) as f:
        secrets = json.load(f)
else:
    secrets = {}

FRED_KEY = secrets.get("FRED_API_KEY")
ALPHA_KEY = secrets.get("ALPHA_VANTAGE_API_KEY")
COINGECKO_KEY = secrets.get("COINGECKO_API_KEY")
BINANCE_KEY = secrets.get("BINANCE_API_KEY")
KOSIS_KEY = secrets.get("KOSIS_API_KEY")
GEMINI_KEY = secrets.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5flash"

# ===============================
# Gemini 호출 함수
# ===============================
import google.generativeai as genai
genai.configure(api_key=GEMINI_KEY)

def ask_gemini(prompt):
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text if response else "내용 없음"


# ===============================
# 시장데이터 불러오기
# (전일 종가 기준 완성된 차트 데이터)
# ===============================

def get_alpha_daily(symbol):
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


def get_binance_close(symbol="BTCUSDT"):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": 2}
    r = requests.get(url)
    data = r.json()
    if isinstance(data, list) and len(data) > 0:
        return float(data[-1][4])
    return None


# ===============================
# 보고서 생성 함수
# ===============================

def generate_stock_report(date_str, nasdaq_close, kospi_close):
    prompt = f"""
당신은 20년 경력의 자본시장 분석가다.

다음 형식의 'Stock Report'를 작성하라.

1. 헤드라인 = Stock Report
2. 전일 자본시장 핵심요인 요약 (금리, 정책, 뉴스 등)
3. 유동성 평가 (DXY, M2, 장단기금리, 미국채수요/발행량 등)
4. 나스닥/코스피 상승·횡보·하락 확률 분석
5. 장기/중기/단기 전략 확률 제시
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
2. 암호화폐 시장 핵심 이슈 요약
3. 나스닥/금리/정책 등 암호화폐 시장 영향요약
4. 유동성 평가 (스테이블코인, 대규모 입출금 등)
5. BTC/ETH 상승·횡보·하락 확률 분석
6. 장기/중기/단기 (Spot/Futures) 전략 확률 제시

데이터:
- 날짜: {date_str}
- BTC 전일 종가: {btc_close}
- ETH 전일 종가: {eth_close}
"""
    return ask_gemini(prompt)


# ===============================
# 파일로 저장
# ===============================
def save_report(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


# ===============================
# Streamlit UI
# ===============================

st.set_page_config(page_title="Ynance Report", layout="wide")
st.title("📊 Report — Automated Market & Crypto Analysis")

st.write("---")

# 보고서 생성 버튼
if st.button("📄 보고서 생성"):

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    # 데이터 로딩
    nasdaq = get_alpha_daily("NDX") or "N/A"
    kospi = get_alpha_daily("KS11") or "N/A"
    btc = get_binance_close("BTCUSDT") or "N/A"
    eth = get_binance_close("ETHUSDT") or "N/A"

    # Gemini 보고서 생성
    stock_report = generate_stock_report(date_str, nasdaq, kospi)
    crypto_report = generate_crypto_report(date_str, btc, eth)

    # 파일 저장
    stock_filename = f"Stock_Report_{date_str}.md"
    crypto_filename = f"Crypto_Report_{date_str}.md"

    save_report(stock_filename, stock_report)
    save_report(crypto_filename, crypto_report)

    st.success("보고서가 생성되었습니다.")

    # 다운로드 버튼
    with open(stock_filename, "rb") as f:
        st.download_button("📥 Stock Report 다운로드", f, file_name=stock_filename)

    with open(crypto_filename, "rb") as f:
        st.download_button("📥 Crypto Report 다운로드", f, file_name=crypto_filename)

    # 펼치기 UI 추가
    with st.expander("📄 생성된 보고서 본문 보기"):
        st.subheader("Stock Report")
        st.markdown(stock_report)

        st.subheader("Crypto Report")
        st.markdown(crypto_report)
