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
    page_icon=None, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 외부 모듈 임포트 (기존 로직 유지)
from widget_utils import inject_floating_button
from docx import Document
from processor import handle_ai_analysis, generate_civil_document
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 용인시 민원창구 연계 플로팅 버튼 활성화
inject_floating_button()

# ==========================================
# 2. 세션 상태 관리 및 초기화
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = "guest"
if "chat_history" not in st.session_state: st.session_state.chat_history = load_history(st.session_state.user_id)
if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
if "selected_index" not in st.session_state: st.session_state.selected_index = None
if "current_page" not in st.session_state: st.session_state.current_page = "main"
if "qna_list" not in st.session_state: st.session_state.qna_list = []

def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle

# 기본 커스텀 스타일 백엔드 적용
apply_custom_style(st.session_state.dark_mode) 

# ==========================================
# 3. 고대비 및 고해상도 테마 오버라이드 CSS (UI 개선 및 시인성 확보)
# ==========================================
def apply_premium_ui_v2(is_dark):
    base_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div, span { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    div[data-testid="stTabBar"] {
        gap: 8px !important;
    }
    div[data-testid="stMarkdownContainer"] p {
        line-height: 1.6 !important;
    }
</style>
"""
    if is_dark:
        theme_css = """
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a !important; color: #f8fafc !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: #1e293b !important; border-right: 1px solid #334155 !important; }
    
    /* 사이드바 메뉴 버튼 스타일 개선 */
    div[data-testid="stSidebar"] button {
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        margin-bottom: 4px !important;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] button:hover {
        background-color: #334155 !important;
        border-color: #64748b !important;
    }
    
    /* 채팅 입력창 및 입력 위젯 스타일 보정 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput textarea {
        background-color: #1e293b !important;
        border: 2px solid #475569 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: #ffffff !important; }
    
    /* 대화상자(Dialog) 및 팝업 내부 시인성 강제 확보 */
    div[role="dialog"], div[data-testid="stModal"], div[data-testid="stDialog"], div[data-testid="stDialog"] div {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    div[data-testid="stDialog"] label, div[data-testid="stDialog"] p, div[data-testid="stDialog"] span {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }
    
    /* 컨테이너 및 익스팬더 테두리 명확화 */
    div[data-testid="stExpander"] { background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 10px !important; }
    div[data-testid="stExpander"] details summary { color: #ffffff !important; background-color: #334155 !important; }
</style>
"""
    else:
        theme_css = """
<style>
    [data-testid="stAppViewContainer"] { background-color: #ffffff !important; color: #0f172a !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: #f8fafc !important; border-right: 1px solid #cbd5e1 !important; }
    
    /* 사이드바 메뉴 버튼 스타일 개선 */
    div[data-testid="stSidebar"] button {
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        margin-bottom: 4px !important;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] button:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
    }
    
    /* 채팅 입력창 및 입력 위젯 스타일 보정 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput > div {
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: #0f172a !important; }
    
    /* 대화상자(Dialog) 및 팝업 내부 시인성 전면 확보 조치 */
    div[role="dialog"], div[data-testid="stModal"], div[data-testid="stDialog"], div[data-testid="stDialog"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-testid="stDialog"] label, div[data-testid="stDialog"] p, div[data-testid="stDialog"] span, div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2 {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDialog"] input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #cbd5e1 !important;
    }
    
    /* 라이트모드 컨테이너 및 익스팬더 경계선 명확화 */
    div[data-testid="stExpander"] { 
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important; 
        border-radius: 10px !important; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stExpander"] details summary { 
        color: #0f172a !important; 
        background-color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    .stMarkdown, .stText, label { color: #0f172a !important; }
</style>
"""
    st.markdown(base_css + theme_css, unsafe_allow_html=True)

# 튜닝된 UI 주입
apply_premium_ui_v2(st.session_state.dark_mode)

# --- [대화기록 내부 검색 팝업 창] ---
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

@dialog_decorator("대화 기록 검색 시스템", width="large")
def open_history_search_dialog():
    search_query = st.text_input("검색 키워드 입력", placeholder="예: 건폐율, 사선제한, 처인구...", key="dialog_history_search_input")
    query = search_query.strip().lower()

    if not st.session_state.chat_history:
        st.caption("저장된 이력이 존재하지 않습니다.")
        return

    results = []
    for idx, chat in enumerate(st.session_state.chat_history):
        searchable_text = chat.get("title", "") + " "
        for msg in chat.get("messages", []):
            searchable_text += msg.get("query", "") + " " + msg.get("response", "") + " "
        if not query or query in searchable_text.lower():
            results.append((idx, chat))

    st.caption(f"검색 결과: {len(results)}건" if query else "최근 대화방 목록")

    if not results:
        st.warning("일치하는 검색 결과가 없습니다.")
        return

    with st.container(height=400, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            preview = chat.get("messages", [])[0].get("query", "")[:60] + "..." if chat.get("messages") else ""
            
            with st.container():
                if st.button(f"{title[:25]}... ({time_str})", key=f"dialog_chat_{idx}", use_container_width=True):
                    st.session_state.selected_index = idx
                    st.session_state.current_page = "main"
                    st.rerun()
                st.caption(f"미리보기: {preview}")
                st.markdown("---")

# ==========================================
# 4. 구조화된 사이드바 시스템
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; font-weight:700; color:#4A90E2;'>Yong-In City</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:13px; color:#888; margin-top:-10px;'>건축 조례 지능형 분석 플랫폼</p>", unsafe_allow_html=True)
    st.divider()
    
    # [인증 인프라]
    with st.expander("담당자 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            auth_tabs = st.tabs(["로그인", "사용자 등록"])
            with auth_tabs[0]:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("로그인", use_container_width=True):
                    from storage import authenticate_user
                    if authenticate_user(login_id.strip(), login_pw.strip()):
                        st.session_state.user_id = login_id.strip()
                        st.session_state.chat_history = load_history(st.session_state.user_id)
                        st.toast(f"환영합니다, {st.session_state.user_id} 담당자님.", icon=None)
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            with auth_tabs[1]:
                reg_id = st.text_input("생성할 아이디", key="reg_id")
                reg_pw = st.text_input("생성할 비밀번호", type="password", key="reg_pw")
                if st.button("사용자 등록 신청", use_container_width=True):
                    from storage import check_id_exists, register_user
                    if check_id_exists(reg_id.strip()):
                        st.error("이미 사용 중인 아이디입니다.")
                    elif register_user(reg_id.strip(), reg_pw.strip()):
                        st.toast("사용자 등록이 완료되었습니다. 로그인해 주시기 바랍니다.", icon=None)
        else:
            st.markdown(f"접속 사용자: <span style='color:#4A90E2; font-weight:bold;'>{st.session_state.user_id} 담당자님</span>", unsafe_allow_html=True)
            if st.button("로그아웃", use_container_width=True, type="secondary"):
                st.session_state.user_id = "guest"
                st.session_state.chat_history = load_history("guest")
                st.session_state.selected_index = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # [내비게이션 모듈]
    st.subheader("메뉴 구성")
    if st.button("AI 건축 규제 검토", use_container_width=True): st.session_state.current_page = "main"; st.rerun()
    if st.button("민원 서식 자동 완성", use_container_width=True): st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("실무자 검증 Q&A", use_container_width=True): st.session_state.current_page = "qna"; st.rerun()
    if st.button("시스템 데이터 사이트맵", use_container_width=True): st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("다크 모드 적용", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.divider()
    
    # [대화 세션 히스토리 인터페이스]
    st.subheader("최근 대화 목록")
    c_new, c_src = st.columns(2)
    with c_new:
        if st.button("새 대화 시작", use_container_width=True, type="primary"):
            st.session_state.selected_index = None
            st.session_state.current_page = "main"
            st.rerun()
    with c_src:
        if st.button("대화 검색", use_container_width=True):
            open_history_search_dialog()

    history_container = st.container(height=400, border=True)
    with history_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                actual_index = len(st.session_state.chat_history) - 1 - i
                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]
                query_summary = chat.get("title", "대화 주제")[:14] + ".."
                
                # 중첩 컬럼 제약을 완전히 우회하여 구버전 호환성 확보 및 가독성 증대
                if st.button(f"{time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                    st.session_state.selected_index = actual_index
                    st.session_state.current_page = "main"
                    st.rerun()
        else:
            st.caption("기록된 이력이 없습니다.")

    if st.session_state.chat_history:
        if st.button("전체 대화 기록 삭제", type="secondary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.selected_index = None
            from storage import clear_history
            clear_history(st.session_state.user_id) 
            st.toast("모든 대화 기록이 정상적으로 삭제되었습니다.")
            st.rerun()


# ==========================================
# 5. 비즈니스 로직 및 화면 분기 (Main)
# ==========================================

# --- [화면 1] 메인 인공지능 분석 엔진 ---
if st.session_state.current_page == "main":
    st.markdown("## 건축 조례 및 규제 법령 분석 시스템")
    st.caption("용인시 자치조례 및 관련 상위 법령을 종합 분석하여 규제 사항 및 예외 조건을 도출합니다.")
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
        show_state_panel = st.toggle("컨텍스트 설정 패널 보기", value=True, key="use_state_panel")

    if show_state_panel:
        col_chat, col_state = st.columns([70, 30])
    else:
        col_chat = st.container()
        col_state = None

    with col_chat:
        chat_box = st.container(height=520, border=True)
        
        user_query = st.chat_input("조례 해석 또는 규제 검토 내용을 입력하세요. (예: 처인구 자연녹지지역 내 조례상 건폐율 특례 조항)")

        with chat_box:
            if current_chat is not None:
                st.info(f"이전 대화 기록 로드 완료: {current_chat.get('title', '이전 대화')}")
                for msg in current_chat.get("messages", []):
                    render_user_message(msg.get("query", ""))
                    render_ai_report(msg.get("response", ""))
                
                # 실무형 대화방 관리 기능 추가 (중첩 레이아웃 완전 배제형)
                st.markdown("---")
                if st.button("현재 활성화된 대화방 기록 삭제", use_container_width=True, type="secondary"):
                    st.session_state.chat_history.pop(st.session_state.selected_index)
                    from storage import save_history
                    save_history(st.session_state.chat_history, st.session_state.user_id)
                    st.session_state.selected_index = None
                    st.toast("현재 대화방이 안전하게 삭제되었습니다.")
                    st.rerun()
                    
                if st.button("현재 대화 종료 후 새 대화 시작", use_container_width=True):
                    st.session_state.selected_index = None
                    st.rerun()
            else:
                st.markdown("""
                <div style='text-align: center; padding: 40px 20px;'>
                    <h3 style='color: #4A90E2; font-weight:600; margin-bottom: 12px;'>검토할 건축 규제 내용을 입력해 주세요</h3>
                    <p style='color: #777; font-size: 14px;'>상위 건축법령 및 자치법규를 분석하여 명확한 유권해석 기준을 제시합니다.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 중첩 컬럼(st.columns) 에러 발생의 원인이 된 코드를 단일 직관 표기 형식으로 안전하게 우회 변경
                st.info("**검토 예시 1:** 용인시 기흥구 상업지역 용적률 완화 적용 범위")
                st.info("**검토 예시 2:** 대지 안의 공지 규정에 따른 이격거리 예외 기준")

        if user_query:
            render_user_message(user_query)
            with st.status("조례 및 법령 분석 중...", expanded=True) as status:
                try:
                    st.write("자치 조례 및 연계 법령 데이터 분석 중...")
                    response_text = handle_ai_analysis(user_query)

                    if st.session_state.chat_history:
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1

                    status.update(label="분석 완료", state="complete")
                    render_ai_report(response_text)
                    st.toast("건축 규제 검토 리포트 작성이 완료되었습니다.")
                except Exception as e:
                    status.update(label="시스템 오류 발생", state="error")
                    st.error(f"오류 메시지: {str(e)}")
            st.rerun()

    if show_state_panel and col_state is not None:
        with col_state:
            st.markdown("<p style='font-size:16px; font-weight:600; margin-bottom:2px;'>대지 매개변수 설정</p>", unsafe_allow_html=True)
            st.caption("규제 검토를 위한 대지별 속성 설정")

            with st.container(border=True):
                search_addr = st.text_input("대지 주소 입력", placeholder="예: 처인구 중부대로 1199", label_visibility="collapsed")
                if st.button("토지대장 데이터 연동", use_container_width=True):
                    if current_chat is not None:
                        mock_data = {"용도지역": "일반주거지역", "규제지역": "비행안전구역", "대지면적": "1,250㎡"}
                        current_chat["state"].update(mock_data)
                        save_history(st.session_state.chat_history, st.session_state.user_id)
                        st.rerun()

            if current_chat is not None:
                if not current_state:
                    df_state = pd.DataFrame(columns=["변수명", "속성값"])
                else:
                    df_state = pd.DataFrame(list(current_state.items()), columns=["변수명", "속성값"])

                edited_df = st.data_editor(
                    df_state,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key=f"state_editor_v2_{st.session_state.selected_index}"
                )

                new_state = {}
                for _, row in edited_df.iterrows():
                    k = str(row["변수명"]).strip() if pd.notna(row["변수명"]) else ""
                    v = str(row["속성값"]).strip() if pd.notna(row["속성값"]) else ""
                    if k and k != "nan": new_state[k] = v

                if new_state != current_state:
                    current_chat["state"] = new_state
                    save_history(st.session_state.chat_history, st.session_state.user_id)
                    st.rerun()
            else:
                st.info("활성화된 대화방이 없습니다. 왼쪽 메뉴에서 새 대화를 시작하거나 기존 대화 기록을 선택해 주세요.")
        
        
# --- [화면 2] 민원 양식 생성 자동화 모듈 ---
elif st.session_state.current_page == "doc_gen":
    st.markdown("## 행정 민원 서식 자동 완성 시스템")
    st.caption("신청하고자 하는 민원 내용을 입력하시면 표준 행정 서식 포맷으로 자동 변환합니다.")
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

    col1, col2 = st.columns(2)
    with col1:
        civil_type = st.selectbox("민원 분류 선택", list(required_docs.keys()))
    with col2:
        site_address = st.text_input("대상지 주소", placeholder="예: 경기도 용인시 처인구 역북동")

    civil_content = st.text_area("상세 신청 내용 입력", height=140, placeholder="서식에 반영할 상세 내용을 입력해 주세요.")

    if st.button("서식 생성", use_container_width=True, type="primary"):
        if not site_address or not civil_content:
            st.error("대상지 주소와 신청 내용을 모두 입력해 주세요.")
        else:
            with st.spinner("행정 서식 표준 포맷 적용 중..."):
                try:
                    result = generate_civil_document(civil_type, site_address, civil_content)
                    st.session_state.selected_index = None
                    st.toast("민원 서식 생성이 완료되었습니다.", icon=None)
                    
                    st.divider()
                    st.subheader("생성된 서식 미리보기")
                    st.markdown(f"<div style='padding:24px; border:2px solid #e2e8f0; border-radius:14px; background:rgba(120,120,120,0.03);'>{result}</div>", unsafe_allow_html=True)
                    
                    info_tabs = st.tabs(["필수 첨부 서류", "관할 행정 부서", "접수 및 처리 절차", "파일 다운로드"])
                    
                    with info_tabs[0]:
                        for doc in required_docs.get(civil_type, required_docs["기타"]):
                            st.write(f"• {doc}")
                    with info_tabs[1]:
                        dept = department_map.get(civil_type, "민원여권과")
                        st.info(f"용인시청 및 관할 구청 소관 부서: **{dept}**")
                    with info_tabs[2]:
                        st.markdown("""
                        1. **온라인 접수:** 정부24 또는 세움터 통합 접수
                        2. **오프라인 접수:** 용인시청 또는 구청 종합민원실 방문 접수
                        """)
                    with info_tabs[3]:
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
                except Exception as e:
                    st.error(f"예외 발생 알림: {str(e)}")

# --- [화면 3] 전문가 교차 검증 Q&A 게시판 ---
elif st.session_state.current_page == "qna":
    st.markdown("## 실무자 규제 해석 검증 게시판")
    st.caption("인허가 및 심의 과정에서 발생하는 모호한 사안에 대해 질문을 등록하고 해석을 공유하는 공간입니다.")
    st.divider()
    
    col1, col2 = st.columns([65, 35])
    with col1:
        st.subheader("질의응답 목록")
        if not st.session_state.qna_list:
            st.info("등록된 질의가 없습니다.")
        else:
            for i, q in enumerate(st.session_state.qna_list):
                badge = "접수 대기" if q['status'] == "대기중" else "검증 완료"
                with st.expander(f"[{badge}] {q['title']}"):
                    st.markdown(f"**질의 내용:** {q['content']}")
                    if q['status'] == "답변완료":
                        st.info(f"**검토 답변:** {q['answer']}")
    
    with col2:
        st.subheader("신규 질문 등록")
        with st.form("qna_form_v2", clear_on_submit=True):
            q_title = st.text_input("질문 제목")
            q_content = st.text_area("질문 내용")
            if st.form_submit_button("질문 등록", use_container_width=True):
                if q_title and q_content:
                    st.session_state.qna_list.append({"title": q_title, "content": q_content, "status": "대기중", "answer": ""})
                    st.toast("질문이 성공적으로 등록되었습니다.")
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해 주세요.")
        
        st.divider()
        with st.expander("관리자 검토 및 답변 등록"):
            admin_pw = st.text_input("관리자 인증 코드", type="password")
            if admin_pw == "2026":
                st.success("관리자 인증 완료")
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        answer_text = st.text_input(f"답변 내용 입력: {q['title']}", key=f"ans_{i}")
                        if st.button("답변 등록", key=f"btn_{i}"):
                            st.session_state.qna_list[i]['answer'] = answer_text
                            st.session_state.qna_list[i]['status'] = "답변완료"
                            st.rerun()

# --- [화면 4] 사이트맵 ---
elif st.session_state.current_page == "sitemap":

    st.markdown("## 플랫폼 구조 및 법률 아카이브 색인")
    st.caption("시스템이 분석하는 데이터 구조 및 연계 법률 색인 일람입니다.")
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
    background:#f8fafc;
    font-family: Pretendard, sans-serif;
}
.wrapper{
    background-color:#1e3a8a;
    padding:25px;
    border-radius:14px;
    box-shadow:0 4px 10px rgba(0,0,0,0.15);
}
.title{
    color:white;
    text-align:center;
    font-size:28px;
    font-weight:700;
    margin-bottom:25px;
}
.section{
    background:white;
    border-radius:10px;
    padding:18px;
    margin-bottom:18px;
}
.section-title{
    text-align:center;
    font-weight:700;
    color:#1e3a8a;
    font-size:18px;
    margin-bottom:15px;
}
.flex{
    display:flex;
    gap:12px;
    flex-wrap:wrap;
}
.card-blue{
    background:#f0f7ff;
    border:1px solid #cce3ff;
    border-radius:8px;
    padding:12px;
    flex:1;
    min-width:180px;
    text-align:center;
}
.card-gray{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:8px;
    padding:12px;
    flex:1;
    min-width:220px;
    text-align:center;
}
.card-green{
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    border-radius:8px;
    padding:12px;
    flex:1;
    min-width:220px;
    text-align:center;
}
.card-title-blue{
    font-weight:700;
    color:#0d47a1;
    font-size:15px;
}
.card-title-gray{
    font-weight:700;
    color:#334155;
    font-size:15px;
}
.card-title-green{
    font-weight:700;
    color:#166534;
    font-size:15px;
}
.card-desc{
    font-size:12px;
    color:#555;
    margin-top:5px;
}
</style>
</head>
<body>
<div class="wrapper">
    <div class="title">
        용인시 건축 조례 전문 해석 플랫폼 사이트맵
    </div>
    <div class="section">
        <div class="section-title">
            사용자 및 담당자 서비스 (UI)
        </div>
        <div class="flex">
            <div class="card-blue">
                <div class="card-title-blue">
                    건축 규제 검토
                </div>
                <div class="card-desc">
                    법령 시맨틱 분석 질의응답
                </div>
            </div>
            <div class="card-blue">
                <div class="card-title-blue">
                    민원 서식 빌더
                </div>
                <div class="card-desc">
                    행정 서류 자동 완성
                </div>
            </div>
            <div class="card-blue">
                <div class="card-title-blue">
                    실무 Q&A 게시판
                </div>
                <div class="card-desc">
                    질의 및 검토 답변 공유
                </div>
            </div>
            <div class="card-blue">
                <div class="card-title-blue">
                    컨텍스트 관리
                </div>
                <div class="card-desc">
                    대지 상태 및 파라미터 제어
                </div>
            </div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">
            AI 및 백엔드 통합 엔진
        </div>
        <div class="flex">
            <div class="card-gray">
                <div class="card-title-gray">
                    LLM 분석 엔진
                </div>
                <div class="card-desc">
                    handle_ai_analysis 모듈
                </div>
            </div>
            <div class="card-gray">
                <div class="card-title-gray">
                    법률 레이어링 구조화
                </div>
                <div class="card-desc">
                    규제 조항 필터링 및 매핑
                </div>
            </div>
            <div class="card-gray">
                <div class="card-title-gray">
                    인증 및 세션 관리자
                </div>
                <div class="card-desc">
                    대화 이력 보존 및 상태 동기화
                </div>
            </div>
        </div>
    </div>
    <div class="section">
        <div class="section-title">
            데이터베이스 및 외부 연계 체계
        </div>
        <div class="flex">
            <div class="card-green">
                <div class="card-title-green">
                    지역 자치법규 DB
                </div>
                <div class="card-desc">
                    용인시/경기도 지역 조례
                </div>
            </div>
            <div class="card-green">
                <div class="card-title-green">
                    상위 차용 법령 DB
                </div>
                <div class="card-desc">
                    국가 법령 인덱스
                </div>
            </div>
            <div class="card-green">
                <div class="card-title-green">
                    내부 시스템 로컬 DB
                </div>
                <div class="card-desc">
                    사용자 데이터 및 문서 스키마
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""

    components.html(
        architecture_html,
        height=900,
        scrolling=True
    )

    st.divider()
    
    tabs = st.tabs(["1. 자치 조례 일람", "2. 상위 법령 일람", "3. 조례 인용 법규 (44개)", "4. 법령 인용 법규 (61개)"])
    
    with tabs[0]:
        df_ord = pd.DataFrame([
            ["경기도", "경기도 건축 조례"],
            ["경기도", "경기도 건축기본조례"],
            ["경기도", "경기도 건축물 미술작품 설치 및 관리에 관한 조례"],
            ["경기도", "경기도 건축물관리 조례"],
            ["용인시", "용인시 건축 조례"],
            ["용인시", "용인시 건축물관리 조례"],
            ["용인시", "용인시 도시계획 조례"]
        ], columns=["소관지자체", "지방자치조례 정식명칭"])
        st.dataframe(df_ord, hide_index=True, use_container_width=True)

    with tabs[1]:
        df_law = pd.DataFrame([
            ["건축법"], ["건축기본법"], ["문화예술진흥법"], ["건축물관리법"], ["국토의 계획 및 이용에 관한 법률"],
            ["건축법 시행령"], ["건축기본법 시행령"], ["문화예술진흥법 시행령"], ["건축물관리법 시행령"], ["국토의 계획 및 이용에 관한 법률 시행령"],
            ["건축법 시행규칙"], ["건축물관리법 시행규칙"], ["국토의 계획 및 이용에 관한 법률 시행규칙"]
        ], columns=["대한민국 헌정 법령 및 시행령/시행규칙 명칭"])
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
        df_ord_borrow = pd.DataFrame({"연계 및 인용 조례의 차용법규명": ord_borrow_data})
        st.dataframe(df_ord_borrow, hide_index=True, use_container_width=True)

    with tabs[3]:
        law_borrow_data = [
            "건설기술 진흥법", "건설산업기본법", "건축기본법", "건축법", "건축사법", 
            "경관법", "고등교육법", "공간정보의 구축 및 관리 등에 관한 법률", 
            "공공기관의 운영에 관한 법률", "공공주택 특별법", "공동주택관리법", 
            "공유재산 및 물품 관리법", "공익사업을 위한 토지 등의 취득 및 보상에 관한 법률", 
            "관광진흥법", "국가기술자격법", "국가유산기본법", "국유재산법", 
            "국토안전관리원법", "국토의 계획 및 이용에 관한 법률", "기술사법", 
            "녹색건축물 조성 지원법", "농어촌정비법", "농지법", "도로법", 
            "도시 및 주거환경정비법", "도시개발법", "도시공원 및 녹지 등에 관한 법률", 
            "도시교통정비 촉진법", "도시재생 활성화 및 지원에 관한 특별법", "문화예술진흥법", 
            "문화유산의 보존 및 활용에 관한 법률", "민법", "빈집 및 소규모주택 정비에 관한 특례법", 
            "사도법", "산림자원의 조성 및 관리에 관한 법률", "산업입지 및 개발에 관한 법률", 
            "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "소방시설 설치 및 관리에 관한 법률", 
            "수도권정비계획법", "수도법", "시설물의 안전 및 유지관리에 관한 특별법", 
            "영유아보육법", "자연공원법", "자연유산의 보존 및 활용에 관한 법률", 
            "자연재해대책법", "전자정부법", "주차장법", "주택법", "지방공기업법", 
            "집합건물의 소유 및 관리에 관한 법률", "택지개발촉진법", "토지이용규제 기본법", 
            "하수도법", "하천법", "한국토지주택공사법", "행정대집행법", 
            "건설기술 진흥법 시행령", "건축법 시행령", "국토의 계획 및 이용에 관한 법률 시행령", 
            "수산자원관리법 시행령"
        ]
        df_law_borrow = pd.DataFrame({"상위 법령 기반 교차 준용/차용법규명": law_borrow_data})
        st.dataframe(df_law_borrow, hide_index=True, use_container_width=True)

}
