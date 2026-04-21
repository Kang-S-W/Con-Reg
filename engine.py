import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 1. API 키 호출
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 2. 클라이언트 생성 시 API 버전을 'v1'으로 강제 고정합니다. (v1beta 오류 원천 차단)
        client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1'}
        )
        
        # 3. AI 응답 지침 (영어 병기 금지, 별표/슬래시 금지)
        system_instruction = """
        당신은 용인시 건축 조례 전문가입니다. 
        모든 답변은 한국어로만 작성하세요. (영어 번역 병기 절대 금지)
        별표나 슬래시 기호를 절대 사용하지 마세요.
        [cite] 문구는 무조건 제거하세요.

        1. 단순 개념 설명 (예: 건폐율 정의)
           - 일반 설명문 형태로 작성.
        2. 사례 해석 (예: 용인시 건폐율 기준)
           - 아래 6가지 항목 준수:
           1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차
        """
        
        # 4. 콘텐츠 생성
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_query,
            config={'system_instruction': system_instruction}
        )
        
        if response and response.text:
            # 특수 기호 최종 필터링
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 응답을 생성하지 못했습니다."

    except Exception as e:
        # 오류 메시지에 라이브러리 정보를 포함하여 확실히 진단합니다.
        return f"엔진 연동 오류(신규 SDK): {str(e)}"
