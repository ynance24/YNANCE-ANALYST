# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

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
# 기존 메뉴들은 그대로 유지 (예: Home 등)
# -------------------------
if selected_menu == "Home":
    st.subheader("Home — Market Overview & Indicators")
    st.write("기존 Home 메뉴 기능 그대로")

elif selected_menu == "Markets":
    st.subheader("Markets")
    st.write("기존 Markets 메뉴 기능 그대로")

elif selected_menu == "Trading":
    st.subheader("Trading")
    st.write("기존 Trading 메뉴 기능 그대로")

elif selected_menu == "Talk":
    st.subheader("Talk")
    st.write("기존 Talk 메뉴 기능 그대로")

elif selected_menu == "Assets":
    st.subheader("Assets")
    st.write("기존 Assets 메뉴 기능 그대로")

# -------------------------
# Report 메뉴만 구현
# -------------------------
elif selected_menu == "Report":
    st.subheader("Report — Market & Crypto Analysis")

    # 날짜/요일/시간 표시
    now = datetime.now()
    st.markdown(f"**작성일:** {now.strftime('%Y-%m-%d %A %H:%M:%S')}")

    # 섹션 구분
    st.markdown("### 1. 전일까지의 자본시장 이슈")
    st.write("GEMINI 모니터링 기반 자본시장 뉴스, 이벤트 요약")

    st.markdown("### 2. 전일까지의 이벤트")
    st.write("경제지표 발표, 기업 실적, 정책 이벤트 등 요약")

    st.markdown("### 3. 전일까지 나스닥/비트코인 상황")
    st.write("NASDAQ 및 BTC 전일 종가, 변동성, 주요 뉴스 기반 요약")

    st.markdown("### 4. 종합 분석/예측")
    st.write("Stock 시장과 Crypto 시장을 다방면 변수와 이슈를 종합해 분석/예측 보고서 작성")
    st.write("- Stock 시장 분석/예측")
    st.write("- Crypto 시장 분석/예측")

    st.caption("※ 데이터는 GEMINI 모니터링 기반으로 참고하며, 시각화/URL은 제공하지 않습니다.")
