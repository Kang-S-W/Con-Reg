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
import textwrap  # ✅ HTML 들여쓰기 제거를 위한 모듈 추가

# ==========================================
# 1. 페이지 설정 (최상단 고정 - 이모티콘 제거 및 타이틀 변경)
# ==========================================
st.set_page_config(
    page_title="용인시 건축법규 지원엔진", 
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
# 3. 프리미엄 인핸스드 테마 및 채팅창 확장 CSS (윤곽선 선명화 및 경계선 분리)
# ==========================================
def apply_premium_ui_v2(is_dark):
    base_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    
    /* 아이콘 깨짐 방지 강제 복구 */
    span[class*="material-symbols"], span[class*="material-icons"], i[class*="material"],
    .material-icons, .material-symbols-rounded, .material-symbols-outlined,
    [data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"],
    button[kind="header"] span, button[kind="header"] i {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-weight: normal !important;
        font-style: normal !important;
    }
    
    /* 탭 메뉴 스타일 고도화 */
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
    [data-testid="stAppViewContainer"] { background-color: #1a1a1a !important; color: #f5f5f5 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: #111111 !important; border-right: 1px solid #444444 !important; }
    
    /* 채팅 입력창 크기 대폭 확장 및 테두리 시각화 강화 (다크) - 조금 더 선명하게 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput textarea {
        background-color: #242424 !important;
        border: 2px solid #667085 !important;
        border-radius: 14px !important;
        padding: 8px 12px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, .stChatInput textarea:focus {
        border-color: #6ba4e8 !important;
        box-shadow: 0 0 0 3px rgba(107, 164, 232, 0.25) !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: #ffffff !important; font-size: 15px !important; }
    
    /* 에디터 및 컨테이너 개선 */
    div[data-testid="stExpander"] { background-color: #222222 !important; border: 1px solid #444444 !important; border-radius: 12px !important; }
    div[data-testid="stExpander"] details summary { color: #f5f5f5 !important; background-color: #2a2a2a !important; }
    div[data-testid="stExpander"] details > div { background-color: #222222 !important; color: #f5f5f5 !important; }
    
    /* 컨텍스트 관리 왼쪽 선 (구분선 추가) */
    div[data-testid="column"]:has(#context-panel) {
        border-left: 2px solid #556075 !important;
        padding-left: 20px !important;
    }
</style>
"""
    else:
        theme_css = """
<style>
    [data-testid="stAppViewContainer"] { background-color: #fcfcfc !important; color: #1e293b !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: #f1f5f9 !important; border-right: 1px solid #cbd5e1 !important; }
    
    /* 채팅 입력창 크기 대폭 확장 및 테두리 시각화 강화 (라이트) - 조금 더 선명하게 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stChatInput > div {
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
        border-radius: 14px !important;
        padding: 8px 12px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, .stChatInput:focus-within {
        border-color: #4a90e2 !important;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2) !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, .stChatInput textarea { color: #0f172a !important; font-size: 15px !important; }
    
    /* 라이트모드 가시성 전면 확보 조치 */
    div[data-testid="stExpander"], div[data-testid="stExpander"] > details { 
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important; 
        border-radius: 12px !important; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    div[data-testid="stExpander"] details summary, 
    div[data-testid="stExpander"] details summary p { 
        color: #111111 !important; 
        background-color: #f8fafc !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] details > div { background-color: #ffffff !important; color: #111111 !important; }
    .stMarkdown, .stText, label { color: #1e293b !important; }
    
    /* 컨텍스트 관리 왼쪽 선 (구분선 추가) */
    div[data-testid="column"]:has(#context-panel) {
        border-left: 2px solid #94a3b8 !important;
        padding-left: 20px !important;
    }
</style>
"""
    st.markdown(base_css + theme_css, unsafe_allow_html=True)

# 튜닝된 UI 주입
apply_premium_ui_v2(st.session_state.dark_mode)

# --- [대화기록 내부 검색 팝업 창] ---
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

# 이모티콘 제거
@dialog_decorator("대화기록 검색 시스템", width="large")
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

    st.caption(f"검색 매칭: {len(results)}건" if query else "최근 생성 대화방")

    if not results:
        st.warning("일치하는 검색 결과가 없습니다.")
        return

    with st.container(height=400, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            preview = chat.get("messages", [])[0].get("query", "")[:60] + "..." if chat.get("messages") else ""
            
            with st.container():
                # 이모티콘 제거
                if st.button(f"{title[:25]}... \n\n {time_str}", key=f"dialog_chat_{idx}", use_container_width=True):
                    st.session_state.selected_index = idx
                    st.session_state.current_page = "main"
                    st.rerun()
                st.caption(f"미리보기: {preview}")
                st.markdown("---")

# ==========================================
# 4. 구조화된 사이드바 시스템 (로고 삽입, 타이틀 변경, 이모티콘 제거)
# ==========================================
with st.sidebar:
    # 용인시 로고 삽입 및 타이틀 변경
    logo_col1, logo_col2, logo_col3 = st.columns([1, 3, 1])
    with logo_col2:
        st.image("image_3d6ddc.png", use_container_width=True)
    st.markdown("<h2 style='text-align:center; font-weight:700; color:#4A90E2; font-size:22px; margin-top:10px;'>용인시 건축법규 지원엔진</h2>", unsafe_allow_html=True)
    st.divider()
    
    # [인증 인프라] (이모티콘 제거)
    with st.expander("실무자 권한 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            auth_tabs = st.tabs(["로그인", "계정 생성"])
            with auth_tabs[0]:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("패스워드", type="password", key="login_pw")
                if st.button("보안인증 로그인", use_container_width=True):
                    from storage import authenticate_user
                    if authenticate_user(login_id.strip(), login_pw.strip()):
                        st.session_state.user_id = login_id.strip()
                        st.session_state.chat_history = load_history(st.session_state.user_id)
                        # 이모티콘 제거
                        st.toast(f"환영합니다, {st.session_state.user_id} 주무관님.")
                        st.rerun()
                    else:
                        st.error("인증 자격 증명이 불일치합니다.")
            with auth_tabs[1]:
                reg_id = st.text_input("신규 생성 아이디", key="reg_id")
                reg_pw = st.text_input("신규 패스워드", type="password", key="reg_pw")
                if st.button("권한 신청 및 생성", use_container_width=True):
                    from storage import check_id_exists, register_user
                    if check_id_exists(reg_id.strip()):
                        st.error("이미 사용 중인 식별자입니다.")
                    elif register_user(reg_id.strip(), reg_pw.strip()):
                        # 이모티콘 제거
                        st.toast("사용자 계정이 생성되었습니다. 로그인을 시도하세요.")
        else:
            st.markdown(f"접속 세션: <span style='color:#4A90E2; font-weight:bold;'>{st.session_state.user_id}</span>", unsafe_allow_html=True)
            if st.button("시스템 로그아웃", use_container_width=True, type="secondary"):
                st.session_state.user_id = "guest"
                st.session_state.chat_history = load_history("guest")
                st.session_state.selected_index = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # [내비게이션 모듈 - 직관성 개선] (이모티콘 제거)
    st.subheader("핵심 메뉴")
    if st.button("메인 엔진 (AI 심층 질의)", use_container_width=True): st.session_state.current_page = "main"; st.rerun()
    if st.button("민원 서식 행정 자동완성", use_container_width=True): st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("실무 교차 검증 Q&A", use_container_width=True): st.session_state.current_page = "qna"; st.rerun()
    if st.button("플랫폼 데이터 사이트맵", use_container_width=True): st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("다크 테마 적용", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.divider()
    
    # [대화 세션 히스토리 인터페이스] (이모티콘 제거)
    st.subheader("최근 대화 아카이브")
    c_new, c_src = st.columns(2)
    with c_new:
        if st.button("새 대화방", use_container_width=True, type="primary"):
            st.session_state.selected_index = None
            st.session_state.current_page = "main"
            st.rerun()
    with c_src:
        if st.button("인덱스 검색", use_container_width=True):
            open_history_search_dialog()

    history_container = st.container(height=400, border=False)
    with history_container:
        if st.session_state.chat_history:
            # 기존 대화에 고유 id가 없으면 한 번만 부여
            id_changed = False
            for chat in st.session_state.chat_history:
                if "id" not in chat:
                    chat["id"] = str(uuid.uuid4())
                    id_changed = True

            if id_changed:
                save_history(st.session_state.chat_history, st.session_state.user_id)

            history_items = list(enumerate(st.session_state.chat_history))
            history_items = sorted(
                history_items,
                key=lambda item: (
                    item[1].get("pinned", False),
                    item[1].get("updated_at", item[1].get("created_at", ""))
                ),
                reverse=True
            )

            for actual_index, chat in history_items:
                chat_id = chat["id"]

                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]

                title = chat.get("title", "질의 데이터")
                is_pinned = chat.get("pinned", False)

                pin_mark = "[고정] " if is_pinned else ""
                query_summary = title[:11] + ".." if len(title) > 11 else title

                col_btn, col_menu = st.columns([82, 18])

                with col_btn:
                    # 이모티콘 제거
                    if st.button(
                        f"{pin_mark}{time_str} | {query_summary}",
                        key=f"hist_btn_{chat_id}",
                        use_container_width=True
                    ):
                        st.session_state.selected_index = actual_index
                        st.session_state.current_page = "main"
                        st.rerun()

                with col_menu:
                    with st.popover(
                        "⋯", 
                        use_container_width=True, 
                        help=f"대화 관리 {chat_id}"
                    ):
                        new_title = st.text_input(
                            "이름 변경", 
                            value=title, 
                            key=f"sidebar_rename_title_{chat_id}"
                        )
                        if st.button(
                            "이름 저장", 
                            key=f"sidebar_save_title_{chat_id}", 
                            use_container_width=True
                        ):
                            st.session_state.chat_history[actual_index]["title"] = new_title.strip() or "질의 데이터"
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                            st.toast("대화 이름이 변경되었습니다.")
                            st.rerun()

                        pin_label = "고정 해제" if is_pinned else "핀 고정"
                        if st.button(
                            pin_label, 
                            key=f"sidebar_toggle_pin_{chat_id}", 
                            use_container_width=True
                        ):
                            st.session_state.chat_history[actual_index]["pinned"] = not is_pinned
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                            st.toast("핀 상태가 변경되었습니다.")
                            st.rerun()

                        if st.button(
                            "삭제", 
                            key=f"sidebar_delete_chat_{chat_id}", 
                            use_container_width=True
                        ):
                            st.session_state.chat_history.pop(actual_index)
                            if st.session_state.selected_index == actual_index:
                                st.session_state.selected_index = None
                            save_history(st.session_state.chat_history, st.session_state.user_id)
                            st.toast("대화가 삭제되었습니다.")
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.chat_history:
            if st.button("전체 세션 아카이브 초기화", use_container_width=True, type="secondary"):
                st.session_state.chat_history = []
                save_history([], st.session_state.user_id)
                st.session_state.selected_index = None
                st.rerun()


# ==========================================
# 5. 메인 앱 레이아웃 및 페이지 라우팅
# ==========================================

# --- 🏠 [화면 1] 메인 대화 엔진 --- (이모티콘 제거)
if st.session_state.current_page == "main":
    
    st.markdown("""
        <div style='text-align: center; padding: 60px 20px;'>
            <h1 style='color: #4A90E2; font-weight:800; font-size: 38px; margin-bottom: 10px; letter-spacing:-1px;'>건축 조례 및 규제 법령 해석 AI 시스템</h1>
            <h3 style='color: #4A90E2; font-weight:600; margin-bottom: 12px;'>질의할 건축 규제를 기술해 주세요</h3>
            <p style='color: #777; font-size: 14px;'>상위 건축법령 및 경기도/용인시 자치법규 데이터베이스를 교차 매핑하여 정확한 행정 유권해석 룰셋을 출력합니다.</p>
        </div>
    """, unsafe_allow_html=True)

    c_info1, c_info2 = st.columns(2)
    with c_info1:
        st.info("**질의 표준:** 용인시 기흥구 상업지역 용적률 인센티브 완화 적용 범위")
    with c_info2:
        st.info("**질의 표준:** 대지안의 공지 규정 관련 용인시 조례상 이격거리 예외 기준")

    # 선택된 대화 표시 로직
    is_new_chat = st.session_state.selected_index is None
    show_state_panel = False

    if not is_new_chat and st.session_state.selected_index < len(st.session_state.chat_history):
        show_state_panel = True
        chat_data = st.session_state.chat_history[st.session_state.selected_index]
        if "messages" not in chat_data:
            chat_data["messages"] = [{"query": chat_data.get("query", ""), "response": chat_data.get("response", "")}]
            save_history(st.session_state.chat_history, st.session_state.user_id)

        col_top_left, col_top_right = st.columns([4, 1])
        with col_top_left:
            st.success(f"과거 분석 히스토리 로드 완료: {chat_data.get('title', '질의 데이터')}")
        with col_top_right:
            if st.button("현재 히스토리 언로드 및 새 질의 시작", use_container_width=True):
                st.session_state.selected_index = None
                st.rerun()
                
        # 대화 내용 렌더링
        for msg in chat_data["messages"]:
            render_user_message(msg["query"])
            render_ai_report(msg["response"])
            
    # CSS: 컨텍스트 관리 영역 경계선 삽입을 위한 HTML 앵커 추가
    col_chat, col_state = None, None
    if show_state_panel:
        col_chat, col_state = st.columns([73, 27])
    
    with st.container():
        user_query = st.chat_input("용인시 건축 조례 및 상위 법령에 대해 입력해 주세요 (예: 제2종일반주거지역 건폐율)")
        
        if user_query:
            render_user_message(user_query)
            with st.status("분석 엔진 작동 중 (시맨틱 법률 조항 매핑)...", expanded=True) as status:
                try:
                    st.write("실시간 조례 데이터셋 및 연계 차용법령 가중치 분석 중...")
                    response_text = handle_ai_analysis(user_query)
                    
                    if is_new_chat:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        title_summary = user_query[:15] + ("..." if len(user_query)>15 else "")
                        st.session_state.chat_history.append({
                            "id": str(uuid.uuid4()),
                            "title": title_summary,
                            "created_at": timestamp,
                            "updated_at": timestamp,
                            "messages": [{"query": user_query, "response": response_text}],
                            "context_state": {}
                        })
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1
                    else:
                        st.session_state.chat_history[st.session_state.selected_index]["messages"].append(
                            {"query": user_query, "response": response_text}
                        )
                        st.session_state.chat_history[st.session_state.selected_index]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    save_history(st.session_state.chat_history, st.session_state.user_id)
                    status.update(label="해석 도출 완료", state="complete")
                    render_ai_report(response_text)
                    st.toast("AI 규제 검토 리포트 작성이 완료되었습니다.")
                except Exception as e:
                    status.update(label="런타임 인터럽트 감지", state="error")
                    st.error(f"오류 피드백: {str(e)}")
            st.rerun()
            
    # 컨텍스트 관리 패널 (사이드 컬럼) - 이모티콘 제거
    if show_state_panel and col_state is not None:
        with col_state:
            st.markdown("<div id='context-panel'></div>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:16px; font-weight:600; margin-bottom:2px;'>컨텍스트 관리</p>", unsafe_allow_html=True)
            st.caption("AI 해석에 주입될 대지 관련 동적 변수셋")
            with st.container(border=True):
                search_addr = st.text_input("대지 주소 동기화", placeholder="예: 처인구 역북동")
                zone_type = st.selectbox("지역 지구 지정", ["미지정", "제1종전용주거지역", "제2종전용주거지역", "제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역", "준주거지역", "상업지역", "공업지역", "녹지지역"])
                area_size = st.number_input("건축 제원 입력 (대지면적 ㎡)", min_value=0, value=0, step=10)
                custom_memo = st.text_area("사용자 커스텀 메모", height=80, placeholder="특이사항 메모")
                if st.button("분석 엔진에 동기화 적용", use_container_width=True):
                    if "context_state" not in chat_data: chat_data["context_state"] = {}
                    chat_data["context_state"]["addr"] = search_addr
                    chat_data["context_state"]["zone"] = zone_type
                    chat_data["context_state"]["area"] = area_size
                    chat_data["context_state"]["memo"] = custom_memo
                    save_history(st.session_state.chat_history, st.session_state.user_id)
                    st.success("시스템 적용 완료")

# --- 📝 [화면 2] 서식 자동완성 --- (이모티콘 제거)
elif st.session_state.current_page == "doc_gen":
    st.markdown("## 민원 서식 행정 자동완성 시스템")
    st.caption("AI 해석 결과를 바탕으로 행정 표준 민원서 및 신청서를 자동 빌드합니다.")
    st.divider()
    
    required_docs = {
        "건축허가 관련": ["건축계획서", "배치도", "평면도", "소유권 증빙서류"],
        "건축선 문의": ["지적도", "현황측량성과도", "건축선 지정 관련 사유서"],
        "일조권 민원": ["일조 분석 보고서", "단면도", "피해 현황 사진"],
        "불법건축물 신고": ["현장 사진", "위반 위치도", "신고인 신분증 사본"],
        "용도변경 문의": ["기존 건축물대장", "변경 전후 평면도", "용도변경 동의서(필요시)"],
        "주차장 기준 문의": ["주차장 배치도", "건축물대장", "차량 이동 동선도"],
        "건축물 해석 문의": ["질의 대상 도면", "관련 법규 검토서"],
        "기타": ["민원 신청서", "관련 도면 및 증빙 서류"]
    }

    dept_mapping = {
        "건축허가 관련": "건축허가과", "건축선 문의": "건축과", "일조권 민원": "건축과",
        "불법건축물 신고": "건축과", "용도변경 문의": "건축허가과", "주차장 기준 문의": "교통정책과",
        "건축물 해석 문의": "건축과", "기타": "민원여권과"
    }

    col1, col2 = st.columns(2)
    with col1:
        civil_type = st.selectbox("처리 목적 분류 선택", list(required_docs.keys()))
    with col2:
        site_address = st.text_input("관할지 주소 정보", placeholder="예: 경기도 용인시 처인구 역북동")
        
    civil_content = st.text_area("발생 원인 및 요청 서사 기술", height=140, placeholder="양식에 맞춰 구체화할 내용을 입력해 주세요.")
    
    if st.button("AI 행정 양식 빌드 수행", use_container_width=True, type="primary"):
        if not site_address or not civil_content:
            st.error("행정 대상 주소 및 서사 내용을 공백 없이 채워주십시오.")
        else:
            with st.spinner("행정 처리 표준 스키마 적용 중..."):
                try:
                    result = generate_civil_document(civil_type, site_address, civil_content)
                    st.session_state.selected_index = None
                    st.toast("민원 양식 생성이 완료되었습니다.")
                    
                    st.divider()
                    st.subheader("빌드 완료된 서식 리포트")
                    st.markdown(f"<div style='padding:24px; border:2px solid #e2e8f0; border-radius:14px; background:rgba(120,120,120,0.03);'>{result}</div>", unsafe_allow_html=True)
                    
                    info_tabs = st.tabs(["필수 증빙 목록", "관할 행정 부서", "접수 이행 프로세스", "파일 내보내기"])
                    
                    with info_tabs[0]:
                        for doc in required_docs.get(civil_type, required_docs["기타"]):
                            st.write(f"• {doc}")
                            
                    with info_tabs[1]:
                        dept = dept_mapping.get(civil_type, "민원여권과")
                        st.write(f"본 민원은 용인시청 **{dept}**로 배정될 확률이 높습니다.")
                        
                    with info_tabs[2]:
                        st.write("1. 작성된 양식 출력 및 날인\n2. 필수 증빙 서류 취합\n3. 용인시청 민원실 또는 온라인 민원24 접수\n4. 담당 부서 배정 및 검토\n5. 결과 통보 (통상 7~14일 소요)")
                        
                    with info_tabs[3]:
                        bio = io.BytesIO()
                        document = Document()
                        document.add_heading(f"[{civil_type}] 민원 신청서", level=1)
                        clean_text = textwrap.dedent(result.replace("<br>", "\n")).strip()
                        document.add_paragraph(clean_text)
                        document.save(bio)
                        
                        st.download_button(
                            label="표준 워드 파일(DOCX) 다운로드",
                            data=bio.getvalue(),
                            file_name=f"용인시_민원양식_{datetime.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"양식 빌드 중 오류 발생: {e}")

# --- 💡 [화면 3] Q&A 게시판 --- (이모티콘 제거)
elif st.session_state.current_page == "qna":
    st.markdown("## 실무 현장 질의응답 (Q&A)")
    st.caption("주무관 및 실무자 간의 교차 검증 및 지식 아카이브 공간입니다.")
    st.divider()

    if not st.session_state.qna_list:
        st.info("현재 등록된 실무 질의가 없습니다.")
    else:
        for q in reversed(st.session_state.qna_list):
            with st.expander(f"[{q['status']}] {q['title']}"):
                st.write(f"**작성자:** {q['author']} | **일시:** {q['date']}")
                st.write(f"**질의 내용:**\n{q['content']}")
                if q['answer']:
                    st.markdown("---")
                    st.write(f"**✅ 답변 내용:**\n{q['answer']}")
                    
    st.divider()
    st.subheader("신규 유권해석 케이스 발행")
    q_title = st.text_input("질의 요약 제목")
    q_content = st.text_area("상세 질의 내용")
    if st.button("질의 등록", use_container_width=True):
        if q_title and q_content:
            st.session_state.qna_list.append({
                "title": q_title, "author": st.session_state.user_id, 
                "date": datetime.now().strftime("%Y-%m-%d"), 
                "content": q_content, "status": "대기중", "answer": ""
            })
            st.toast("신규 안건이 성공적으로 피드에 배포되었습니다.")
            st.rerun()
        else:
            st.error("필수 항목 누락")
            
    st.divider()
    with st.expander("조정관 승인 영역"):
        admin_pw = st.text_input("조정관 PIN 코드", type="password")
        if admin_pw == "2026":
            st.success("접근 권한 활성화")
            for i, q in enumerate(st.session_state.qna_list):
                if q['status'] == "대기중":
                    answer_text = st.text_input(f"해석 피드백 기입: {q['title']}", key=f"ans_{i}")
                    if st.button("해석 확정 배포", key=f"btn_{i}"):
                        st.session_state.qna_list[i]['answer'] = answer_text
                        st.session_state.qna_list[i]['status'] = "답변완료"
                        st.rerun()

# --- 🗺️ [화면 4] 사이트맵 --- (이모티콘 제거)
elif st.session_state.current_page == "sitemap":
    st.markdown("## 플랫폼 구조 및 법률 아카이브 트리")
    st.caption("플랫폼 엔진이 검사하는 데이터 구조의 설계 색인 일람입니다.")
    st.divider()
    
    architecture_html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8">
    <style>
        body{ margin:0; padding:20px; background:#f8fafc; font-family: Pretendard, sans-serif; }
        .wrapper{ background-color:#1e3a8a; padding:25px; border-radius:14px; box-shadow:0 4px 10px rgba(0,0,0,0.15); }
        .title{ color:white; text-align:center; font-size:28px; font-weight:700; margin-bottom:25px; }
        .section{ background:white; border-radius:10px; padding:18px; margin-bottom:18px; }
        .section-title{ text-align:center; font-size:20px; font-weight:700; color:#1e3a8a; margin-bottom:15px; border-bottom:2px solid #e2e8f0; padding-bottom:10px; }
        .flex{ display:flex; justify-content:space-around; align-items:flex-start; flex-wrap:wrap; gap:15px; }
        .card, .card-blue, .card-green, .card-orange{ background:#f1f5f9; border-radius:8px; padding:15px; width:28%; box-shadow:0 2px 5px rgba(0,0,0,0.05); text-align:center; border:1px solid #cbd5e1; }
        .card-blue{ border-left:5px solid #3b82f6; }
        .card-green{ border-left:5px solid #10b981; }
        .card-orange{ border-left:5px solid #f59e0b; }
        .card-title, .card-title-blue, .card-title-green, .card-title-orange{ font-weight:700; font-size:16px; margin-bottom:10px; }
        .card-title-blue{ color:#3b82f6; }
        .card-title-green{ color:#10b981; }
        .card-title-orange{ color:#f59e0b; }
        .card-desc{ font-size:13px; color:#475569; line-height:1.4; }
        .arrow{ text-align:center; color:white; font-size:24px; margin:5px 0; }
    </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="title">용인시 건축법규 지원엔진 아키텍처</div>
            
            <div class="section">
                <div class="section-title">프론트엔드 (UI/UX)</div>
                <div class="flex">
                    <div class="card-blue">
                        <div class="card-title-blue">메인 챗봇 인터페이스</div>
                        <div class="card-desc">사용자 질의 입력 및 AI 답변 렌더링</div>
                    </div>
                    <div class="card-blue">
                        <div class="card-title-blue">사이드바 제어 패널</div>
                        <div class="card-desc">인증, 메뉴 이동, 대화 이력 관리</div>
                    </div>
                    <div class="card-blue">
                        <div class="card-title-blue">상태 및 옵션 관리</div>
                        <div class="card-desc">다크모드, 컨텍스트 상태 시각화</div>
                    </div>
                </div>
            </div>
            
            <div class="arrow">↓</div>
            
            <div class="section">
                <div class="section-title">백엔드 및 AI 엔진 로직</div>
                <div class="flex">
                    <div class="card-orange">
                        <div class="card-title-orange">Semantic 매핑 모듈</div>
                        <div class="card-desc">사용자 질의에서 법률적 의도 및 키워드 추출</div>
                    </div>
                    <div class="card-orange">
                        <div class="card-title-orange">DB 검색 및 스니펫 알고리즘</div>
                        <div class="card-desc">TF-IDF 기반 조항 가중치 평가 및 발췌</div>
                    </div>
                    <div class="card-orange">
                        <div class="card-title-orange">LLM 프롬프트 엔지니어링</div>
                        <div class="card-desc">Gemini API 연동, 컨텍스트 주입 및 상태 동기화</div>
                    </div>
                </div>
            </div>
            
            <div class="arrow">↓</div>
            
            <div class="section">
                <div class="section-title">데이터베이스 및 외부 연계 체계</div>
                <div class="flex">
                    <div class="card-green">
                        <div class="card-title-green">지역 자치법규 DB</div>
                        <div class="card-desc">용인시/경기도 지역 조례</div>
                    </div>
                    <div class="card-green">
                        <div class="card-title-green">상위 차용 법령 DB</div>
                        <div class="card-desc">국가 법령 인덱스</div>
                    </div>
                    <div class="card-green">
                        <div class="card-title-green">내부 시스템 로컬 DB</div>
                        <div class="card-desc">사용자 데이터 및 문서 스키마</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    # ✅ markdown 대신 html component 사용
    components.html(
        architecture_html,
        height=900,
        scrolling=True
    )

    st.divider()
    
    # 조례, 법령, 조례의 차용법규(44개), 법령의 차용법규(61개) 전수 매핑 탭 구조 (이모티콘 제거)
    tabs = st.tabs(["1. 기본 조례 일람", "2. 상위 기본 법령 일람", "3. 조례의 차용 법규 (전체 44개)", "4. 법령의 차용 법규 (전체 61개)"])
    
    # 탭 1: 조례 리스트
    with tabs[0]:
        df_ord = pd.DataFrame([
            ["경기도", "경기도 건축 조례"], ["경기도", "경기도 건축기본조례"],
            ["경기도", "경기도 건축물 미술작품 설치 및 관리에 관한 조례"], ["경기도", "경기도 건축물관리 조례"],
            ["용인시", "용인시 건축 조례"], ["용인시", "용인시 건축물관리 조례"],
            ["용인시", "용인시 공공디자인 진흥 조례"], ["용인시", "용인시 도시계획 조례"],
            ["용인시", "용인시 주차장 설치 및 관리 조례"]
        ], columns=["소관", "법규명"])
        st.dataframe(df_ord, hide_index=True, use_container_width=True)

    # 탭 2: 법령 리스트
    with tabs[1]:
        df_stat = pd.DataFrame([
            ["국토교통부", "건축법"], ["국토교통부", "건축법 시행령"], ["국토교통부", "건축법 시행규칙"],
            ["국토교통부", "국토의 계획 및 이용에 관한 법률"], ["국토교통부", "국토의 계획 및 이용에 관한 법률 시행령"],
            ["국토교통부", "건축기본법"], ["국토교통부", "건축물관리법"], ["국토교통부", "주차장법"]
        ], columns=["소관부처", "법규명"])
        st.dataframe(df_stat, hide_index=True, use_container_width=True)

    # 탭 3: 조례의 차용 법규 리스트 (제공해주신 44개 항목 정밀 가공 매핑)
    with tabs[2]:
        ord_borrow_data = [
            "가축분뇨의 관리 및 이용에 관한 법률", "건축법", "건축법 시행규칙", "건축법 시행령", "건축사법",
            "경관법", "공간정보의 구축 및 관리 등에 관한 법률", "공공주택 특별법 시행령", "공유재산 및 물품 관리법 시행령",
            "국가유산기본법", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령", "녹색건축물 조성 지원법",
            "농어촌정비법", "농지법", "도시개발법", "도시교통정비 촉진법", "도시재생 활성화 및 지원에 관한 특별법",
            "민법", "부동산 가격공시에 관한 법률", "부동산등기법", "산업입지 및 개발에 관한 법률", "산지관리법",
            "소방기본법", "수도권정비계획법", "에너지이용 합리화법", "전통시장 및 상점가 육성을 위한 특별법", "주차장법",
            "주차장법 시행규칙", "주차장법 시행령", "주택법", "주택법 시행령", "지방세법", "지방자치단체를 당사자로 하는 계약에 관한 법률",
            "지방자치법", "지방재정법", "측량·수로조사 및 지적에 관한 법률", "경기도 건축 조례", "경기도 건축물 미술작품 설치 및 관리에 관한 조례 시행규칙",
            "경기도 위원회 수당 및 여비 지급 조례", "경기도 지방보조금 관리 조례", "용인시 각종 위원회 설치 및 운영 조례",
            "용인시 건축 조례", "용인시 도시계획 조례", "공공발주사업에 대한 건축사의 업무범위와 대가기준"
        ]
        df_ord_borrow = pd.DataFrame({"연계 및 인용 조례의 차용법규명": ord_borrow_data})
        st.dataframe(df_ord_borrow, hide_index=True, use_container_width=True)

    # 탭 4: 법령의 차용 법규 리스트 (제공해주신 61개 항목 정밀 가공 매핑)
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
            "도시교통정비 촉진법", "도시재생 활성화 및 지원에 관한 특별법", 
            "민간임대주택에 관한 특별법", "방송통신발전 기본법", "보금자리주택건설 등에 관한 특별법", 
            "부동산 거래신고 등에 관한 법률", "부동산등기법", "산업입지 및 개발에 관한 법률", 
            "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "소음·진동관리법", 
            "엔지니어링산업 진흥법", "영유아보육법", "자연재해대책법", "장애인·노인·임산부 등의 편의증진 보장에 관한 법률", 
            "재난 및 안전관리 기본법", "전기사업법", "전기통신사업법", "전통시장 및 상점가 육성을 위한 특별법", 
            "정보통신공사업법", "주차장법", "주택법", "중소기업창업 지원법", 
            "지방공기업법", "지방세법", "지방세특례제한법", "지방자치단체를 당사자로 하는 계약에 관한 법률", 
            "지능형건축물 인증에 관한 규칙", "지적재조사에 관한 특별법", "초·중등교육법", 
            "택지개발촉진법", "하수도법", "한국토지주택공사법", "행정대집행법"
        ]
        df_law_borrow = pd.DataFrame({"연계 및 인용 상위법령의 차용법규명": law_borrow_data})
        st.dataframe(df_law_borrow, hide_index=True, use_container_width=True)
