import streamlit as st
import requests
import json
import re
import time

def get_gemini_response(user_query, db_context=""):
    # 1. 모델명 수정 (안정적인 1.5-flash 사용)
    # 2.0 버전을 원하실 경우 'gemini-2.0-flash-exp'로 기재하세요.
    MODEL_NAME = "gemini-1.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"""
        당신은 용인시 건축 조례 및 법령 전문가입니다. 
        제공된 [참고 법규 데이터]를 최우선 근거로 사용하여 답변하십시오.

        [참고 법규 데이터]:
        {db_context if db_context else "직접적인 조례 데이터를 찾지 못했습니다. 일반적인 건축법령 지식에 기반하되 공식 확인이 필요함을 명시하십시오."}

        답변 규칙:
        1. 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.
        2. 질문의 성격에 따라 형식을 달리하십시오:
           - [사례 해석 및 규제 확인]: 구체적인 대지 조건이나 행위에 대한 질문은 반드시 아래 '6개 항목'을 지키십시오.
           - [단순 개념 및 용어 정의]: "용적률이 뭐야?"와 같은 단순 질문은 6개 항목을 따르지 말고, 가독성 좋은 일반 설명문 형식으로 답변하십시오.
        3. 6개 항목 구성 (사례 질문용):
           1. 결론
           2. 적용 지역 및 법적 위계
           3. 핵심 근거 조문
           4. 세부 해석 및 설명
           5. 추가 확인 사항 및 원문 링크 (제공된 link 활용)
           6. 담당 기관 및 후속 절차

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # [수정] 503 오류 발생 시 최대 3번 재시도하는 로직 추가
        max_retries = 3
        for i in range(max_retries):
            try:
                # [수정] 타임아웃을 100초로 상향 조정
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    text = response.json()['candidates'][0]['content']['parts'][0]['text']
                    # 기호 정제
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                # 503 오류일 경우 잠시 대기 후 재시도
                if response.status_code == 503:
                    if i < max_retries - 1:
                        time.sleep(2) # 2초 대기 후 재시도
                        continue
                
                return f"엔진 응답 실패: {response.status_code} / {response.text}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(2)
                    continue
                return "엔진 응답 시간 초과 (100초). 데이터 양을 조절하거나 다시 시도해 주세요."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
