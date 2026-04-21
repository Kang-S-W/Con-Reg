import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # 1. 보안 설정에서 API 키 불러오기
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        return "오류: 스트림릿 Secrets에 API 키가 설정되지 않았습니다."

    genai.configure(api_key=api_key)
    
    # 2. 404 오류 방지 핵심: 모델 명칭을 가장 표준적인 형태로 고정
    # 라이브러리가 꼬였을 경우를 대비해 예외 처리 강화
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    # 3. 질문 성격에 따른 유연한 지침 (별표, 슬래시, 인용구 제거)
    system_instruction = """
    당신은 용인시 건축 조례 전문가입니다. 
    사용자의 질문 성격에 따라 다음 두 가지 중 하나를 선택하세요.

    1. 단순 개념 질문 (예: 건폐율이 뭐야?, 일조권 정의)
       - 형식: 정의와 산식을 중심으로 일반적인 설명문 형태로 작성하세요.
       - 6가지 항목으로 나누지 마세요.

    2. 구체적 사례 및 법적 해석 질문 (예: 용인시 건폐율 기준, 높이 제한)
       - 형식: 반드시 아래 6가지 항목을 엄격히 준수하세요.
       1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차

    공통 규칙:
    - 별표나 슬래시 기호를 절대 사용하지 마세요.
    -와 같은 문구를 절대 포함하지 마세요.
    - 한국어로만 작성하세요.
    """
    
    try:
        # 질문과 지침 결합
        response = model.generate_content(f"{system_instruction}\n\n질문: {user_query}")
        text = response.text
        
        # 4. 잔여 기호 및 인용구 강제 제거 필터
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        
        return clean_text
    except Exception as e:
        # 오류 발생 시 구체적인 메시지 출력 (디버깅용)
        return f"AI 서비스 연동 오류: {str(e)}"
