import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # 지침을 본문에 합쳐서 서버가 헛소리 못하게 차단
        prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하세요.
        규칙:
        1. 답변에 영어 번역을 절대 넣지 마세요.
        2. 별표(*)나 슬래시(/) 기호를 절대 쓰지 마세요.
        3. [cite] 표시를 모두 지우세요.
        4. 단순 개념은 설명문으로, 사례는 아래 6개 항목으로 답하세요.
        (1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차)

        질문: {user_query}
        """
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        if response and response.text:
            # 특수 기호 최종 제거
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        return "답변 생성에 실패했습니다."

    except Exception as e:
        return f"연동 오류: {str(e)}"
