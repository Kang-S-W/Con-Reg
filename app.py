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

# ==========================================
# 1. 페이지 설정 (가장 먼저 실행되어야 함)
# ==========================================
st.set_page_config(
    page_title="용인시 건축 조례 지원 플랫폼", 
    page_icon="🏢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모듈 Import (페이지 설정 이후)
from widget_utils import inject_floating_button
from docx import Document
from processor import handle_ai_analysis, generate_civil_document
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 용인시 민원창구 연계버튼
inject_floating_button()

# ==========================================
# 2. 상태 변수 초기화
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = "guest"
if "chat_history" not in st.session_state: st.session_state.chat_history = load_history(st.session_state.user_id)
if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
if "selected_index" not in st.session_state: st.session_state.selected_index = None
if "current_page" not in st.session_state: st.session_state.current_page = "main"
if "qna_list" not in st.session_state: st.session_state.qna_list = []

def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle

# ==========================================
# 3. 프리미엄 CSS 스타일링 (SaaS 룩앤필 & 가시성 개선)
# ==========================================
apply_custom_style(st.session_state.dark_mode) 

def apply_premium_ui(is_dark):
    # ChatGPT, Claude 스타일의 모던/플랫 디자인 적용
    base_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    
    /* 아이콘 폰트 강제 복구 블록 */
    span[class*="material-symbols"], span[class*="material-icons"], i[class*="material"],
    .material-icons, .material-symbols-rounded, .material-symbols-outlined,
    [data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"],
    button[kind="header"] span, button[kind="header"] i {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-weight: normal !important;
        font-style: normal !important;
        -webkit-font-smoothing: antialiased !important;
    }
    
    /* 입력창 디자인 (모던 플랫 스타일) */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        border-radius: 12px !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 1px #4A90E2 !important;
    }
    
    /* 버튼 디자인 */
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] button:active { transform: scale(0.98); }
    
    /* Expander 디자인 */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        box-shadow: none !important;
        margin-bottom: 12px !important;
    }
</style>
"""
    # 라이트/다크 모드 글씨 안보임 현상을 완벽히 해결한 테마 분기
    if is_dark:
        theme_css = """
<style>
    [data-testid="stAppViewContainer"] { background-color: #212121 !important; color: #ECECEC !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stSidebar"] { background-color: #171717 !important; border-right: 1px solid #333 !important; }
    
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #2F2F2F !important; border: 1px solid #444 !important; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { color: #FFF !important; }
    
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button { background-color: #2F2F2F !important; color: #ECECEC !important; border: 1px solid #444 !important; }
    div[data-testid="stButton"] button:hover { background-color: #3A3A3A !important; border-color: #555 !important; }
    
    div[data-testid="stExpander"] { background-color: #171717 !important; border: 1px solid #333 !important; }
    div[data-testid="stExpander"] details summary { color: #ECECEC !important; }
    
    /* 기본 텍스트 요소가 배경에 묻히지 않도록 상위 컨테이너 컬러 강제 */
    .stMarkdown, .stText { color: #ECECEC !important; }
</style>
"""
    else:
        theme_css = """
<style>
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; color: #111111 !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stSidebar"] { background-color: #F9F9F9 !important; border-right: 1px solid #E5E5E5 !important; }
    
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #FFFFFF !important; border: 1px solid #E5E5E5 !important; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { color: #111111 !important; }
    
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button { background-color: #FFFFFF !important; color: #333333 !important; border: 1px solid #E5E5E5 !important; }
    div[data-testid="stButton"] button:hover { background-color: #F0F0F0 !important; border-color: #D5D5D5 !important; }
    
    div[data-testid="stExpander"] { background-color: #F9F9F9 !important; border: 1px solid #E5E5E5 !important; }
    div[data-testid="stExpander"] details summary { color: #111111 !important; }
    
    .stMarkdown, .stText { color: #111111 !important; }
</style>
"""
    st.markdown(base_css + theme_css, unsafe_allow_html=True)

apply_premium_ui(st.session_state.dark_mode)

# --- [대화기록 검색 팝업] ---
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

@dialog_decorator("🔍 대화기록 검색", width="large")
def open_history_search_dialog():
    search_query = st.text_input("검색어 입력", placeholder="예: 일조권, 건폐율...", key="dialog_history_search_input")
    query = search_query.strip().lower()

    if not st.session_state.chat_history:
        st.caption("저장된 대화기록이 없습니다.")
        return

    results = []
    for idx, chat in enumerate(st.session_state.chat_history):
        searchable_text = chat.get("title", "") + " "
        for msg in chat.get("messages", []):
            searchable_text += msg.get("query", "") + " " + msg.get("response", "") + " "
        if not query or query in searchable_text.lower():
            results.append((idx, chat))

    st.caption(f"검색 결과 {len(results)}개" if query else "최근 대화")

    if not results:
        st.warning("검색 결과가 없습니다.")
        return

    with st.container(height=400, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            preview = chat.get("messages", [])[0].get("query", "")[:60] + "..." if chat.get("messages") else ""
            
            with st.container():
                if st.button(f"💬 {title[:25]}... \n\n {time_str}", key=f"dialog_chat_{idx}", use_container_width=True):
                    st.session_state.selected_index = idx
                    st.session_state.current_page = "main"
                    st.rerun()
                st.caption(f"미리보기: {preview}")
                st.markdown("---")

# ==========================================
# 4. 사이드바 구성 (그룹화 및 깔끔한 정리)
# ==========================================
with st.sidebar:
    st.title("플랫폼 제어")
    
    # [인증 섹션]
    with st.expander("👤 실무자 시스템 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            auth_tabs = st.tabs(["로그인", "회원가입"])
            with auth_tabs[0]:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("로그인", use_container_width=True):
                    from storage import authenticate_user
                    if authenticate_user(login_id.strip(), login_pw.strip()):
                        st.session_state.user_id = login_id.strip()
                        st.session_state.chat_history = load_history(st.session_state.user_id)
                        st.toast(f"환영합니다, {st.session_state.user_id}님!", icon="👋")
                        st.rerun()
                    else:
                        st.error("정보가 일치하지 않습니다.")
            with auth_tabs[1]:
                reg_id = st.text_input("새 아이디", key="reg_id")
                reg_pw = st.text_input("비밀번호", type="password", key="reg_pw")
                if st.button("가입하기", use_container_width=True):
                    from storage import check_id_exists, register_user
                    if check_id_exists(reg_id.strip()):
                        st.error("이미 존재하는 아이디입니다.")
                    elif register_user(reg_id.strip(), reg_pw.strip()):
                        st.toast("가입 성공! 로그인해주세요.", icon="✅")
        else:
            st.success(f"현재 접속: **{st.session_state.user_id}**")
            if st.button("안전 로그아웃", use_container_width=True):
                st.session_state.user_id = "guest"
                st.session_state.chat_history = load_history("guest")
                st.session_state.selected_index = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # [메뉴 내비게이션]
    st.subheader("📌 메인 메뉴")
    if st.button("🏠 메인화면 (AI 챗봇)", use_container_width=True): st.session_state.current_page = "main"; st.rerun()
    if st.button("📝 민원 양식 자동생성", use_container_width=True): st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("💡 FAQ & Q&A 게시판", use_container_width=True): st.session_state.current_page = "qna"; st.rerun()
    if st.button("🗺️ 플랫폼 사이트맵", use_container_width=True): st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("🌙 다크 모드", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.markdown("---")
    
    # [대화 이력 섹션]
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 새 대화", use_container_width=True):
            st.session_state.selected_index = None
            st.session_state.current_page = "main"
            st.rerun()
    with col2:
        if st.button("🔍 검색", use_container_width=True):
            open_history_search_dialog()

    st.subheader("대화 이력")
    history_container = st.container(height=350, border=False)
    with history_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                actual_index = len(st.session_state.chat_history) - 1 - i
                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]
                query_summary = chat.get("title", "새 대화")[:12] + ".."
                
                col_btn, col_del = st.columns([8, 2])
                with col_btn:
                    if st.button(f"조회 {time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                        st.session_state.selected_index = actual_index
                        st.session_state.current_page = "main"
                        st.rerun()
                with col_del:
                    if st.button("삭제", key=f"del_{actual_index}", use_container_width=True):
                        st.session_state.chat_history.pop(actual_index)
                        from storage import save_history
                        save_history(st.session_state.chat_history, st.session_state.user_id)
                        
                        if st.session_state.selected_index == actual_index:
                            st.session_state.selected_index = None
                        elif st.session_state.selected_index is not None and st.session_state.selected_index > actual_index:
                            st.session_state.selected_index -= 1
                        st.rerun()
        else:
            st.caption("저장된 기록이 없습니다.")

    if st.session_state.chat_history:
        if st.button("🗑️ 전체 기록 삭제", type="primary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.selected_index = None
            from storage import clear_history
            clear_history(st.session_state.user_id) 
            st.toast("모든 기록이 삭제되었습니다.", icon="🗑️")
            st.rerun()


# ==========================================
# 5. 화면 분기 처리 (Main Content)
# ==========================================

# --- 🤖 1. 메인화면 ---
if st.session_state.current_page == "main":
    
    # 상단 헤더 깔끔하게 정리
    st.markdown("## 🏢 건축 조례 및 법령 해석 AI")
    st.caption("건축사, 시공사, 인허가 담당자의 신속한 의사결정을 돕는 심층 규제 분석 엔진입니다.")
    st.write("")

    if st.session_state.selected_index is not None:
        current_chat = st.session_state.chat_history[st.session_state.selected_index]
        if "state" not in current_chat:
            current_chat["state"] = {}
        current_state = current_chat["state"]
    else:
        current_chat = None
        current_state = {}

    col_top_left, col_top_right = st.columns([4, 1])
    with col_top_right:
        show_state_panel = st.toggle("상태 저장소 패널", value=True, key="use_state_panel")

    if show_state_panel:
        col_chat, col_state = st.columns([3, 1])
    else:
        col_chat = st.container()
        col_state = None

    with col_chat:
        chat_box = st.container(height=550, border=False)
        user_query = st.chat_input("예: 용인시 처인구 자연녹지지역의 건폐율과 용적률 기준은?")

        with chat_box:
            if current_chat is not None:
                st.info(f"과거 대화 열람 중: {current_chat.get('title', '새 대화')}")
                for msg in current_chat.get("messages", []):
                    render_user_message(msg.get("query", ""))
                    render_ai_report(msg.get("response", ""))
                
                if st.button("닫기 및 새 질문하기", use_container_width=True):
                    st.session_state.selected_index = None
                    st.rerun()
            else:
                # 이미지를 제거하고 모던한 안내 메시지로 대체
                st.markdown("""
                <div style='text-align: center; margin-top: 80px; margin-bottom: 40px;'>
                    <h2 style='color: #888; margin-bottom: 20px;'>어떤 규제를 검토해 드릴까요?</h2>
                    <p style='color: #aaa; font-size: 16px;'>경기도 용인시 조례 및 125개 상위 법령 데이터베이스를 기반으로 정확하게 분석합니다.<br>하단의 입력창에 질의하고 싶은 조례 및 구역을 자유롭게 남겨주세요.</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_chip1, col_chip2 = st.columns(2)
                with col_chip1:
                    st.info("💡 **예시:** 인접 대지 신축 공사로 인한 일조권 사선제한 예외 조건은?")
                with col_chip2:
                    st.info("💡 **예시:** 용인시 기흥구 보정동 제2종 일반주거지역의 건축선 후퇴 기준은?")

        if user_query:
            render_user_message(user_query)
            with st.status("법률 시맨틱 엔진 가동 중...", expanded=True) as status:
                try:
                    st.write("조항 필터링 및 교차 검증 진행 중...")
                    response_text = handle_ai_analysis(user_query)

                    if st.session_state.chat_history:
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1

                    status.update(label="심층 분석 완료", state="complete")
                    render_ai_report(response_text)
                    st.toast("분석이 완료되었습니다.")
                except Exception as e:
                    status.update(label="시스템 에러 발생", state="error")
                    st.error(f"오류가 발생했습니다: {str(e)}")
            st.rerun()

    if show_state_panel and col_state is not None:
        with col_state:
            st.subheader("상태 저장소")
            st.caption("대지 및 건축물의 상태값으로, 답변에 참조됩니다.")

            with st.expander("주소 기반 대지 정보 자동 연동", expanded=True):
                search_addr = st.text_input("도로명 주소 입력", placeholder="예: 중부대로 1199", label_visibility="collapsed")
                if st.button("데이터 연동", use_container_width=True):
                    if current_chat is not None:
                        mock_data = {"용도지역": "준주거지역 (임시)", "용도지구": "해당없음 (임시)", "대지면적": "8000 (임시)"}
                        current_chat["state"].update(mock_data)
                        from storage import save_history
                        save_history(st.session_state.chat_history, st.session_state.user_id)
                        st.rerun()

            if current_chat is not None:
                import pandas as pd
                
                if not current_state:
                    df_state = pd.DataFrame(columns=["항목", "내용"])
                else:
                    df_state = pd.DataFrame(list(current_state.items()), columns=["항목", "내용"])

                edited_df = st.data_editor(
                    df_state,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key=f"state_editor_{st.session_state.selected_index}"
                )

                new_state = {}
                for _, row in edited_df.iterrows():
                    key_val = str(row["항목"]).strip() if pd.notna(row["항목"]) else ""
                    val_val = str(row["내용"]).strip() if pd.notna(row["내용"]) else ""
                    if key_val and key_val != "nan":
                        new_state[key_val] = val_val

                if new_state != current_state:
                    current_chat["state"] = new_state
                    from storage import save_history
                    save_history(st.session_state.chat_history, st.session_state.user_id)
                    st.rerun()
            else:
                st.info("상태 저장소는 대화창별로 저장됩니다.")
        
        
# --- 📝 2. 민원 양식 생성 ---
elif st.session_state.current_page == "doc_gen":
    st.markdown("## 📝 맞춤형 건축 민원 양식 자동완성")
    st.caption("복잡한 민원 내용을 입력하면 AI가 용인시 행정 양식에 맞춰 문서를 정갈하게 작성해 드립니다.")
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
        civil_type = st.selectbox("📌 민원 유형 선택", list(required_docs.keys()))
    with col2:
        site_address = st.text_input("📍 대상 건축물 주소", placeholder="예: 경기도 용인시 처인구 중부대로 1199")

    civil_content = st.text_area("✏️ 민원 상세 내용", height=150, placeholder="예: 인접 대지 신축 공사로 인해 심각한 일조권 침해가 우려되어 확인을 요청합니다...")

    if st.button("✨ AI 민원 양식 생성하기", use_container_width=True, type="primary"):
        if not site_address or not civil_content:
            st.error("주소와 민원 내용을 모두 입력해주세요.")
        else:
            with st.spinner("서식 구조화 및 양식 작성 중..."):
                try:
                    result = generate_civil_document(civil_type, site_address, civil_content)
                    st.session_state.selected_index = None
                    st.toast("민원 양식이 성공적으로 생성되었습니다!", icon="🎉")
                    
                    st.divider()
                    st.subheader("📄 생성된 민원서")
                    st.markdown(f"<div style='padding:20px; border:1px solid #ddd; border-radius:12px; background:rgba(150,150,150,0.05);'>{result}</div>", unsafe_allow_html=True)
                    
                    info_tabs = st.tabs(["📎 필요 서류", "🏢 담당 부서", "🏛️ 접수 절차", "📥 파일 다운로드"])
                    
                    with info_tabs[0]:
                        for doc in required_docs.get(civil_type, required_docs["기타"]):
                            st.write(f"✔️ {doc}")
                    with info_tabs[1]:
                        dept = department_map.get(civil_type, "민원여권과")
                        st.info(f"📌 용인시청 또는 관할 구청 **{dept}** 문의 요망")
                    with info_tabs[2]:
                        st.markdown("""
                        * **온라인:** 정부24(gov.kr), 국민신문고(epeople.go.kr) 용인시 지정 접수
                        * **오프라인:** 용인시청/구청 민원실 방문 접수
                        * **전화문의:** 용인시 민원콜센터 (☎️ 1577-1122)
                        """)
                    with info_tabs[3]:
                        doc = Document()
                        doc.add_heading('용인시 건축 행정 민원서', level=1)
                        doc.add_paragraph(f"민원 유형: {civil_type}\n대상 주소: {site_address}")
                        doc.add_heading('민원 내용', level=2)
                        doc.add_paragraph(result)

                        buffer = io.BytesIO()
                        doc.save(buffer)
                        buffer.seek(0)
                        st.download_button(
                            label="💾 DOCX 양식 다운로드",
                            data=buffer,
                            file_name="용인시_건축민원서.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")

# --- 💡 3. Q&A 게시판 ---
elif st.session_state.current_page == "qna":
    st.markdown("## 💡 커뮤니티 Q&A")
    st.caption("플랫폼 사용법이나 애매한 규제 해석에 대해 질문을 남겨주시면 전문가가 답변해 드립니다.")
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📋 실시간 질문 목록")
        if not st.session_state.qna_list:
            st.info("등록된 질문이 없습니다. 첫 질문의 주인공이 되어보세요!")
        else:
            for i, q in enumerate(st.session_state.qna_list):
                status_badge = "⏳ 답변대기" if q['status'] == "대기중" else "✅ 답변완료"
                with st.expander(f"[{status_badge}] {q['title']}"):
                    st.markdown(f"**Q.** {q['content']}")
                    if q['status'] == "답변완료":
                        st.info(f"**A.** {q['answer']}")
    
    with col2:
        st.subheader("📝 질문 작성하기")
        with st.form("qna_form", clear_on_submit=True):
            q_title = st.text_input("제목", placeholder="질문 요약")
            q_content = st.text_area("내용", placeholder="상세 내용 입력")
            if st.form_submit_button("질문 등록", use_container_width=True):
                if q_title and q_content:
                    st.session_state.qna_list.append({"title": q_title, "content": q_content, "status": "대기중", "answer": ""})
                    st.toast("질문이 등록되었습니다.", icon="✅")
                    st.rerun()
                else:
                    st.error("모두 입력해 주세요.")
        
        st.divider()
        with st.expander("🛠️ 관리자 패널"):
            admin_pw = st.text_input("관리자 PIN", type="password")
            if admin_pw == "2026":
                st.success("인증 완료")
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        answer_text = st.text_input(f"답변: {q['title']}", key=f"ans_{i}")
                        if st.button("답변 등록", key=f"btn_{i}"):
                            st.session_state.qna_list[i]['answer'] = answer_text
                            st.session_state.qna_list[i]['status'] = "답변완료"
                            st.rerun()

# --- 🗺️ 4. 사이트맵 ---
elif st.session_state.current_page == "sitemap":
    st.markdown("## 🗺️ 플랫폼 사이트맵 및 아키텍처")
    st.caption("본 플랫폼은 클라우드 기반 AI 엔진과 최신 법률 DB를 연동하여 동작합니다.")
    st.divider()
    
    # 1. 사이트 트리 구성 (오류 없는 네이티브 마크다운)
    st.subheader("📍 사이트 트리 (Site Tree)")
    col_tree1, col_tree2 = st.columns(2)
    
    with col_tree1:
        st.markdown("""
        * **🏠 메인화면 (AI 챗봇)**
            * 실시간 법령/조례 검토 시맨틱 엔진
            * 대화 이력 관리 (조회, 검색, 삭제)
            * 건축물 상태 저장소 (주소 연동, 대지 정보 관리)
        * **📝 민원 양식 자동생성**
            * 민원 유형별 필수 서류 안내
            * 담당 부서 및 접수 절차 안내
            * AI 맞춤형 민원서 자동 작성 및 DOCX 다운로드
        """)
        
    with col_tree2:
        st.markdown("""
        * **💡 FAQ & Q&A 게시판**
            * 실시간 커뮤니티 질의응답
            * 관리자 전용 답변 처리 패널
        * **🗺️ 플랫폼 사이트맵**
            * 사이트 트리 및 시스템 아키텍처 안내
            * 취급 법규 및 조례 DB 목록 조회
        """)

    st.divider()

    # 2. 시스템 아키텍처 (HTML 충돌 없는 네이티브 컨테이너)
    st.subheader("⚙️ 시스템 아키텍처")
    col_arch1, col_arch2, col_arch3 = st.columns(3)
    
    with col_arch1:
        with st.container(border=True):
            st.markdown("#### 📱 UI Layer\n*(대국민 / 실무자 서비스)*")
            st.markdown("- 🤖 AI 법률 검토 (자연어)\n- 📝 문서 생성 자동화\n- 💡 실시간 커뮤니티")
            
    with col_arch2:
        with st.container(border=True):
            st.markdown("#### 🧠 Processing Layer\n*(AI 핵심 엔진)*")
            st.markdown("- 🔍 LLM 기반 조항 분석\n- 🧩 RAG 시맨틱 벡터 검색\n- ⚖️ 논리 추론 및 매핑")
            
    with col_arch3:
        with st.container(border=True):
            st.markdown("#### 🗄️ Data Layer\n*(데이터베이스 연동)*")
            st.markdown("- 🏛️ 국가법령정보센터 API\n- 📂 플랫폼 로컬 Vector DB\n- 📜 125+ 상위법 및 조례")

    st.divider()
    
    with st.expander("📚 취급 법규 전체 목록 보기", expanded=True):
        st.caption("※ 탭을 클릭하여 종류별 법규를 확인하세요.")
        tabs = st.tabs(["🏛️ 지역 조례 (7개)", "📜 주요 상위법", "🔗 위임 법규"])
        
        with tabs[0]:
            df_ord = pd.DataFrame([
                ["경기도", "경기도 건축 조례", "건축법"], ["경기도", "경기도 건축기본조례", "건축기본법"],
                ["용인시", "용인시 건축 조례", "건축법"], ["용인시", "용인시 도시계획 조례", "국토계획법"]
            ], columns=["지자체", "조례명", "근거법률"])
            st.dataframe(df_ord, hide_index=True, use_container_width=True)
        with tabs[1]:
            st.write("✔️ 건축법 / 시행령 / 시행규칙 \n✔️ 국토의 계획 및 이용에 관한 법률 \n✔️ 건축물관리법")
        with tabs[2]:
            st.write("총 100여 개의 조례 및 상위법 위임 하위 법규(건설기술진흥법, 농지법, 주택법 등) 데이터를 교차 검증합니다.")
