import streamlit as st
import re
import html
import json

def render_user_message(query):
    """사용자 질문 출력"""
    st.markdown(
        f'<div class="user-msg">질문: {html.escape(query)}</div>',
        unsafe_allow_html=True
    )

def render_ai_report(response_text):
    """AI 답변 출력 + 소제목 정리 + st.iframe 기반 복사 버튼"""

    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 1. Markdown 제목(#) 표시 제거
    response_text = re.sub(r"(?m)^\s*#{1,6}\s*", "", response_text)

    # 2. 소제목 정리 (다음 줄로 내림)
    pattern = r"(?m)^\s*(" + "|".join(map(re.escape, titles)) + r")\s*[:：]?\s*(.*)$"
    def fix_heading(match):
        title = match.group(1)
        body = match.group(2).strip()
        return f"\n\n{title}\n{body}" if body else f"\n\n{title}"
    response_text = re.sub(pattern, fix_heading, response_text)
    response_text = re.sub(r"\n{3,}", "\n\n", response_text).strip()

    # 3. 화면 표시용 HTML 변환 및 특수문자 보호
    formatted_text = html.escape(response_text)

    # [★ 핵심 수정: 하이퍼링크 강제 활성화]
    # engine.py에서 보낸 [이름]|||주소||| 형식을 <a> 태그로 바꿉니다.
    # 이 방식은 주소 끝의 ')'가 잘리지 않게 완벽히 보호합니다.
    formatted_text = re.sub(
        r"\[(.*?)\]\|\|\|(.*?)\|\|\|", 
        r'<a href="\2" target="_blank" style="color: #0b459c; text-decoration: underline; font-weight: bold;">\1</a>', 
        formatted_text
    )

    # 소제목 볼드 처리
    for title in titles:
        formatted_text = re.sub(
        r"\[(.*?)\]\|\|\|(.*?)\|\|\|", 
        r'<a href="\2" target="_blank" style="color: #0b459c; text-decoration: underline; font-weight: bold;">\1</a>', 
        formatted_text
    )
    
    formatted_text = formatted_text.replace("\n", "<br>")

    # 4. 복사용 텍스트 준비
    copy_text = json.dumps(response_text, ensure_ascii=False)

    # 5. [★ 핵심 수정: st.iframe으로 교체]
    # 2026-06-01 삭제 예정인 구형 함수를 최신 규격으로 교체하여 경고를 제거합니다.
    copy_button_html = f"""
    <div style="text-align:right; height:34px;">
        <button id="copyBtn" style="border:1px solid #ccc; background:white; border-radius:8px; padding:4px 9px; cursor:pointer; font-size:14px;">📋 복사</button>
    </div>
    <script>
    const text = {copy_text};
    const btn = document.getElementById("copyBtn");
    btn.addEventListener("click", async () => {{
        try {{
            const ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed"; ta.style.left = "-9999px";
            document.body.appendChild(ta); ta.focus(); ta.select();
            document.execCommand("copy"); document.body.removeChild(ta);
            btn.innerText = "✅ 복사됨";
            setTimeout(() => btn.innerText = "📋 복사", 1200);
        }} catch (e) {{ btn.innerText = "복사 실패"; }}
    }});
    </script>
    """
    
    # data:text/html 형식을 사용하여 iframe 내부에 버튼을 렌더링합니다.
    st.iframe(f"data:text/html;charset=utf-8,{html.escape(copy_button_html)}", height=45)

    # 6. 최종 답변 카드 출력
    st.markdown(
        f'<div class="report-card">{formatted_text}</div>',
        unsafe_allow_html=True
    )
