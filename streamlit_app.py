# streamlit_app.py (Report 메뉴 부분 포함)
import streamlit as st
from datetime import datetime
import pandas as pd
import json
import os

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
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Report Helper Functions
# -------------------------
def generate_report():
    now = datetime.now()
    
    # --- Stock Report ---
    stock = {
        "market_events": "TODO: Gemini 모니터링 기반 전일 자본시장 이벤트 및 뉴스 요약",
        "liquidity": "TODO: DXY, M2, 장단기 금리, 미국채 수요/발행량 기반 유동성 평가",
        "trend_prob": {"상승":0.35, "횡보":0.45, "하락":0.2},
        "strategy": {"장기":0.5, "중기":0.3, "단기":0.2}
    }
    
    stock_md = f"""
### Stock Report
**작성일:** {now.strftime('%Y-%m-%d %A %H:%M:%S')}

**자본시장 이벤트/뉴스 요약:**  
{stock['market_events']}

**유동성 평가:**  
{stock['liquidity']}

**상승/횡보/하락 확률:**  
|상승|횡보|하락|
|---|---|---|
|{stock['trend_prob']['상승']*100:.1f}%|{stock['trend_prob']['횡보']*100:.1f}%|{stock['trend_prob']['하락']*100:.1f}%|

**장기/중기/단기 전략 확률:**  
|장기|중기|단기|
|---|---|---|
|{stock['strategy']['장기']*100:.1f}%|{stock['strategy']['중기']*100:.1f}%|{stock['strategy']['단기']*100:.1f}%|
"""

    # --- Crypto Report ---
    crypto = {
        "market_events": "TODO: Gemini 모니터링 기반 전일 암호화폐 시장 이벤트 요약",
        "major_factors": "TODO: NASDAQ, 금리, 정책 등 전일 암호화폐시장 영향 요약",
        "liquidity": "TODO: 스테이블코인 증감량, 타 거래소/지갑 입출금 등 유동성 평가",
        "trend_prob": {"상승":0.4, "횡보":0.35, "하락":0.25},
        "strategy": {"장기":0.45, "중기":0.35, "단기":0.2}
    }
    
    crypto_md = f"""
### Crypto Report
**작성일:** {now.strftime('%Y-%m-%d %A %H:%M:%S')}

**시장 이벤트 요약:**  
{crypto['market_events']}

**주요 영향 요인:**  
{crypto['major_factors']}

**유동성 평가:**  
{crypto['liquidity']}

**상승/횡보/하락 확률:**  
|상승|횡보|하락|
|---|---|---|
|{crypto['trend_prob']['상승']*100:.1f}%|{crypto['trend_prob']['횡보']*100:.1f}%|{crypto['trend_prob']['하락']*100:.1f}%|

**장기/중기/단기 전략 확률:**  
|장기|중기|단기|
|---|---|---|
|{crypto['strategy']['장기']*100:.1f}%|{crypto['strategy']['중기']*100:.1f}%|{crypto['strategy']['단기']*100:.1f}%|
"""
    return stock_md, crypto_md

# -------------------------
# Report 화면
# -------------------------
if selected_menu == "Report":
    st.subheader("Report — Automated Market & Crypto Analysis")
    if st.button("보고서 생성"):
        stock_md, crypto_md = generate_report()
        st.success("보고서 생성 완료!")
        st.markdown(stock_md)
        st.markdown(crypto_md)
