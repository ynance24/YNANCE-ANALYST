# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import threading
import websocket
import requests
import os

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="YNANCE ANALYST", layout="wide")

# -------------------------
# secrets.json 불러오기
# -------------------------
SECRETS_PATH = "./secrets.json"
BINANCE_API_KEY = None
BINANCE_API_SECRET_KEY = None
GEMINI_API_KEY = None
if os.path.exists(SECRETS_PATH):
    try:
        with open(SECRETS_PATH, "r") as f:
            secrets = json.load(f)
            BINANCE_API_KEY = secrets.get("BINANCE_API_KEY")
            BINANCE_API_SECRET_KEY = secrets.get("BINANCE_API_SECRET_KEY")
            GEMINI_API_KEY = secrets.get("GEMINI_API_KEY")
    except Exception as e:
        st.error(f"secrets.json 로딩 오류: {e}")

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
body {background-color: #f5f5f5;}
</style>
""", unsafe_allow_html=True)
st.markdown("# YNANCE ANALYST", unsafe_allow_html=True)

# -------------------------
# Session State 초기화
# -------------------------
for key, default in [("spot_df", pd.DataFrame()), ("fut_df", pd.DataFrame()), ("klines", pd.DataFrame()),
                     ("threads", {}), ("depth_symbol", None), ("fund_rate", 0), ("symbol_list", []),
                     ("gemini_data", pd.DataFrame())]:
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------
# 메뉴
# -------------------------
menus = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]
selected_menu = st.radio("", menus, index=0, horizontal=True)

# -------------------------
# Helper Functions
# -------------------------
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
    except:
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

# -------------------------
# Home
# -------------------------
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

# -------------------------
# Markets
# -------------------------
elif selected_menu == "Markets":
    st.subheader("Markets — Stock / Crypto")
    left, right = st.columns([1,3])
    with left:
        market_cat = st.radio("Category", ["Stock", "Crypto"], index=1, horizontal=False)
        market_type = "Spot"
        if market_cat == "Crypto":
            market_type = st.radio("Market", ["Spot", "Futures"], index=0, horizontal=False)
        search = st.text_input("Search symbol", value="")
        rows = st.number_input("Rows to show", min_value=10, max_value=500, value=200, step=10)
    placeholder = st.empty()
    SPOT_WS = "wss://stream.binance.com/ws/!ticker@arr"
    FUT_WS  = "wss://fstream.binance.com/ws/!ticker@arr"
    def spot_on_message(ws, msg):
        df = parse_ticker(msg)
        if not df.empty:
            st.session_state.spot_df = df.sort_values("volume", ascending=False).reset_index(drop=True)
            st.session_state.symbol_list = df["symbol"].tolist()
    def fut_on_message(ws, msg):
        df = parse_ticker(msg)
        if not df.empty:
            st.session_state.fut_df = df.sort_values("volume", ascending=False).reset_index(drop=True)
            st.session_state.symbol_list = df["symbol"].tolist()
    if market_type=="Spot":
        if "spot_thread" not in st.session_state.threads:
            t = threading.Thread(target=run_ws, args=(SPOT_WS, spot_on_message), daemon=True)
            t.start()
            st.session_state.threads["spot_thread"] = t
        df = st.session_state.spot_df
    else:
        if "fut_thread" not in st.session_state.threads:
            t = threading.Thread(target=run_ws, args=(FUT_WS, fut_on_message), daemon=True)
            t.start()
            st.session_state.threads["fut_thread"] = t
        df = st.session_state.fut_df
    if search: df = df[df["symbol"].str.contains(search.upper())]
    if df.empty:
        placeholder.info("WebSocket으로 마켓 데이터 로딩 중... 잠시만요.")
    else:
        placeholder.dataframe(df.head(rows), use_container_width=True)

# -------------------------
# Trading
# -------------------------
elif selected_menu == "Trading":
    st.subheader("Trading — 실시간 차트 & Depth/Funding")
    left, right = st.columns([3,1])
    with right:
        symbol = st.selectbox("Symbol", options=st.session_state.symbol_list or ["BTCUSDT"]).strip().upper()
        interval = st.selectbox("Kline interval", ["1m","3m","5m","15m","1h"], index=0)
        depth_limit = st.selectbox("Depth limit", [5,10,20,50,100], index=2)
    view = st.radio("View", ["Chart", "Depth/Funding"], index=0, horizontal=True)
    chart_ph, depth_ph, fund_ph = st.empty(), st.empty(), st.empty()
    KLINE_WS = f"wss://fstream.binance.com/ws/{symbol.lower()}@kline_{interval}"
    DEPTH_WS = f"wss://fstream.binance.com/ws/{symbol.lower()}@depth20@100ms"
    FUND_WS  = f"wss://fstream.binance.com/ws/{symbol.lower()}@markPrice@1s"
    def kline_on_message(ws, msg):
        try:
            data = json.loads(msg).get("k", {})
            if not data: return
            candle = {k: float(data[k]) if k != "t" else int(data[k]) for k in ["t","o","h","l","c","v"]}
            df = st.session_state.klines
            if df.empty or candle["t"] > df["t"].max():
                df = pd.concat([df, pd.DataFrame([candle])], ignore_index=True)
            else:
                df.iloc[-1] = pd.Series(candle)
            st.session_state.klines = df.tail(500).reset_index(drop=True)
            if view=="Chart" and not df.empty:
                d = df.copy()
                d.index = pd.to_datetime(d["t"], unit="ms")
                chart_ph.line_chart(d["c"])
        except: pass
    def depth_on_message(ws, msg):
        try:
            data = json.loads(msg)
            bids = pd.DataFrame(data.get("b", []), columns=["price","qty"]).astype(float) if data.get("b") else pd.DataFrame(columns=["price","qty"])
            asks = pd.DataFrame(data.get("a", []), columns=["price","qty"]).astype(float) if data.get("a") else pd.DataFrame(columns=["price","qty"])
            bids["cum"], asks["cum"] = bids["qty"].cumsum(), asks["qty"].cumsum()
            left, right = bids.head(depth_limit).reset_index(drop=True), asks.head(depth_limit).reset_index(drop=True)
            combined = pd.concat([left, right], axis=1, keys=["Bids","Asks"])
            if view=="Depth/Funding": depth_ph.table(combined)
        except: pass
    def fund_on_message(ws, msg):
        try:
            data = json.loads(msg)
            rate = float(data.get("r",0))
            st.session_state.fund_rate = rate
            if view=="Depth/Funding": fund_ph.metric(label="Funding Rate", value=f"{rate*100:.4f}%")
        except: pass
    if st.session_state.depth_symbol != symbol:
        st.session_state.depth_symbol = symbol
        for key, url, func in [("kline_thread", KLINE_WS, kline_on_message),
                               ("depth_thread", DEPTH_WS, depth_on_message),
                               ("fund_thread", FUND_WS, fund_on_message)]:
            t = threading.Thread(target=run_ws, args=(url, func), daemon=True)
            t.start()
            st.session_state.threads[key] = t

# -------------------------
# Talk / Report
# -------------------------
elif selected_menu in ["Talk","Report"]:
    st.subheader(selected_menu)
    st.write("GEMINI API 데이터 연동")
    df = fetch_gemini_data()
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("GEMINI 데이터 없음 / API Key 확인 필요")

# -------------------------
# Assets
# -------------------------
elif selected_menu == "Assets":
    st.subheader("Assets — 자리 (REST 추후 추가하지 않음)")
    st.info("이 탭은 현재 읽기전용 자리입니다. REST/키 체크 절대 없음.")
    st.write("- 계좌 잔고: (미구현, REST 없음)")
    st.write("- 포지션: (미구현, REST 없음)")

st.write("---")
st.caption("WebSocket 전용 운영 — Markets/Trading 모두 REST 호출 없음")
