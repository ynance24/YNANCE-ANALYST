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
    "<h1 style='text-align:center; color:#333333; margin-bottom:5px;'>YNANCE ANALYST</h1>",
    unsafe_allow_html=True
)

# -------------------------------
# 상위 메뉴 (가로 버튼)
# -------------------------------
menu_cols = st.columns(len(MENU_ITEMS))
for idx, item in enumerate(MENU_ITEMS):
    is_active = st.session_state.selected_menu == item
    color = "#28a745" if is_active else "#888888"  # 선택 메뉴 초록, 나머지 회색
    if menu_cols[idx].button(item):
        st.session_state.selected_menu = item
        st.experimental_rerun()  # 클릭 즉시 화면 갱신
    # 텍스트만 표시 (체크 표시 제거)
    menu_cols[idx].markdown(
        f"<div style='text-align:center; color:{color}; font-weight:bold; font-size:18px;'>{item}</div>",
        unsafe_allow_html=True
    )

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
MENU_FUNCTIONS[st.session_state.selected_menu]()
