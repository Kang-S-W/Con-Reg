import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 1. 스트림릿 Secrets에서 API 키 호출
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 2. 최신 google-genai 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # 3. 인공지능 지침 (영어 병기 금지, 별표/슬래시 제거)
        system_instruction = """
        당신은 용인시 건축 조례 전문가입니다. 
        단순 개념 질문은 일반 설명문으로, 사례 해석은 6개 항목 보고서로 답하세요.
        답변에 영어 번역을 병기하지 마세요.
        별표나 슬래시 기호, [cite] 문구는 절대 사용하지 마세요.
        모든 답변은 한국어로만 작성하세요.
        """
        
        # 4. 최신 방식의 콘텐츠 생성 (v1beta 오류를 피하는 가장 확실한 방법)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_query,
            config={'system_instruction': system_instruction}
        )
        
        if response and response.text:
            # 특수 기호 강제 제거
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 답변 생성에 실패했습니다."

    except Exception as e:
        return f"최신 엔진 연동 오류 발생: {str(e)}"
