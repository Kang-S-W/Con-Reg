import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 1. 스트림릿 Secrets에서 키 불러오기
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # 2. 인공지능 지침 (별표, 슬래시, 인용구 제거)
        system_instruction = """
        당신은 용인시 건축 조례 전문가입니다. 
        단순 개념은 설명문으로, 사례는 6개 항목 보고서로 답하세요.
        별표나 슬래시 기호, [cite] 문구는 절대 쓰지 마세요.
        항목 번호는 '1. 2. 3.' 형태로만 작성하세요.
        """
        
        # 3. 최신 모델 호출 (v1beta가 아닌 정식 v1 경로 사용)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_query,
            config={'system_instruction': system_instruction}
        )
        
        if response and response.text:
            # 특수 기호 강제 제거 필터
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 답변을 생성하지 못했습니다."

    except Exception as e:
        # 오류 발생 시 어떤 라이브러리를 쓰는지 로그에 찍히게 합니다.
        return f"엔진 연동 오류: {str(e)}"
