import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    try:
        # 1. 보안 비밀에서 키 불러오기
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 2. 모델 설정 (가장 표준적인 명칭인 'gemini-1.5-flash' 사용)
        # 이 명칭이 404가 뜨는 것은 라이브러리 버전 문제일 가능성이 99%입니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_instruction = """
        당신은 용인시 건축 조례 및 법령 전문가입니다. 
        단순 개념 질문은 일반 설명문으로, 사례 해석은 6가지 항목 보고서로 답하세요.
        별표나 슬래시 기호, [cite] 문구는 절대 사용하지 마세요.
        모든 답변은 한국어로 작성하세요.
        """
        
        full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
        
        # 3. 답변 생성
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            text = response.text
            # 인용구 및 불필요한 기호 제거
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 빈 답변을 반환했습니다. 다시 시도해 주세요."
            
    except Exception as e:
        # 오류 발생 시 구체적인 원인을 출력합니다.
        return f"분석 엔진 오류: {str(e)}"
