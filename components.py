import streamlit as st
import re
import html
import json
import textwrap

def render_user_message(query):
    st.markdown(
        f'<div class="user-msg">질문: {html.escape(query)}</div>',
        unsafe_allow_html=True
    )

def render_ai_report(response_text):
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]
    response_text = re.sub(r"(?m)^\s*#{1,6}\s*", "", response_text)

    # 소제목 뒤에 내용이 바로 붙어 있으면 강제로 다음 줄로 내림
    pattern = r"(?m)^\s*(?:#+\s*)?(" + "|".join(map(re.escape, titles)) + r")\s*[:：]?\s*(?=\S)"
    response_text = re.sub(r"\n{3,}", "\n\n", response_text)
    
    # 예전처럼 줄바꿈 유지 + 소제목만 굵게
    formatted_text = response_text

    for title in titles:
        formatted_text = re.sub(
            rf"(?m)^(\s*{re.escape(title)}\s*)$",
            r'<strong class="report-title">\1</strong>',
            formatted_text
        )

    formatted_text = formatted_text.replace("\n", "<br>")
    copy_text = json.dumps(response_text, ensure_ascii=False)

    html_block = (
        f'<div class="report-wrapper">'
        f'<button class="copy-btn" '
        f'onclick=\'navigator.clipboard.writeText({copy_text})\' '
        f'title="답변 복사">📋 복사TEST</button>'
        f'<div class="report-card">{formatted_text}</div>'
        f'</div>'
    )

    st.markdown(html_block, unsafe_allow_html=True)
