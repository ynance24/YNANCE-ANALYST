# -------------------------
# Home 화면 (업그레이드)
# -------------------------
if selected_menu == "Home":
    st.subheader("Home — Market Overview & Indicators")
    
    # 상단 영역: NASDAQ / KOSPI / BTC
    col1, col2, col3 = st.columns(3)

    # NASDAQ
    with col1:
        nasdaq = fetch_alpha_vantage("^IXIC")
        if not nasdaq.empty:
            df = nasdaq.copy().sort_index()
            df['MA20'] = df['4. close'].rolling(20).mean()
            df['EMA20'] = df['4. close'].ewm(span=20, adjust=False).mean()
            delta = df['4. close'].diff()
            up, down = delta.clip(lower=0), -delta.clip(upper=0)
            RS = up.rolling(14).mean() / down.rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + RS))
            df['MACD'] = df['4. close'].ewm(span=12, adjust=False).mean() - df['4. close'].ewm(span=26, adjust=False).mean()
            st.line_chart(df[['4. close','MA20','EMA20']])
            st.metric("NASDAQ 변동률", f"{df['4. close'].pct_change().iloc[-1]*100:.2f}%")
        else:
            st.warning("NASDAQ 데이터 로딩 실패")
    
    # KOSPI
    with col2:
        kospi = fetch_alpha_vantage("^KS11")
        if not kospi.empty:
            df = kospi.copy().sort_index()
            df['MA20'] = df['4. close'].rolling(20).mean()
            df['EMA20'] = df['4. close'].ewm(span=20, adjust=False).mean()
            delta = df['4. close'].diff()
            up, down = delta.clip(lower=0), -delta.clip(upper=0)
            RS = up.rolling(14).mean() / down.rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + RS))
            df['MACD'] = df['4. close'].ewm(span=12, adjust=False).mean() - df['4. close'].ewm(span=26, adjust=False).mean()
            st.line_chart(df[['4. close','MA20','EMA20']])
            st.metric("KOSPI 변동률", f"{df['4. close'].pct_change().iloc[-1]*100:.2f}%")
        else:
            st.warning("KOSPI 데이터 로딩 실패")
    
    # BTC
    with col3:
        btc = fetch_binance("BTCUSDT")
        if not btc.empty:
            df = btc.copy().sort_values("Open time")
            df['MA20'] = df['Close'].rolling(20).mean()
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            delta = df['Close'].diff()
            up, down = delta.clip(lower=0), -delta.clip(upper=0)
            RS = up.rolling(14).mean() / down.rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + RS))
            df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
            st.line_chart(df[['Close','MA20','EMA20']])
            st.metric("BTC 변동률", f"{df['Close'].pct_change().iloc[-1]*100:.2f}%")
        else:
            st.warning("BTC 데이터 로딩 실패")
    
    # Fear & Greed Index
    col4, col5 = st.columns(2)
    fng_stock = fetch_fng_stock()
    fng_crypto = fetch_fng_crypto()
    with col4:
        st.metric("Stock F&G", f"{fng_stock['value']}", f"{fng_stock['classification']}")
    with col5:
        st.metric("Crypto F&G", f"{fng_crypto['value']}", f"{fng_crypto['classification']}")
    
    # FRED 주요 지표
    st.markdown("### FRED 주요 경제지표")
    fred_series = {
        "DXY": "DTWEXBGS",
        "M2": "M2SL",
        "US Base Money": "BOGMBASE",
        "10Y Treasury Rate": "DGS10",
        "2Y Treasury Rate": "DGS2"
    }
    for name, series in fred_series.items():
        df = fetch_fred(series)
        if not df.empty:
            st.line_chart(df.set_index("date")["value"])
            st.write(name)
        else:
            st.warning(f"{name} 데이터 로딩 실패")
    
    st.caption("전일 종가/주봉 기준 데이터, 기술적지표 포함 (MA/EMA/RSI/MACD)")
