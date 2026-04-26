# style.py
import streamlit as st

def apply_custom_style(is_dark: bool):
    """
    다크 모드 여부에 따라 전체 Streamlit UI 색상을 동적으로 변경하는 CSS 주입 함수
    """
    if is_dark:
        bg_main = "#0e1117"
        bg_sidebar = "#262730"
        text_main = "#fafafa"
        card_bg = "#1e1e1e"
        card_border = "#333333"
        user_msg_bg = "#1e3a8a"
        user_msg_text = "#ffffff"
        tab_color = "#aaaaaa"
        btn_bg = "#333333"
        btn_border = "#555555"
    else:
        bg_main = "#ffffff"
        bg_sidebar = "#f4f6f9"
        text_main = "#222222"
        card_bg = "#ffffff"
        card_border = "#eaeaea"
        user_msg_bg = "#e1f5fe"
        user_msg_text = "#000000"
        tab_color = "#555555"
        btn_bg = "#ffffff"
        btn_border = "#cccccc"

    custom_css = f"""
    <style>
    /* 1. 메인 화면 & 폰트 */
    .stApp {{ background-color: {bg_main}; color: {text_main}; }}
    html, body, [class*="css"] {{ font-size: 16px !important; line-height: 1.7 !important; color: {text_main}; }}
    
    /* 2. 최상단 헤더(하얀 띠) 투명화 및 배경색 동기화 */
    [data-testid="stHeader"] {{ background-color: {bg_main} !important; }}
    
    /* 3. 사이드바 배경 및 텍스트 색상 강제 지정 */
    [data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; }}
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{
        color: {text_main} !important;
    }}
    
    /* 4. 일반 버튼 (Secondary) - '전체 기록 삭제' 등 */
    button[kind="secondary"] {{
        background-color: {btn_bg} !important;
        color: {text_main} !important;
        border: 1px solid {btn_border} !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: #1E88E5 !important;
        color: #1E88E5 !important;
    }}
    
    /* 5. 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 15px; border-bottom: 2px solid {card_border}; }}
    .stTabs [data-baseweb="tab"] {{ height: 60px; font-size: 18px !important; font-weight: 600; color: {tab_color}; }}
    .stTabs [aria-selected="true"] {{ color: #1E88E5 !important; }}
    
    /* 6. 결과 보고서 카드 및 사용자 메시지 (components.py 연동용) */
    .report-card {{ 
        padding: 30px; border-radius: 12px; background-color: {card_bg}; 
        border: 1px solid {card_border}; color: {text_main};
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 10px; margin-bottom: 20px; 
    }}
    .user-msg {{ 
        background-color: {user_msg_bg}; color: {user_msg_text};
        padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; font-weight: bold;
    }}
    
    /* 7. 기본 텍스트 요소 강제 적용 */
    p, h1, h2, h3, h4, h5, h6, li {{ color: {text_main} !important; }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)
