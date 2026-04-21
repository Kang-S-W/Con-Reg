import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 1. 최신 방식의 클라이언트 설정
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # 2. 질문 성격에 따른 지침 설정 (별표, 슬래시, 인용구 제거 강제)
        system_instruction = """
        당신은 용인시 건축 조례 전문가입니다. 
        사용자의 질문 성격에 따라 다음 두 가지 방식 중 하나를 선택하세요.

        1. 단순 개념 질문 (예: 건폐율이 뭐야?)
           정의와 산식을 중심으로 일반적인 설명문 형태로 작성하세요. 6가지 항목으로 나누지 마세요.

        2. 구체적 사례 및 법적 해석 질문 (예: 용인시 건폐율 기준)
           반드시 아래 6가지 항목을 엄격히 준수하세요.
           1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차

        공통 규칙:
        별표나 슬래시 기호를 절대 사용하지 마세요.
        인용 표시나 cite 문구를 절대 포함하지 마세요.
        한국어로만 작성하세요.
        """
        
        # 3. 최신 API 호출 방식 적용
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_query,
            config={'system_instruction': system_instruction}
        )
        
        if response and response.text:
            text = response.text
            # 잔여 특수 기호 및 인용구 강제 제거 필터
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 답변을 생성하는 데 실패했습니다."

    except Exception as e:
        return f"최신 엔진 연동 오류: {str(e)}"
