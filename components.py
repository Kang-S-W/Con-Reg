import streamlit as st
import re
import uuid
import html
import json

def render_user_message(query):
    st.markdown(
        f'<div class="user-msg">질문: {query}</div>',
        unsafe_allow_html=True
    )

def render_ai_report(response_text):
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 화면 표시용 HTML
    safe_text = html.escape(response_text)

    for title in titles:
        safe_text = re.sub(
            rf"(?m)^\s*(?:#+\s*)?{re.escape(title)}\s*[:：]?(?=\s|$)",
            f'<strong class="report-title">{title}</strong>',
            safe_text
        )

    formatted_text = safe_text.replace("\n", "<br>")

    # 복사용 원문 텍스트
    copy_text = json.dumps(response_text, ensure_ascii=False)
    box_id = f"copy_{uuid.uuid4().hex}"

    st.markdown(f"""
<div class="report-wrapper">
    <button class="copy-btn"
        onclick='navigator.clipboard.writeText({copy_text})'
        title="답변 복사">📋 복사TEST</button>

    <div id="{box_id}" class="report-card">{formatted_text}</div>
</div>
""", unsafe_allow_html=True)
