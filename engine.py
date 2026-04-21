import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    try:
        # 1. API 키 설정
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 2. 모델 설정 (가장 안정적인 flash 모델 사용)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 3. 지침을 프롬프트 내부에 직접 주입 (400 에러 원천 차단)
        # 승욱 님의 요청사항(영어 금지, 별표/슬래시 금지)을 최우선으로 반영
        failsafe_prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 다음 규칙을 '절대' 준수하여 답변하세요:

        규칙 1: 모든 답변은 한국어로만 작성하세요. 영어 번역을 병기하지 마세요.
        규칙 2: 답변 전체에서 별표(*)나 슬래시(/) 기호를 절대 사용하지 마세요. 강조는 숫자로만 하세요.
        규칙 3: [cite]나 인용구 표시를 모두 제거하세요.
        규칙 4: 질문이 단순 개념이면 일반 설명문으로, 구체적 사례면 아래 6단계 형식을 따르세요.
        (1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차)

        질문 내용: {user_query}
        """
        
        # 4. 답변 생성
        response = model.generate_content(failsafe_prompt)
        
        if response and response.text:
            text = response.text
            # 인용구 및 잔여 특수 기호 강제 제거
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI 응답 생성 실패: 답변이 비어 있습니다."

    except Exception as e:
        return f"엔진 최종 가동 오류: {str(e)}"
