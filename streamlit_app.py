import streamlit as st
import pandas as pd
import json
import threading
import websocket
from datetime import datetime
import requests
import os

-------------------------

Config

-------------------------

st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

secrets.json 불러오기

SECRETS_PATH = "./secrets.json"
BINANCE_API_KEY = BINANCE_API_SECRET_KEY = GEMINI_API_KEY = None
if os.path.exists(SECRETS_PATH):
with open(SECRETS_PATH, "r") as f:
secrets = json.load(f)
BINANCE_API_KEY = secrets.get("BINANCE_API_KEY")
BINANCE_API_SECRET_KEY = secrets.get("BINANCE_API_SECRET_KEY")
GEMINI_API_KEY = secrets.get("GEMINI_API_KEY")

-------------------------

CSS

-------------------------

st.markdown("""

<style>  
body {background-color: #f5f5f5;}  
</style>  """, unsafe_allow_html=True)
st.markdown("# YNANCE ANALYST", unsafe_allow_html=True)

-------------------------

Session State 초기화

-------------------------

if "spot_df" not in st.session_state: st.session_state.spot_df = pd.DataFrame()
if "fut_df" not in st.session_state: st.session_state.fut_df = pd.DataFrame()
if "klines" not in st.session_state: st.session_state.klines = pd.DataFrame()
if "threads" not in st.session_state: st.session_state.threads = {}
if "depth_symbol" not in st.session_state: st.session_state.depth_symbol = None
if "fund_rate" not in st.session_state: st.session_state.fund_rate = 0
if "symbol_list" not in st.session_state: st.session_state.symbol_list = []
if "gemini_data" not in st.session_state: st.session_state.gemini_data = pd.DataFrame()

-------------------------

메뉴

-------------------------

menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

-------------------------

Helper Functions

-------------------------

def parse_ticker(msg):
try:
data = json.loads(msg)
if isinstance(data, dict) and data.get("e") == "24hrTicker":
data = [data]
rows = []
for x in data:
rows.append({
"symbol": x.get("s"),
"last": float(x.get("c") or 0),
"volume": float(x.get("v") or 0),
"change": float(x.get("p") or 0),
"pct": float(x.get("P") or 0)
})
return pd.DataFrame(rows)
except Exception:
return pd.DataFrame()

def run_ws(ws_url, on_message):
ws = websocket.WebSocketApp(ws_url, on_message=on_message)
ws.run_forever()

def fetch_gemini_data():
if not GEMINI_API_KEY:
st.warning("GEMINI_API_KEY 없음")
return pd.DataFrame()
try:
headers = {"X-GEMINI-APIKEY": GEMINI_API_KEY}
resp = requests.get("https://api.gemini.com/v1/pubticker/btcusd", headers=headers)
if resp.ok:
data = resp.json()
df = pd.DataFrame([{
"bid": float(data.get("bid",0)),
"ask": float(data.get("ask",0)),
"last": float(data.get("last",0)),
"volume": float(data.get("volume", {}).get("BTC",0))
}])
st.session_state.gemini_data = df
return df
else:
st.error("GEMINI 데이터 로딩 실패")
return pd.DataFrame()
except Exception as e:
st.error(f"GEMINI API 오류: {e}")
return pd.DataFrame()

-------------------------

메뉴별 화면 출력

-------------------------

if selected_menu == "Home":
st.subheader("Home — Fear & Greed Index")
fng_ph = st.empty()
try:
resp = requests.get("https://api.alternative.me/fng/?limit=1")
if resp.ok:
data = resp.json().get("data", [{}])[0]
value = int(data.get("value", 0))
classification = data.get("value_classification", "Unknown")
fng_ph.metric("Fear & Greed Index", f"{value}", classification)
except:
fng_ph.info("Fear & Greed Index 로딩 실패")

elif selected_menu == "Markets":
st.subheader("Markets — Stock / Crypto")
left, right = st.columns([1,3])
with left:
market_cat = st.radio("Category", ["Stock", "Crypto"], index=1)
if market_cat == "Crypto":
market_type = st.radio("Market", ["Spot", "Futures"], index=0)
search = st.text_input("Search symbol", value="")
rows = st.number_input("Rows to show", min_value=10, max_value=500, value=200, step=10)
placeholder = st.empty()
df = pd.DataFrame()  # 초기화

# 실제 WebSocket 스레드 실행은 생략하거나 안전하게 처리  
placeholder.info("WebSocket 데이터 로딩 시도 (배포용 기본 표시)")

elif selected_menu == "Trading":
st.subheader("Trading — 실시간 차트 & Depth/Funding")
st.info("Trading 화면 WebSocket 스레드는 배포용 생략")

elif selected_menu in ["Talk","Report"]:
st.subheader(selected_menu)
df = fetch_gemini_data()
if not df.empty:
st.dataframe(df)
else:
st.info("GEMINI 데이터 없음 / API Key 확인 필요")

elif selected_menu == "Assets":
st.subheader("Assets — 자리 (REST 추후 추가)")
st.info("현재 읽기 전용")

위 코드를 WebSocket 까지 동작하는 완전 배포용 streamlit_app.py 를 에러없이 돌고 GEMINI_API_KEY 를 secrets.json 에서 자동으로 불러와 기제되게 업그레이드해
