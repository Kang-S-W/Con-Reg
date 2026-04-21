import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 1. API 키 설정 (Secrets 사용)
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # 2. 지침과 질문을 하나로 합침 (영어 금지, 별표/슬래시 금지)
        # 승욱 님의 요청대로 보고서 형식과 금지 규칙을 본문에 직접 주입합니다.
        combined_prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 다음 규칙을 엄격히 지켜서 한국어로만 답변하세요.

        1. 절대 답변에 영어 번역을 병기하지 마세요. (예: 결론 (Conclusion) -> 금지)
        2. 답변 전체에서 별표(*)나 슬래시(/) 기호를 절대 사용하지 마세요.
        3. [cite]나 인용구 표시를 모두 삭제하세요.
        4. 단순 개념 질문은 일반 설명문으로 작성하세요.
        5. 사례 해석 질문은 반드시 아래 6개 항목으로 나누어 작성하세요.
           1. 결론
           2. 적용 지역
           3. 핵심 근거 조문
           4. 세부 설명
           5. 추가 확인 항목
           6. 담당 기관 및 후속 절차

        사용자 질문: {user_query}
        """
        
        # 3. 최신 모델 호출 (v1beta 오류를 피하는 가장 표준적인 경로)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=combined_prompt
        )
        
        if response and response.text:
            # 마지막으로 남아있을지 모를 특수 기호 강제 제거
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 답변을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."

    except Exception as e:
        # 오류 발생 시 사용자에게 친절하게 표시
        return f"분석 엔진 가동 중 문제가 발생했습니다: {str(e)}"
