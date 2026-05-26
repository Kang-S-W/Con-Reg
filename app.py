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

# 1. 페이지 설정 (가장 먼저 실행되어야 함)
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

# --- [로컬 이미지 변환 함수] ---
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

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
# 3. 프리미엄 CSS 스타일링 (SaaS 룩앤필 & 아이콘 깨짐 완벽 방지)
# ==========================================
# 기존 style.py에서 넘어오는 CSS가 있다면 여기서 먼저 실행됩니다.
apply_custom_style(st.session_state.dark_mode) 

def apply_premium_ui(is_dark):
    base_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    
    /* 1. 기본 폰트 적용 (!important 남발 방지) */
    html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div { 
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; 
    }
    
    /* 2. 🚨 가장 중요한 아이콘 폰트 강제 복구 블록 🚨 */
    /* style.py 등에서 * { font-family: ... !important; } 가 적용되었더라도 이를 무력화합니다. */
    span[class*="material-symbols"], 
    span[class*="material-icons"], 
    i[class*="material"],
    .material-icons,
    .material-symbols-rounded,
    .material-symbols-outlined,
    [data-testid="stIconMaterial"],
    [data-testid="stExpanderToggleIcon"],
    button[kind="header"] span,
    button[kind="header"] i {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' 1 !important;
        font-feature-settings: 'liga' 1 !important;
        -webkit-font-smoothing: antialiased !important;
    }
    
    /* 입력창 디자인 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
        border-color: #0b459c !important;
        box-shadow: 0 0 0 2px rgba(11, 69, 156, 0.2) !important;
    }
    
    /* 버튼 디자인 */
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: none !important;
        font-family: 'Pretendard', sans-serif !important; /* 버튼 텍스트는 Pretendard 강제 */
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stButton"] button:active { transform: translateY(0px); }
    
    /* Expander (아코디언 메뉴) 디자인 */
    div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid rgba(150, 150, 150, 0.2) !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
        margin-bottom: 12px !important;
    }
</style>
"""
    # 다크/라이트 모드별 색상 세부 조정
    theme_css = """
<style>
    .stApp { background-color: #121212 !important; }
    div[data-testid="stSidebar"]
