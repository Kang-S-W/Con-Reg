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
# 1. 페이지 설정 (최상단 고정)
# ==========================================
st.set_page_config(
    page_title="용인시 건축 조례 지원 플랫폼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 외부 모듈 임포트 (기존 로직 유지)
try:
    from widget_utils import inject_floating_button
    from docx import Document
    from processor import handle_ai_analysis, generate_civil_document
    from style import apply_custom_style
    from components import render_user_message, render_ai_report
    from storage import load_history, save_history 
    
    inject_floating_button()
except ImportError:
    pass

# ==========================================
# 2. 세션 상태 관리 및 초기화
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = "guest"
if "chat_history" not in st.session_state: 
    try:
        st.session_state.chat_history = load_history(st.session_state.user_id)
    except NameError:
        st.session_state.chat_history = []
if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
if "selected_index" not in st.session_state: st.session_state.selected_index = None
if "current_page" not in st.session_state: st.session_state.current_page = "main"
if "qna_list" not in st.session_state: st.session_state.qna_list = []

def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle

try:
    apply_custom_style(st.session_state.dark_mode) 
except NameError:
    pass

# ==========================================
# 3. 프리미엄 인핸스드 테마 및 CSS 제어
# ==========================================
def apply_premium_ui_v2(is_dark):
    # 공통 적용 CSS (글꼴 및 기본 형태)
    base_css = """
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div { 
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; 
        }
        
        /* 입력창 디자인 개선 */
        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
            border-radius: 6px !important;
            transition: all 0.2s ease;
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 1px #2563eb !important;
        }
        
        /* 버튼 디자인 개선 */
        div[data-testid="stButton"] button {
            border-radius: 6px;
            font-weight: 500;
        }
    </style>
    """
    
    # 모드에 따른 명시적 컬러 변수 선언 (가시성 오류 근본 해결)
    if is_dark:
        theme_css = """
        <style>
            :root {
                --bg-color: #121212;
                --sec-bg-color: #1e1e1e;
                --text-color: #f1f5f9;
                --border-color: #334155;
                --input-bg: #0f172a;
            }
            [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: var(--bg-color) !important; color: var(--text-color) !important; }
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: var(--sec-bg-color) !important; border-right: 1px solid var(--border-color) !important; }
            
            .stMarkdown, .stText, label, p, h1, h2, h3, span { color: var(--text-color) !important; }
            
            div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput textarea {
                background-color: var(--input-bg) !important;
                border: 1px solid var(--border-color) !important;
            }
            div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: var(--text-color) !important; }
            
            div[data-testid="stExpander"] { background-color: var(--sec-bg-color) !important; border: 1px solid var(--border-color) !important; border-radius: 8px !important; }
            div[data-testid="stExpander"] details summary { background-color: var(--sec-bg-color) !important; color: var(--text-color) !important; }
            
            /* 팝업 다이얼로그 가시성 보장 */
            div[role="dialog"] { background-color: var(--sec-bg-color) !important; border: 1px solid var(--border-color) !important; border-radius: 12px; }
            div[role="dialog"] input { background-color: var(--input-bg) !important; color: var(--text-color) !important; }
            div[role="dialog"] * { color: var(--text-color) !important; }
        </style>
        """
    else:
        theme_css = """
        <style>
            :root {
                --bg-color: #f8fafc;
                --sec-bg-color: #ffffff;
                --text-color: #0f172a;
                --border-color: #cbd5e1;
                --input-bg: #ffffff;
            }
            [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background-color: var(--bg-color) !important; color: var(--text-color) !important; }
            [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: var(--sec-bg-color) !important; border-right: 1px solid var(--border-color) !important; }
            
            .stMarkdown, .stText, label, p, h1, h2, h3, span { color: var(--text-color) !important; }
            
            div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput > div {
                background-color: var(--input-bg) !important;
                border: 1px solid var(--border-color) !important;
            }
            div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: var(--text-color) !important; }
            
            div[data-testid="stExpander"], div[data-testid="stExpander"] > details { background-color: var(--sec-bg-color) !important; border: 1px solid var(--border-color) !important; border-radius: 8px !important; }
            div[data-testid="stExpander"] details summary { background-color: var(--sec-bg-color) !important; color: var(--text-color) !important; }
            
            /* 팝업 다이얼로그 가시성 보장 */
            div[role="dialog"] { background-color: var(--sec-bg-color) !important; border: 1px solid var(--border-color) !important; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            div[role="dialog"] input { background-color: var(--input-bg) !important; color: var(--text-color) !important; }
            div[role="dialog"] * { color: var(--text-color) !important; }
        </style>
        """
    st.markdown(base_css + theme_css, unsafe_allow_html=True)

apply_premium_ui_v2(st.session_state.dark_mode)

# --- [대화기록 내부 검색 팝업 창] ---
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

@dialog_decorator("대화 기록 검색", width="large")
def open_history_search_dialog():
    search_query = st.text_input("검색어 입력", placeholder="예: 건폐율, 사선제한, 처인구 등", key="dialog_history_search_input")
    query = search_query.strip().lower()

    if not st.session_state.chat_history:
        st.caption("저장된 대화 기록이 없습니다.")
        return

    results = []
    for idx, chat in enumerate(st.session_state.chat_history):
        searchable_text = chat.get("title", "") + " "
        for msg in chat.get("messages", []):
            searchable_text += msg.get("query", "") + " " + msg.get("response", "") + " "
        if not query or query in searchable_text.lower():
            results.append((idx, chat))

    st.caption(f"검색 결과: {len(results)}건" if query else "최근 생성된 대화")

    if not results:
        st.warning("일치하는 검색 결과가 없습니다.")
        return

    with st.container(height=380, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "지정되지 않은 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            preview = chat.get("messages", [])[0].get("query", "")[:50] + "..." if chat.get("messages") else "기록된 텍스트 없음"
            
            with st.container(border=True):
                if st.button(f"{title[:30]} | {time_str}", key=f"dialog_chat_{idx}", use_container_width=True):
                    st.session_state.selected_index = idx
                    st.session_state.current_page = "main"
                    st.rerun()
                st.caption(f"내용 요약: {preview}")

# ==========================================
# 4. 구조화된 사이드바 시스템
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; font-weight:700; color:#2563eb;'>Yong-In City</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:13px; color:#64748b; margin-top:-10px;'>건축 조례 지능형 분석 플랫폼</p>", unsafe_allow_html=True)
    st.divider()
    
    # [인증 인프라]
    with st.expander("사용자 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            auth_tabs = st.tabs(["로그인", "회원가입"])
            with auth_tabs[0]:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("로그인", use_container_width=True):
                    try:
                        from storage import authenticate_user
                        if authenticate_user(login_id.strip(), login_pw.strip()):
                            st.session_state.user_id = login_id.strip()
                            st.session_state.chat_history = load_history(st.session_state.user_id)
                            st.toast(f"환영합니다, {st.session_state.user_id} 님.")
                            st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                    except ImportError:
                        st.error("서버 모듈이 연동되지 않았습니다.")
            with auth_tabs[1]:
                reg_id = st.text_input("가입 아이디", key="reg_id")
                reg_pw = st.text_input("가입 비밀번호", type="password", key="reg_pw")
                if st.button("계정 생성", use_container_width=True):
                    try:
                        from storage import check_id_exists, register_user
                        if check_id_exists(reg_id.strip()):
                            st.error("이미 사용 중인 아이디입니다.")
                        elif register_user(reg_id.strip(), reg_pw.strip()):
                            st.toast("계정이 생성되었습니다. 다시 로그인해 주세요.")
                    except ImportError:
                        st.error("서버 모듈이 연동되지 않았습니다.")
        else:
            st.markdown(f"현재 접속자: <span style='color:#2563eb; font-weight:bold;'>{st.session_state.user_id}</span>", unsafe_allow_html=True)
            if st.button("로그아웃", use_container_width=True, type="secondary"):
                st.session_state.user_id = "guest"
                try:
                    from storage import load_history
                    st.session_state.chat_history = load_history("guest")
                except ImportError:
                    st.session_state.chat_history = []
                st.session_state.selected_index = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # [내비게이션 모듈]
    st.subheader("핵심 메뉴")
    if st.button("AI 규제 검토", use_container_width=True): st.session_state.current_page = "main"; st.rerun()
    if st.button("민원 서식 작성", use_container_width=True): st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("실무 Q&A", use_container_width=True): st.session_state.current_page = "qna"; st.rerun()
    if st.button("시스템 사이트맵", use_container_width=True): st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("다크 테마 적용", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.divider()
    
    # [대화 세션 히스토리 인터페이스]
    st.subheader("최근 대화 기록")
    c_new, c_src = st.columns(2)
    with c_new:
        if st.button("새 대화방", use_container_width=True, type="primary"):
            st.session_state.selected_index = None
            st.session_state.current_page = "main"
            st.rerun()
    with c_src:
        if st.button("검색", use_container_width=True):
            open_history_search_dialog()

    with st.container(height=350, border=True):
        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                actual_index = len(st.session_state.chat_history) - 1 - i
                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]
                query_summary = chat.get("title", "질의 데이터")[:11] + ".."
                
                col_btn, col_del = st.columns([80, 20])
                with col_btn:
                    if st.button(f"{time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                        st.session_state.selected_index = actual_index
                        st.session_state.current_page = "main"
                        st.rerun()
                with col_del:
                    if st.button("삭제", key=f"del_{actual_index}", use_container_width=True):
                        st.session_state.chat_history.pop(actual_index)
                        try:
                            from storage import save_history
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                        except ImportError:
                            pass
                        if st.session_state.selected_index == actual_index:
                            st.session_state.selected_index = None
                        elif st.session_state.selected_index is not None and st.session_state.selected_index > actual_index:
                            st.session_state.selected_index -= 1
                        st.rerun()
        else:
            st.caption("저장된 기록이 없습니다.")

    if st.session_state.chat_history:
        if st.button("전체 대화 기록 삭제", type="secondary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.selected_index = None
            try:
                from storage import clear_history
                clear_history(st.session_state.user_id) 
            except ImportError:
                pass
            st.toast("대화 기록이 모두 삭제되었습니다.")
            st.rerun()


# ==========================================
# 5. 비즈니스 로직 및 화면 분기 (Main)
# ==========================================

# --- [화면 1] 메인 인공지능 분석 엔진 ---
if st.session_state.current_page == "main":
    st.markdown("## 건축 조례 및 규제 법령 해석 AI 시스템")
    st.caption("용인시 전역의 자치조례 및 상위 상호 연계 법령을 연산하여 정밀한 예외 조건 및 규제 요약을 도출합니다.")
    st.write("")

    if st.session_state.selected_index is not None:
        current_chat = st.session_state.chat_history[st.session_state.selected_index]
        if "state" not in current_chat: current_chat["state"] = {}
        current_state = current_chat["state"]
    else:
        current_chat = None
        current_state = {}

    col_top_left, col_top_right = st.columns([4, 1])
    with col_top_right:
        show_state_panel = st.toggle("대상지 정보 설정", value=True, key="use_state_panel")

    if show_state_panel:
        col_chat, col_state = st.columns([73, 27])
    else:
        col_chat = st.container()
        col_state = None

    with col_chat:
        chat_box = st.container(height=520, border=True)
        
        user_query = st.chat_input("조례 해석 또는 규제 검토 대상을 입력하세요. (예: 처인구 자연녹지지역 내 조례상 건폐율 특례조항)")

        with chat_box:
            if current_chat is not None:
                st.info(f"과거 분석 기록을 불러왔습니다: {current_chat.get('title', '이전 대화')}")
                for msg in current_chat.get("messages", []):
                    try:
                        render_user_message(msg.get("query", ""))
                        render_ai_report(msg.get("response", ""))
                    except NameError:
                        st.markdown(f"**질문:** {msg.get('query', '')}")
                        st.markdown(f"**답변:** {msg.get('response', '')}")
                
                if st.button("새로운 질의 시작", use_container_width=True):
                    st.session_state.selected_index = None
                    st.rerun()
            else:
                st.markdown("""
                <div style='text-align: center; padding: 60px 20px;'>
                    <h3 style='color: #2563eb; font-weight:600; margin-bottom: 12px;'>질의할 건축 규제를 입력해 주세요</h3>
                    <p style='color: #64748b; font-size: 14px;'>상위 건축법령 및 경기도/용인시 자치법규 데이터베이스를 교차 매핑하여 정확한 행정 유권해석 룰셋을 출력합니다.</p>
                </div>
                """, unsafe_allow_html=True)
                
                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    st.info("질의 예시: 용인시 기흥구 상업지역 용적률 인센티브 완화 적용 범위")
                with c_info2:
                    st.info("질의 예시: 대지안의 공지 규정 관련 용인시 조례상 이격거리 예외 기준")

        if user_query:
            try:
                render_user_message(user_query)
            except NameError:
                st.markdown(f"**질문:** {user_query}")
                
            with st.status("분석 엔진 작동 중 (시맨틱 법률 조항 매핑)...", expanded=True) as status:
                try:
                    st.write("실시간 조례 데이터셋 및 연계 차용법령 가중치 분석 중...")
                    try:
                        response_text = handle_ai_analysis(user_query)
                    except NameError:
                        time.sleep(1)
                        response_text = f"분석 결과 모의 데이터입니다.\n질의하신 '{user_query}'에 대한 검토 내용입니다."

                    if st.session_state.chat_history:
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1

                    status.update(label="해석 도출 완료", state="complete")
                    try:
                        render_ai_report(response_text)
                    except NameError:
                        st.markdown(f"**답변:** {response_text}")
                        
                    st.toast("분석이 완료되었습니다.")
                except Exception as e:
                    status.update(label="오류 발생", state="error")
                    st.error(f"시스템 메시지: {str(e)}")
            st.rerun()

    if show_state_panel and col_state is not None:
        with col_state:
            with st.container(border=True):
                st.markdown("<p style='font-size:16px; font-weight:600; margin-bottom:2px;'>검토 대상지 정보</p>", unsafe_allow_html=True)
                st.caption("분석에 반영될 대상지 속성 값입니다.")

                search_addr = st.text_input("대상지 주소 입력", placeholder="예: 처인구 중부대로 1199", label_visibility="collapsed")
                if st.button("토지대장 정보 불러오기", use_container_width=True):
                    if current_chat is not None:
                        mock_data = {"검토지구": "일반주거지역", "제한구역": "비행안전구역", "산정대지면적": "1,250㎡"}
                        current_chat["state"].update(mock_data)
                        try:
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                        except NameError:
                            pass
                        st.rerun()

                if current_chat is not None:
                    if not current_state:
                        df_state = pd.DataFrame(columns=["항목", "내용"])
                    else:
                        df_state = pd.DataFrame(list(current_state.items()), columns=["항목", "내용"])

                    edited_df = st.data_editor(
                        df_state,
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True,
                        key=f"state_editor_v2_{st.session_state.selected_index}"
                    )

                    new_state = {}
                    for _, row in edited_df.iterrows():
                        k = str(row["항목"]).strip() if pd.notna(row["항목"]) else ""
                        v = str(row["내용"]).strip() if pd.notna(row["내용"]) else ""
                        if k and k != "nan": new_state[k] = v

                    if new_state != current_state:
                        current_chat["state"] = new_state
                        try:
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                        except NameError:
                            pass
                        st.rerun()
                else:
                    st.info("선택된 대화가 없습니다. 새로운 대화를 시작하거나 기존 기록을 선택해 주세요.")
        
        
# --- [화면 2] 민원 양식 생성 자동화 모듈 ---
elif st.session_state.current_page == "doc_gen":
    st.markdown("## 행정 민원 문서 자동 작성")
    st.caption("작성하고자 하는 내용의 흐름을 입력하시면 표준화된 행정 문서 포맷으로 가공 및 변환합니다.")
    st.divider()

    required_docs = {
        "건축허가 관련": ["건축허가 신청서", "배치도", "평면도", "토지이용계획확인서", "건축계획서"],
        "건축선 문의": ["대지 위치도", "토지이용계획확인서", "현장 사진"],
        "일조권 민원": ["현장 사진", "건축물 배치도", "피해 설명 자료"],
        "불법건축물 신고": ["현장 사진", "위치도", "불법사항 설명자료"],
        "용도변경 문의": ["건축물대장", "평면도", "용도변경 계획서"],
        "주차장 기준 문의": ["배치도", "주차계획도", "건축 개요"],
        "건축물 해석 문의": ["질의서", "관련 도면", "현장 사진"],
        "기타": ["신분증", "민원 설명자료"]
    }
    department_map = {
        "건축허가 관련": "건축허가과", "건축선 문의": "건축과", "일조권 민원": "건축과", 
        "불법건축물 신고": "건축과", "용도변경 문의": "건축허가과", "주차장 기준 문의": "교통정책과", 
        "건축물 해석 문의": "건축과", "기타": "민원여권과"
    }

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            civil_type = st.selectbox("민원 목적 선택", list(required_docs.keys()))
        with col2:
            site_address = st.text_input("대상 건축물 주소", placeholder="예: 경기도 용인시 처인구 역북동")

        civil_content = st.text_area("상세 요청 사항", height=140, placeholder="양식에 맞춰 구체화할 내용을 입력해 주세요.")

        if st.button("행정 양식 생성", use_container_width=True, type="primary"):
            if not site_address or not civil_content:
                st.error("대상 주소 및 상세 요청 사항을 입력해 주십시오.")
            else:
                with st.spinner("문서를 작성 중입니다..."):
                    try:
                        try:
                            result = generate_civil_document(civil_type, site_address, civil_content)
                        except NameError:
                            result = f"{civil_type} 관련 자동 생성된 문서 내용입니다.\n주소: {site_address}\n내용: {civil_content}"
                            
                        st.session_state.selected_index = None
                        st.success("문서 작성이 완료되었습니다.")
                        
                        st.divider()
                        st.subheader("생성 완료된 서식 리포트")
                        st.markdown(f"<div style='padding:24px; border:1px solid #cbd5e1; border-radius:8px; background:var(--background-color);'>{result}</div>", unsafe_allow_html=True)
                        
                        st.write("")
                        info_tabs = st.tabs(["필수 증빙 목록", "관할 행정 부서", "접수 프로세스", "파일 내보내기"])
                        
                        with info_tabs[0]:
                            for doc in required_docs.get(civil_type, required_docs["기타"]):
                                st.write(f"- {doc}")
                        with info_tabs[1]:
                            dept = department_map.get(civil_type, "민원여권과")
                            st.info(f"용인시청 및 관할 구청 소관 부서: **{dept}**")
                        with info_tabs[2]:
                            st.markdown("""
                            1. **온라인 접수:** 정부24 전자민원 혹은 세움터(e-housing) 통합 접수
                            2. **오프라인 접수:** 용인시 종합민원실 방문 후 일괄 접수 처리
                            """)
                        with info_tabs[3]:
                            try:
                                doc = Document()
                                doc.add_heading('용인시 건축 행정 민원 문서', level=1)
                                doc.add_paragraph(f"행정 분류: {civil_type}\n소재 주소: {site_address}")
                                doc.add_heading('본문 내용', level=2)
                                doc.add_paragraph(result)

                                buffer = io.BytesIO()
                                doc.save(buffer)
                                buffer.seek(0)
                                st.download_button(
                                    label="DOCX 파일 다운로드",
                                    data=buffer,
                                    file_name=f"용인시_건축서식_{civil_type}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                            except NameError:
                                st.error("python-docx 패키지가 설치되지 않아 파일 내보내기를 지원할 수 없습니다.")
                    except Exception as e:
                        st.error(f"오류 발생: {str(e)}")

# --- [화면 3] 전문가 교차 검증 Q&A 게시판 ---
elif st.session_state.current_page == "qna":
    st.markdown("## 실무자 간 규제 해석 교차 검증 공간")
    st.caption("인허가 과정에서 발생하는 모호한 사안에 대해 질문을 등록하고 답변을 공유합니다.")
    st.divider()
    
    col1, col2 = st.columns([65, 35])
    with col1:
        st.subheader("전체 질의응답 내역")
        if not st.session_state.qna_list:
            st.info("등록된 질의 내역이 없습니다.")
        else:
            for i, q in enumerate(st.session_state.qna_list):
                badge = "[접수 대기]" if q['status'] == "대기중" else "[검증 완료]"
                with st.expander(f"{badge} {q['title']}"):
                    st.markdown(f"**질의 요지:** {q['content']}")
                    if q['status'] == "답변완료":
                        st.info(f"**해석 공유 답변:** {q['answer']}")
    
    with col2:
        st.subheader("질의 안건 등록")
        with st.container(border=True):
            with st.form("qna_form_v2", clear_on_submit=True):
                q_title = st.text_input("안건 요약 명칭")
                q_content = st.text_area("상세 내용 기술")
                if st.form_submit_button("질문 등록", use_container_width=True):
                    if q_title and q_content:
                        st.session_state.qna_list.append({"title": q_title, "content": q_content, "status": "대기중", "answer": ""})
                        st.success("새로운 안건이 성공적으로 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("모든 항목을 입력해 주십시오.")
        
        st.write("")
        with st.expander("관리자 승인 영역"):
            admin_pw = st.text_input("관리자 PIN", type="password")
            if admin_pw == "2026":
                st.success("인증되었습니다.")
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        answer_text = st.text_input(f"답변 입력: {q['title']}", key=f"ans_{i}")
                        if st.button("답변 등록", key=f"btn_{i}"):
                            st.session_state.qna_list[i]['answer'] = answer_text
                            st.session_state.qna_list[i]['status'] = "답변완료"
                            st.rerun()

# --- [화면 4] 사이트맵 ---
elif st.session_state.current_page == "sitemap":

    st.markdown("## 플랫폼 구조 및 법률 아카이브 트리")
    st.caption("플랫폼 엔진이 검사하는 데이터 구조의 설계 및 참조 색인 목록입니다.")
    st.divider()

    architecture_html = textwrap.dedent("""
    <div style="background-color: #0f172a; padding: 25px; border-radius: 12px; font-family: sans-serif; margin-bottom: 30px;">
        <div style="color: #ffffff; text-align: center; font-size: 20px; font-weight: 600; margin-bottom: 25px;">용인시 건축 조례 분석 플랫폼 구조도</div>
        
        <div style="background-color: #1e293b; border-radius: 8px; padding: 18px; margin-bottom: 15px; border: 1px solid #334155;">
            <div style="text-align: center; font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 15px;">사용자 인터페이스 (UI)</div>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 160px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">AI 규제 검토</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">법령 시맨틱 분석 질의응답</div>
                </div>
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 160px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">민원 서식 빌더</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">행정 서류 자동 완성</div>
                </div>
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 160px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">실무 Q&A 게시판</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">지식 공유 및 유권해석</div>
                </div>
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 160px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">컨텍스트 관리소</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">대지 상태 및 파라미터 제어</div>
                </div>
            </div>
        </div>

        <div style="background-color: #1e293b; border-radius: 8px; padding: 18px; margin-bottom: 15px; border: 1px solid #334155;">
            <div style="text-align: center; font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 15px;">통합 엔진 (System Logic)</div>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">LLM 분석 모듈</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">자연어 처리 및 문맥 분석</div>
                </div>
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">법률 레이어 구조화</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">규제 조항 필터링 및 맵핑</div>
                </div>
                <div style="background-color: #334155; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #f1f5f9; font-size: 14px;">세션 동기화 관리</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">대화 이력 보존 및 상태 유지</div>
                </div>
            </div>
        </div>

        <div style="background-color: #1e293b; border-radius: 8px; padding: 18px; border: 1px solid #334155;">
            <div style="text-align: center; font-weight: 600; color: #94a3b8; font-size: 15px; margin-bottom: 15px;">데이터베이스 연계 (DB)</div>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #38bdf8; font-size: 13px;">지역 자치법규 DB</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">용인시 및 경기도 지역 조례</div>
                </div>
                <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #38bdf8; font-size: 13px;">상위 차용 법령 DB</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">대한민국 국가 법령 인덱스</div>
                </div>
                <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 12px; flex: 1; min-width: 200px; text-align: center;">
                    <div style="font-weight: 600; color: #38bdf8; font-size: 13px;">로컬 문서 시스템 DB</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">서식 스키마 및 사용자 데이터</div>
                </div>
            </div>
        </div>
    </div>
    """).strip()

    components.html(
        architecture_html,
        height=600,
        scrolling=True
    )
    
    # 탭별 데이터베이스 테이블 출력
    tabs = st.tabs(["1. 기본 조례 일람", "2. 상위 기본 법령 일람", "3. 조례의 차용 법규 (전체 44개)", "4. 법령의 차용 법규 (전체 61개)"])
    
    with tabs[0]:
        df_ord = pd.DataFrame([
            ["경기도", "경기도 건축 조례"],
            ["경기도", "경기도 건축기본조례"],
            ["경기도", "경기도 건축물 미술작품 설치 및 관리에 관한 조례"],
            ["경기도", "경기도 건축물관리 조례"],
            ["용인시", "용인시 건축 조례"],
            ["용인시", "용인시 건축물관리 조례"],
            ["용인시", "용인시 도시계획 조례"]
        ], columns=["소관 지자체", "지방자치조례 정식 명칭"])
        st.dataframe(df_ord, hide_index=True, use_container_width=True)

    with tabs[1]:
        df_law = pd.DataFrame([
            ["건축법"], ["건축기본법"], ["문화예술진흥법"], ["건축물관리법"], ["국토의 계획 및 이용에 관한 법률"],
            ["건축법 시행령"], ["건축기본법 시행령"], ["문화예술진흥법 시행령"], ["건축물관리법 시행령"], ["국토의 계획 및 이용에 관한 법률 시행령"],
            ["건축법 시행규칙"], ["건축물관리법 시행규칙"], ["국토의 계획 및 이용에 관한 법률 시행규칙"]
        ], columns=["대한민국 법령 및 시행령/시행규칙"])
        st.dataframe(df_law, hide_index=True, use_container_width=True)

    with tabs[2]:
        ord_borrow_data = [
            "감정평가 및 감정평가사에 관한 법률", "건설기술진흥법", "건축기본법", "건축물관리법", 
            "건축법", "건축사법", "고등교육법", "공공주택 특별법", "관광진흥법", 
            "국가유산기본법", "국토의 계획 및 이용에 관한 법률", "근현대문화유산의 보존 및 활용에 관한 법률", 
            "녹색건축물 조성 지원법", "농지법", "대기환경보전법", "도시 및 주거환경정비법", 
            "문화예술진흥법", "민간임대주택에 관한 특별법", "산업입지 및 개발에 관한 법률", 
            "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "실내공기질 관리법", 
            "자연공원법", "전통사찰의 보존 및 지원에 관한 법률", "주택법", 
            "한옥 등 건축자산의 진흥에 관한 법률", "건축기본법 시행령", "건축물관리법 시행령", 
            "건축법 시행령", "국토의 계획 및 이용에 관한 법률 시행령", "농지법 시행령", 
            "다중이용업소의 안전관리에 관한 특별법 시행령", "문화예술진흥법 시행령", 
            "민원 처리에 관한 법률 시행령", "건축물관리법 시행규칙", "건축법 시행규칙", 
            "국토의 계획 및 이용에 관한 법률 시행규칙", "경기도 건축물 미술작품 설치 및 관리에 관한 조례 시행규칙", 
            "경기도 위원회 수당 및 여비 지급 조례", "경기도 지방보조금 관리 조례", 
            "용인시 각종 위원회 설치 및 운영 조례", "용인시 건축 조례", "용인시 도시계획 조례", 
            "공공발주사업에 대한 건축사의 업무범위와 대가기준"
        ]
        df_ord_borrow = pd.DataFrame({"연계 조례의 차용 법규명": ord_borrow_data})
        st.dataframe(df_ord_borrow, hide_index=True, use_container_width=True)

    with tabs[3]:
        law_borrow_data = [
            "국토기본법", "수도권정비계획법", "공간정보의 구축 및 관리 등에 관한 법률", "공유수면 관리 및 매립에 관한 법률",
            "도로법", "사도법", "주차장법", "하수도법", "수도법", "환경정책기본법", "자연환경보전법", 
            "대기환경보전법", "소음·진동관리법", "폐기물관리법", "재난 및 안전관리 기본법", "소방기본법", 
            "화재예방, 소방시설 설치·유지 및 안전관리에 관한 법률", "지진·화산재해대책법", "초지법", "산지관리법", 
            "산림자원의 조성 및 관리에 관한 법률", "농지법", "개발제한구역의 지정 및 관리에 관한 특별조치법",
            "도시공원 및 녹지 등에 관한 법률", "도시교통정비 촉진법", "도시개발법", "택지개발촉진법", 
            "주택법", "공동주택관리법", "도시 및 주거환경정비법", "산업입지 및 개발에 관한 법률",
            "산업집적활성화 및 공장설립에 관한 법률", "물류시설의 개발 및 운영에 관한 법률", "유통산업발전법",
            "관광진흥법", "체육시설의 설치·이용에 관한 법률", "문화재보호법", "자연공원법", "학교보건법",
            "교육환경 보호에 관한 법률", "영유아보육법", "장애인·노인·임산부 등의 편의증진 보장에 관한 법률",
            "건설산업기본법", "건설기술 진흥법", "건설기계관리법", "엔지니어링산업 진흥법", "건축사법",
            "부동산 가격공시에 관한 법률", "감정평가 및 감정평가사에 관한 법률", "공인중개사법", "측량·수로조사 및 지적에 관한 법률",
            "공공기관의 정보공개에 관한 법률", "개인정보 보호법", "행정절차법", "행정소송법", "행정심판법",
            "지방자치법", "지방재정법", "지방세법", "지방세기본법", "지방세특례제한법"
        ]
        df_law_borrow = pd.DataFrame({"연계 상위 법령의 차용 법규명": law_borrow_data})
        st.dataframe(df_law_borrow, hide_index=True, use_container_width=True)
