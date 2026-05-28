import streamlit.components.v1 as components
import streamlit as st
import time
from datetime import datetime
import traceback
import pandas as pd
import numpy as np
import base64
import os
import io
import uuid
import textwrap

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="용인시 건축 조례 지원 플랫폼",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 외부 모듈
from widget_utils import inject_floating_button
from docx import Document
from processor import handle_ai_analysis, generate_civil_document
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history

# 플로팅 버튼
inject_floating_button()

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history(st.session_state.user_id)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

if "qna_list" not in st.session_state:
    st.session_state.qna_list = []


def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle


apply_custom_style(st.session_state.dark_mode)

# ==========================================
# 3. 프리미엄 UI 시스템
# ==========================================
def apply_premium_ui_v3(is_dark):

    base_css = """
<style>

@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, .stApp {
    font-family: 'Pretendard', sans-serif !important;
}

/* 전체 앱 */
[data-testid="stAppViewContainer"] {
    padding-top: 0.5rem;
}

/* 기본 텍스트 가독성 */
p, span, div, label {
    letter-spacing: -0.01em;
}

/* 헤더 */
.main-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
}

.main-caption {
    font-size: 14px;
    opacity: 0.85;
    margin-bottom: 18px;
}

/* 카드 */
.custom-card {
    border-radius: 16px;
    padding: 18px;
    border: 1px solid rgba(120,120,120,0.16);
    margin-bottom: 14px;
}

/* 탭 */
button[data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 10px 18px !important;
    font-weight: 600 !important;
    border: 1px solid transparent !important;
}

/* 사이드바 버튼 */
.stSidebar button {
    border-radius: 12px !important;
    height: 46px !important;
    font-weight: 600 !important;
    border: 1px solid rgba(120,120,120,0.16) !important;
}

/* 일반 버튼 */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    height: 44px !important;
    transition: all 0.18s ease !important;
}

/* 입력 */
.stTextInput input,
.stTextArea textarea,
.stChatInput textarea,
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 14px !important;
    border-width: 1.5px !important;
    font-size: 15px !important;
}

/* 입력 포커스 */
.stTextInput input:focus,
.stTextArea textarea:focus,
.stChatInput textarea:focus {
    outline: none !important;
}

/* Expander */
div[data-testid="stExpander"] {
    border-radius: 14px !important;
    overflow: hidden !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(120,120,120,0.14) !important;
}

/* 대화 히스토리 버튼 */
.history-btn button {
    height: 52px !important;
}

/* 토스트 */
[data-testid="stToast"] {
    border-radius: 14px !important;
}

/* 경계선 */
hr {
    margin-top: 1rem !important;
    margin-bottom: 1rem !important;
}

/* 다이얼로그 */
[data-testid="stDialog"] * {
    color: inherit !important;
}

/* placeholder */
::placeholder {
    opacity: 0.72 !important;
}

/* markdown container */
div[data-testid="stMarkdownContainer"] p {
    line-height: 1.7 !important;
}

/* 메트릭 */
[data-testid="stMetric"] {
    border-radius: 14px;
    padding: 12px;
}

/* info/warning box */
[data-testid="stAlert"] {
    border-radius: 14px !important;
}

</style>
"""

    if is_dark:
        theme_css = """
<style>

[data-testid="stAppViewContainer"] {
    background: #15171a !important;
    color: #f3f4f6 !important;
}

[data-testid="stSidebar"] {
    background: #111317 !important;
    border-right: 1px solid #252932 !important;
}

h1,h2,h3,h4,h5,h6,p,span,label,div {
    color: #f3f4f6 !important;
}

small {
    color: #c7ccd4 !important;
}

.stCaption {
    color: #c7ccd4 !important;
}

.stTextInput input,
.stTextArea textarea,
.stChatInput textarea,
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background: #1d2128 !important;
    color: #ffffff !important;
    border: 1.5px solid #3a4250 !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stChatInput textarea:focus,
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border-color: #5d8dff !important;
    box-shadow: 0 0 0 3px rgba(93,141,255,0.18) !important;
}

.stButton > button,
.stSidebar button {
    background: #1f2430 !important;
    color: #ffffff !important;
}

.stButton > button:hover,
.stSidebar button:hover {
    border-color: #5d8dff !important;
    background: #273142 !important;
}

button[data-baseweb="tab"] {
    background: #1c2129 !important;
    color: #f5f5f5 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #2b3952 !important;
    border-color: #5d8dff !important;
}

div[data-testid="stExpander"] {
    background: #1b1f26 !important;
    border: 1px solid #2f3744 !important;
}

div[data-testid="stExpander"] summary {
    background: #1f2430 !important;
}

.custom-card {
    background: #1b1f26;
}

</style>
"""
    else:
        theme_css = """
<style>

[data-testid="stAppViewContainer"] {
    background: #f5f7fb !important;
    color: #111827 !important;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #dbe2ea !important;
}

h1,h2,h3,h4,h5,h6,p,span,label,div {
    color: #111827 !important;
}

small {
    color: #475569 !important;
}

.stCaption {
    color: #475569 !important;
}

.stTextInput input,
.stTextArea textarea,
.stChatInput textarea,
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1.5px solid #cbd5e1 !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stChatInput textarea:focus,
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}

.stButton > button,
.stSidebar button {
    background: #ffffff !important;
    color: #111827 !important;
}

.stButton > button:hover,
.stSidebar button:hover {
    border-color: #2563eb !important;
    background: #f8fbff !important;
}

button[data-baseweb="tab"] {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #dbe2ea !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #edf4ff !important;
    border-color: #2563eb !important;
}

div[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #dbe2ea !important;
}

div[data-testid="stExpander"] summary {
    background: #f8fafc !important;
}

.custom-card {
    background: #ffffff;
}

</style>
"""

    st.markdown(base_css + theme_css, unsafe_allow_html=True)


apply_premium_ui_v3(st.session_state.dark_mode)

# ==========================================
# 4. 대화 검색 다이얼로그
# ==========================================
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog


@dialog_decorator("대화 기록 검색", width="large")
def open_history_search_dialog():

    search_query = st.text_input(
        "검색어",
        placeholder="예: 건폐율, 일조권, 처인구",
        key="dialog_history_search_input"
    )

    query = search_query.strip().lower()

    if not st.session_state.chat_history:
        st.caption("저장된 대화 기록이 없습니다.")
        return

    results = []

    for idx, chat in enumerate(st.session_state.chat_history):

        searchable_text = chat.get("title", "") + " "

        for msg in chat.get("messages", []):
            searchable_text += (
                msg.get("query", "") + " " +
                msg.get("response", "") + " "
            )

        if not query or query in searchable_text.lower():
            results.append((idx, chat))

    st.caption(
        f"검색 결과 {len(results)}건"
        if query else
        "최근 대화 목록"
    )

    if not results:
        st.warning("일치하는 검색 결과가 없습니다.")
        return

    with st.container(height=420, border=False):

        for idx, chat in reversed(results[-20:]):

            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))

            preview = (
                chat.get("messages", [])[0].get("query", "")[:60] + "..."
                if chat.get("messages") else ""
            )

            if st.button(
                f"{title[:30]}  |  {time_str}",
                key=f"dialog_chat_{idx}",
                use_container_width=True
            ):
                st.session_state.selected_index = idx
                st.session_state.current_page = "main"
                st.rerun()

            st.caption(f"미리보기: {preview}")
            st.divider()

# ==========================================
# 5. 사이드바
# ==========================================
with st.sidebar:

    st.markdown("""
    <div style="padding-top:8px; padding-bottom:10px;">
        <div style="font-size:26px; font-weight:700;">
            Yongin Building AI
        </div>
        <div style="font-size:13px; opacity:0.72; margin-top:4px;">
            용인시 건축 조례 분석 플랫폼
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 로그인
    with st.expander("사용자 계정", expanded=(st.session_state.user_id == "guest")):

        if st.session_state.user_id == "guest":

            auth_tabs = st.tabs(["로그인", "회원가입"])

            with auth_tabs[0]:

                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")

                if st.button("로그인", use_container_width=True):

                    from storage import authenticate_user

                    if authenticate_user(login_id.strip(), login_pw.strip()):

                        st.session_state.user_id = login_id.strip()
                        st.session_state.chat_history = load_history(
                            st.session_state.user_id
                        )

                        st.toast("로그인되었습니다.")
                        st.rerun()

                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

            with auth_tabs[1]:

                reg_id = st.text_input("새 아이디", key="reg_id")
                reg_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")

                if st.button("회원가입", use_container_width=True):

                    from storage import check_id_exists, register_user

                    if check_id_exists(reg_id.strip()):
                        st.error("이미 사용 중인 아이디입니다.")

                    elif register_user(reg_id.strip(), reg_pw.strip()):
                        st.success("회원가입이 완료되었습니다.")

        else:

            st.markdown(
                f"""
                <div class="custom-card">
                    <div style="font-size:13px; opacity:0.72;">현재 사용자</div>
                    <div style="font-size:18px; font-weight:700; margin-top:6px;">
                        {st.session_state.user_id}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("로그아웃", use_container_width=True):

                st.session_state.user_id = "guest"
                st.session_state.chat_history = load_history("guest")
                st.session_state.selected_index = None

                st.rerun()

    st.divider()

    # 메뉴
    st.subheader("메뉴")

    if st.button("AI 조례 분석", use_container_width=True):
        st.session_state.current_page = "main"
        st.rerun()

    if st.button("민원 문서 작성", use_container_width=True):
        st.session_state.current_page = "doc_gen"
        st.rerun()

    if st.button("실무 Q&A", use_container_width=True):
        st.session_state.current_page = "qna"
        st.rerun()

    if st.button("사이트맵", use_container_width=True):
        st.session_state.current_page = "sitemap"
        st.rerun()

    st.divider()

    st.toggle(
        "다크 모드",
        key="dark_mode_toggle",
        on_change=sync_dark_mode
    )

    st.divider()

    # 대화 기록
    st.subheader("대화 기록")

    c_new, c_src = st.columns(2)

    with c_new:

        if st.button("새 대화", use_container_width=True):

            st.session_state.selected_index = None
            st.session_state.current_page = "main"

            st.rerun()

    with c_src:

        if st.button("검색", use_container_width=True):
            open_history_search_dialog()

    history_container = st.container(height=400, border=False)

    with history_container:

        if st.session_state.chat_history:

            for i, chat in enumerate(reversed(st.session_state.chat_history)):

                actual_index = len(st.session_state.chat_history) - 1 - i

                time_str = chat.get(
                    "updated_at",
                    chat.get("created_at", "00-00 00:00")
                )[5:16]

                query_summary = chat.get("title", "새 대화")[:16]

                col_btn, col_del = st.columns([84, 16])

                with col_btn:

                    if st.button(
                        f"{time_str}  |  {query_summary}",
                        key=f"hist_{actual_index}",
                        use_container_width=True
                    ):
                        st.session_state.selected_index = actual_index
                        st.session_state.current_page = "main"
                        st.rerun()

                with col_del:

                    if st.button(
                        "삭제",
                        key=f"del_{actual_index}",
                        use_container_width=True
                    ):

                        st.session_state.chat_history.pop(actual_index)

                        from storage import save_history

                        save_history(
                            st.session_state.chat_history,
                            st.session_state.user_id
                        )

                        if st.session_state.selected_index == actual_index:
                            st.session_state.selected_index = None

                        elif (
                            st.session_state.selected_index is not None
                            and st.session_state.selected_index > actual_index
                        ):
                            st.session_state.selected_index -= 1

                        st.rerun()

        else:
            st.caption("저장된 대화가 없습니다.")

    if st.session_state.chat_history:

        if st.button(
            "전체 기록 삭제",
            type="secondary",
            use_container_width=True
        ):

            st.session_state.chat_history = []
            st.session_state.selected_index = None

            from storage import clear_history

            clear_history(st.session_state.user_id)

            st.toast("대화 기록이 삭제되었습니다.")
            st.rerun()

# ==========================================
# 6. 메인 페이지
# ==========================================
if st.session_state.current_page == "main":

    st.markdown("""
    <div class="main-title">
        건축 조례 및 법령 분석 시스템
    </div>
    <div class="main-caption">
        용인시 조례 및 상위 법령 데이터를 기반으로 규제 조건과 예외 조항을 분석합니다.
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.selected_index is not None:

        current_chat = st.session_state.chat_history[
            st.session_state.selected_index
        ]

        if "state" not in current_chat:
            current_chat["state"] = {}

        current_state = current_chat["state"]

    else:
        current_chat = None
        current_state = {}

    col_top_left, col_top_right = st.columns([4, 1])

    with col_top_right:
        show_state_panel = st.toggle(
            "컨텍스트 패널",
            value=True,
            key="use_state_panel"
        )

    if show_state_panel:
        col_chat, col_state = st.columns([73, 27])
    else:
        col_chat = st.container()
        col_state = None

    with col_chat:

        chat_box = st.container(height=540, border=False)

        user_query = st.chat_input(
            "검토할 조례 또는 건축 규정을 입력하세요."
        )

        with chat_box:

            if current_chat is not None:

                st.info(
                    f"불러온 대화: {current_chat.get('title', '이전 대화')}"
                )

                for msg in current_chat.get("messages", []):

                    render_user_message(msg.get("query", ""))
                    render_ai_report(msg.get("response", ""))

                if st.button(
                    "현재 대화 종료 후 새 질의 시작",
                    use_container_width=True
                ):
                    st.session_state.selected_index = None
                    st.rerun()

            else:

                st.markdown("""
                <div class="custom-card">
                    <div style="font-size:22px; font-weight:700; margin-bottom:10px;">
                        건축 규정 질의 입력
                    </div>
                    <div style="font-size:14px; opacity:0.8;">
                        건축법, 시행령, 용인시 조례 데이터를 기반으로 분석 결과를 제공합니다.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c_info1, c_info2 = st.columns(2)

                with c_info1:
                    st.info(
                        "예시: 기흥구 상업지역 용적률 완화 적용 가능 여부"
                    )

                with c_info2:
                    st.info(
                        "예시: 대지 안 공지 규정의 이격거리 예외 기준"
                    )

        if user_query:

            render_user_message(user_query)

            with st.status("법령 데이터 분석 중...", expanded=True) as status:

                try:

                    st.write("조례 및 상위 법령 데이터 매핑 중...")

                    response_text = handle_ai_analysis(user_query)

                    if st.session_state.chat_history:
                        st.session_state.selected_index = (
                            len(st.session_state.chat_history) - 1
                        )

                    status.update(
                        label="분석 완료",
                        state="complete"
                    )

                    render_ai_report(response_text)

                    st.toast("분석 결과가 생성되었습니다.")

                except Exception as e:

                    status.update(
                        label="오류 발생",
                        state="error"
                    )

                    st.error(f"오류 내용: {str(e)}")

            st.rerun()

    if show_state_panel and col_state is not None:

        with col_state:

            st.markdown("""
            <div style="font-size:18px; font-weight:700; margin-bottom:8px;">
                컨텍스트 설정
            </div>
            """, unsafe_allow_html=True)

            st.caption("분석에 사용할 대지 및 조건 정보")

            with st.container(border=True):

                search_addr = st.text_input(
                    "주소 입력",
                    placeholder="예: 처인구 중부대로 1199"
                )

                if st.button(
                    "토지 정보 불러오기",
                    use_container_width=True
                ):

                    if current_chat is not None:

                        mock_data = {
                            "용도지역": "일반주거지역",
                            "제한구역": "비행안전구역",
                            "대지면적": "1,250㎡"
                        }

                        current_chat["state"].update(mock_data)

                        save_history(
                            st.session_state.chat_history,
                            st.session_state.user_id
                        )

                        st.rerun()

            if current_chat is not None:

                if not current_state:
                    df_state = pd.DataFrame(
                        columns=["항목", "값"]
                    )
                else:
                    df_state = pd.DataFrame(
                        list(current_state.items()),
                        columns=["항목", "값"]
                    )

                edited_df = st.data_editor(
                    df_state,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key=f"state_editor_v2_{st.session_state.selected_index}"
                )

                new_state = {}

                for _, row in edited_df.iterrows():

                    k = (
                        str(row["항목"]).strip()
                        if pd.notna(row["항목"])
                        else ""
                    )

                    v = (
                        str(row["값"]).strip()
                        if pd.notna(row["값"])
                        else ""
                    )

                    if k and k != "nan":
                        new_state[k] = v

                if new_state != current_state:

                    current_chat["state"] = new_state

                    save_history(
                        st.session_state.chat_history,
                        st.session_state.user_id
                    )

                    st.rerun()

            else:
                st.info("대화를 생성하면 컨텍스트를 설정할 수 있습니다.")

# ==========================================
# 7. 문서 생성 페이지
# ==========================================
elif st.session_state.current_page == "doc_gen":

    st.markdown("""
    <div class="main-title">
        민원 문서 작성 시스템
    </div>
    <div class="main-caption">
        입력한 내용을 기반으로 행정 문서를 자동 생성합니다.
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    required_docs = {
        "건축허가 관련": ["건축허가 신청서", "배치도", "평면도"],
        "건축선 문의": ["대지 위치도", "토지이용계획확인서"],
        "일조권 민원": ["현장 사진", "건축물 배치도"],
        "불법건축물 신고": ["현장 사진", "위치도"],
        "용도변경 문의": ["건축물대장", "평면도"],
        "주차장 기준 문의": ["배치도", "주차계획도"],
        "건축물 해석 문의": ["질의서", "관련 도면"],
        "기타": ["신분증", "설명자료"]
    }

    department_map = {
        "건축허가 관련": "건축허가과",
        "건축선 문의": "건축과",
        "일조권 민원": "건축과",
        "불법건축물 신고": "건축과",
        "용도변경 문의": "건축허가과",
        "주차장 기준 문의": "교통정책과",
        "건축물 해석 문의": "건축과",
        "기타": "민원여권과"
    }

    col1, col2 = st.columns(2)

    with col1:
        civil_type = st.selectbox(
            "문서 유형",
            list(required_docs.keys())
        )

    with col2:
        site_address = st.text_input(
            "대상 주소",
            placeholder="예: 경기도 용인시 처인구"
        )

    civil_content = st.text_area(
        "내용 입력",
        height=160,
        placeholder="민원 내용을 입력하세요."
    )

    if st.button(
        "문서 생성",
        use_container_width=True,
        type="primary"
    ):

        if not site_address or not civil_content:

            st.error("주소와 내용을 모두 입력해 주세요.")

        else:

            with st.spinner("문서 생성 중..."):

                try:

                    result = generate_civil_document(
                        civil_type,
                        site_address,
                        civil_content
                    )

                    st.session_state.selected_index = None

                    st.success("문서가 생성되었습니다.")

                    st.divider()

                    st.subheader("생성 결과")

                    st.markdown(
                        f"""
                        <div class="custom-card">
                            {result}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    info_tabs = st.tabs([
                        "필수 서류",
                        "담당 부서",
                        "접수 절차",
                        "파일 다운로드"
                    ])

                    with info_tabs[0]:

                        for doc in required_docs.get(
                            civil_type,
                            required_docs["기타"]
                        ):
                            st.write(f"• {doc}")

                    with info_tabs[1]:

                        dept = department_map.get(
                            civil_type,
                            "민원여권과"
                        )

                        st.info(f"담당 부서: {dept}")

                    with info_tabs[2]:

                        st.markdown("""
                        1. 정부24 또는 세움터 접수
                        2. 용인시청 민원실 방문 접수 가능
                        """)

                    with info_tabs[3]:

                        doc = Document()

                        doc.add_heading(
                            '용인시 건축 민원 문서',
                            level=1
                        )

                        doc.add_paragraph(
                            f"문서 유형: {civil_type}\n"
                            f"주소: {site_address}"
                        )

                        doc.add_heading('본문', level=2)
                        doc.add_paragraph(result)

                        buffer = io.BytesIO()

                        doc.save(buffer)

                        buffer.seek(0)

                        st.download_button(
                            label="DOCX 다운로드",
                            data=buffer,
                            file_name=f"용인시_건축문서_{civil_type}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")

# ==========================================
# 8. Q&A 페이지
# ==========================================
elif st.session_state.current_page == "qna":

    st.markdown("""
    <div class="main-title">
        실무 Q&A
    </div>
    <div class="main-caption">
        건축 인허가 및 규정 해석 관련 질문과 답변을 공유합니다.
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns([65, 35])

    with col1:

        st.subheader("질문 목록")

        if not st.session_state.qna_list:
            st.info("등록된 질문이 없습니다.")

        else:

            for i, q in enumerate(st.session_state.qna_list):

                badge = (
                    "답변 대기"
                    if q['status'] == "대기중"
                    else "답변 완료"
                )

                with st.expander(f"[{badge}] {q['title']}"):

                    st.markdown(f"질문 내용: {q['content']}")

                    if q['status'] == "답변완료":
                        st.info(f"답변: {q['answer']}")

    with col2:

        st.subheader("질문 등록")

        with st.form("qna_form_v2", clear_on_submit=True):

            q_title = st.text_input("제목")

            q_content = st.text_area("내용")

            if st.form_submit_button(
                "등록",
                use_container_width=True
            ):

                if q_title and q_content:

                    st.session_state.qna_list.append({
                        "title": q_title,
                        "content": q_content,
                        "status": "대기중",
                        "answer": ""
                    })

                    st.success("질문이 등록되었습니다.")
                    st.rerun()

                else:
                    st.error("모든 항목을 입력해 주세요.")

        st.divider()

        with st.expander("관리자"):

            admin_pw = st.text_input(
                "관리자 비밀번호",
                type="password"
            )

            if admin_pw == "2026":

                st.success("관리자 모드 활성화")

                for i, q in enumerate(st.session_state.qna_list):

                    if q['status'] == "대기중":

                        answer_text = st.text_input(
                            f"답변 입력 - {q['title']}",
                            key=f"ans_{i}"
                        )

                        if st.button(
                            "답변 등록",
                            key=f"btn_{i}"
                        ):

                            st.session_state.qna_list[i]['answer'] = answer_text
                            st.session_state.qna_list[i]['status'] = "답변완료"

                            st.rerun()

# ==========================================
# 9. 사이트맵
# ==========================================
elif st.session_state.current_page == "sitemap":

    st.markdown("""
    <div class="main-title">
        플랫폼 구조 및 법규 데이터
    </div>
    <div class="main-caption">
        플랫폼 아키텍처 및 학습 데이터 구조입니다.
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    architecture_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">

<style>

body{
    margin:0;
    padding:20px;
    background:#f5f7fb;
    font-family: Pretendard, sans-serif;
}

.wrapper{
    background:#ffffff;
    padding:28px;
    border-radius:18px;
    border:1px solid #dbe2ea;
}

.title{
    font-size:28px;
    font-weight:700;
    margin-bottom:24px;
    color:#111827;
}

.section{
    background:#ffffff;
    border:1px solid #dbe2ea;
    border-radius:14px;
    padding:20px;
    margin-bottom:18px;
}

.section-title{
    font-size:18px;
    font-weight:700;
    margin-bottom:16px;
    color:#111827;
}

.flex{
    display:flex;
    gap:14px;
    flex-wrap:wrap;
}

.card{
    flex:1;
    min-width:220px;
    border-radius:12px;
    padding:16px;
    border:1px solid #dbe2ea;
    background:#f8fafc;
}

.card-title{
    font-size:15px;
    font-weight:700;
    margin-bottom:6px;
    color:#111827;
}

.card-desc{
    font-size:13px;
    color:#475569;
}

</style>
</head>

<body>

<div class="wrapper">

<div class="title">
플랫폼 구조도
</div>

<div class="section">

<div class="section-title">
서비스 구성
</div>

<div class="flex">

<div class="card">
<div class="card-title">AI 조례 분석</div>
<div class="card-desc">건축 규정 및 법령 분석</div>
</div>

<div class="card">
<div class="card-title">민원 문서 작성</div>
<div class="card-desc">행정 문서 자동 생성</div>
</div>

<div class="card">
<div class="card-title">실무 Q&A</div>
<div class="card-desc">질문 및 답변 공유</div>
</div>

<div class="card">
<div class="card-title">컨텍스트 관리</div>
<div class="card-desc">대지 및 조건 변수 관리</div>
</div>

</div>
</div>

<div class="section">

<div class="section-title">
AI 및 백엔드
</div>

<div class="flex">

<div class="card">
<div class="card-title">LLM 분석 엔진</div>
<div class="card-desc">법령 분석 및 요약</div>
</div>

<div class="card">
<div class="card-title">법령 매핑 시스템</div>
<div class="card-desc">조례 및 상위 법령 연계</div>
</div>

<div class="card">
<div class="card-title">세션 및 인증</div>
<div class="card-desc">대화 이력 및 사용자 관리</div>
</div>

</div>
</div>

<div class="section">

<div class="section-title">
데이터베이스
</div>

<div class="flex">

<div class="card">
<div class="card-title">지역 조례 DB</div>
<div class="card-desc">용인시 및 경기도 조례</div>
</div>

<div class="card">
<div class="card-title">상위 법령 DB</div>
<div class="card-desc">국가 법령 및 시행령</div>
</div>

<div class="card">
<div class="card-title">사용자 데이터</div>
<div class="card-desc">세션 및 문서 데이터</div>
</div>

</div>
</div>

</div>

</body>
</html>
"""

    components.html(
        architecture_html,
        height=860,
        scrolling=True
    )

    st.divider()

    st.markdown("""
    <div style="
        font-size:22px;
        font-weight:700;
        margin-bottom:12px;
        margin-top:8px;
    ">
        학습 법규 목록
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "기본 조례",
        "상위 법령",
        "조례 연계 법규",
        "법령 연계 법규"
    ])

    # --------------------------------------
    # 탭1
    # --------------------------------------
    with tabs[0]:

        col1, col2, col3 = st.columns(3)

        ord_list = [
            "경기도 건축 조례",
            "경기도 건축기본조례",
            "경기도 건축물관리 조례",
            "용인시 건축 조례",
            "용인시 건축물관리 조례",
            "용인시 도시계획 조례"
        ]

        cols = [col1, col2, col3]

        for idx, item in enumerate(ord_list):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="custom-card">
                    {item}
                </div>
                """, unsafe_allow_html=True)

    # --------------------------------------
    # 탭2
    # --------------------------------------
    with tabs[1]:

        col1, col2, col3, col4 = st.columns(4)

        law_list = [
            "건축법",
            "건축기본법",
            "건축물관리법",
            "국토의 계획 및 이용에 관한 법률",
            "건축법 시행령",
            "건축법 시행규칙",
            "건축물관리법 시행령",
            "건축물관리법 시행규칙"
        ]

        cols = [col1, col2, col3, col4]

        for idx, item in enumerate(law_list):
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="custom-card">
                    {item}
                </div>
                """, unsafe_allow_html=True)

    # --------------------------------------
    # 탭3
    # --------------------------------------
    with tabs[2]:

        ord_borrow_data = [
            "건설기술진흥법",
            "건축기본법",
            "건축물관리법",
            "건축법",
            "건축사법",
            "공공주택 특별법",
            "국토의 계획 및 이용에 관한 법률",
            "녹색건축물 조성 지원법",
            "농지법",
            "도시 및 주거환경정비법",
            "문화예술진흥법",
            "산지관리법",
            "주택법",
            "건축법 시행령",
            "건축법 시행규칙"
        ]

        cols = st.columns(4)

        for idx, item in enumerate(ord_borrow_data):

            with cols[idx % 4]:

                st.markdown(f"""
                <div class="custom-card">
                    {item}
                </div>
                """, unsafe_allow_html=True)

    # --------------------------------------
    # 탭4
    # --------------------------------------
    with tabs[3]:

        law_borrow_data = [
            "건설기술 진흥법",
            "건설산업기본법",
            "건축기본법",
            "건축법",
            "건축사법",
            "경관법",
            "공동주택관리법",
            "국토의 계획 및 이용에 관한 법률",
            "녹색건축물 조성 지원법",
            "농지법",
            "도로법",
            "도시개발법",
            "문화예술진흥법",
            "민법",
            "산지관리법",
            "주차장법",
            "주택법",
            "행정대집행법"
        ]

        cols = st.columns(4)

        for idx, item in enumerate(law_borrow_data):

            with cols[idx % 4]:

                st.markdown(f"""
                <div class="custom-card">
                    {item}
                </div>
                """, unsafe_allow_html=True)
