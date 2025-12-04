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
# 메뉴 (가로 정렬 + 클릭 시 즉시 전환 + 선택 메뉴 색상 변경)
# -------------------------------
selected_menu = st.radio(
    "",
    MENU_ITEMS,
    index=MENU_ITEMS.index(st.session_state.selected_menu),
    horizontal=True
)
st.session_state.selected_menu = selected_menu

# CSS로 선택 메뉴 색상 변경
st.markdown(
    """
    <style>
    div[role="radiogroup"] > label > div {
        display: inline-block;
        margin-right: 25px;
        font-weight: bold;
        font-size: 18px;
        color: #888888;
    }
    div[role="radiogroup"] > label[aria-checked="true"] > div {
        color: #006400 !important;  /* 선택 메뉴 어두운 녹색 */
    }
    </style>
    """,
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
