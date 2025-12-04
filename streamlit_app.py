import streamlit as st
import json

# -------------------------------
# 페이지 기본 설정
# -------------------------------
st.set_page_config(
    page_title="Ynance Analyst",
    layout="wide"
)

# -------------------------------
# 세션 상태 초기화
# -------------------------------
if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "Home"

# -------------------------------
# 메뉴 정의
# -------------------------------
MENU_ITEMS = ["Home", "Markets", "Trading", "Talk", "Report", "Assets"]

# -------------------------------
# secrets.json 로드
# -------------------------------
try:
    with open("secrets.json") as f:
        secrets = json.load(f)
    secrets_loaded = True
except Exception as e:
    secrets_loaded = False
    secrets_error = e

# -------------------------------
# 상단 타이틀
# -------------------------------
st.markdown(
    """
    <h1 style='text-align:center; color:#333333; margin-bottom: 5px;'>YNANCE ANALYST</h1>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# 상위 메뉴 (텍스트 버튼 스타일)
# -------------------------------
menu_html = ""
for item in MENU_ITEMS:
    color = "#28a745" if st.session_state.selected_menu == item else "#888888"
    menu_html += f"""
        <span style='margin-right:20px; cursor:pointer; color:{color}; font-weight:bold;' 
              onclick="window.streamlit.setComponentValue('{item}')">{item}</span>
    """
st.markdown(
    f"<div style='text-align:left; margin-left:50px;'>{menu_html}</div>",
    unsafe_allow_html=True
)

# -------------------------------
# Streamlit 버튼 대체용 JS 이벤트 감지
# -------------------------------
# st.button 대신 click 시 session_state 변경
# Streamlit 자체에서는 JS click 이벤트를 직접 처리 불가 → 대신 각 메뉴별 버튼 생성
cols = st.columns(len(MENU_ITEMS))
for idx, item in enumerate(MENU_ITEMS):
    if cols[idx].button(item):
        st.session_state.selected_menu = item

# -------------------------------
# 화면 내용 출력 함수
# -------------------------------
def show_home():
    st.subheader("Home")
    if secrets_loaded:
        st.success("secrets.json loaded successfully!")
        st.write("Loaded Keys:", list(secrets.keys()))
    else:
        st.error("Failed to load secrets.json")
        st.write(secrets_error)
    st.write("App is running.")

def show_markets():
    st.subheader("Markets")
    st.write("시장 데이터 관련 내용 표시")

def show_trading():
    st.subheader("Trading")
    st.write("거래 관련 UI 표시")

def show_assets():
    st.subheader("Assets")
    st.write("자산 관리 관련 UI 표시")

def show_talk():
    st.subheader("Talk")
    st.write("Talk 관련 화면 표시")

def show_report():
    st.subheader("Report")
    st.write("리포트 및 통계 화면 표시")

# -------------------------------
# 메뉴별 함수 매핑
# -------------------------------
MENU_FUNCTIONS = {
    "Home": show_home,
    "Markets": show_markets,
    "Trading": show_trading,
    "Assets": show_assets,
    "Talk": show_talk,
    "Report": show_report,
}

# -------------------------------
# 선택 메뉴 화면 출력
# -------------------------------
selected_func = MENU_FUNCTIONS.get(st.session_state.selected_menu, show_home)
selected_func()
