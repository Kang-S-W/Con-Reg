import streamlit as st
import requests
import json
import re
import time

# [추가] 1단계: 질문에서 법률적 단서(시맨틱 키워드)를 추출하는 함수
def get_semantic_keywords(user_query):
    """
    사용자의 질문을 분석하여 DB 검색에 최적화된 법령 명칭과 전문 용어를 도출합니다.
    """
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # AI가 검색 전략가로서 키워드를 뽑아내도록 유도하는 프롬프트
    analysis_prompt = f"""
    질문: '{user_query}'
    위 질문을 분석하여 대한민국 법규 데이터베이스에서 정보를 찾기 위한 핵심 검색어 5개를 뽑아주세요.
    반드시 관련 법령 명칭(예: 건축물관리법)과 행정 전문 용어(예: 사용승인일)를 포함해야 합니다.
    결과는 반드시 콤마(,)로만 구분된 단어 리스트로 출력하십시오. (예: 건축물관리법,정기점검,사용승인일,유지관리,안전점검)
    """
    
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            result = response.json()
            tags = result['candidates'][0]['content']['parts'][0]['text']
            return tags.strip()
    except Exception:
        return "" # 실패 시 빈 문자열 반환 (기본 검색으로 폴백)
    return ""

# [개선] 2단계: DB 컨텍스트와 시맨틱 태그를 결합하여 최종 답변 생성
def get_gemini_response(user_query, db_context="", semantic_tags=""):
    MODEL_NAME = "gemini-2.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        # [프롬프트 고도화] 시맨틱 분석 결과와 DB 한계 인정 로직 통합
        prompt = f"""
        당신은 '용인시 건축 조례 전문 해석 AI 플랫폼'의 행정 전문가입니다. 
        제공된 [참고 법규 데이터]와 [법률 분석 태그]를 바탕으로 답변하십시오.

        [법률 분석 태그]: {semantic_tags if semantic_tags else "분석 정보 없음"}
        [참고 법규 데이터]:
        {db_context if db_context else "해당 질문과 관련된 직접적인 조문이 데이터베이스에 존재하지 않습니다."}

        답변 생성 가이드라인:
        1. [DB 우선 및 한계 명기]: 
           - 데이터베이스에 질문과 관련된 간접적인 언급이 있다면 반드시 '핵심 근거'에 포함하십시오.
           - 데이터베이스 정보만으로 답변이 완전하지 않을 경우, 세부 해석 도입부에 반드시 다음 문구를 명시하십시오:
             "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."

        2. [지능형 보완]: 
           - 위 문구 명시 후, [법률 분석 태그]에 명시된 관련 법령 지식을 활용하여 질문에 대한 명확한 해답을 제공하십시오.

        3. [형식 엄수]:
           - 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.
           - 다음 6개 항목 구성을 유지하십시오: 결론, 적용 지역, 핵심 근거, 세부 해석, 원문 링크, 담당 기관.

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # [핵심] 자동 재시도 로직
        max_retries = 5 
        for i in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    # 불필요한 태그 및 금지 기호 제거
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                if response.status_code == 429:
                    time.sleep(2)
                    continue

                if response.status_code == 503:
                    if i < max_retries - 1:
                        wait_time = (i + 1) * 3
                        time.sleep(wait_time)
                        continue
                
                return f"엔진 응답 실패: {response.status_code} / {response.text}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(3)
                    continue
                return "엔진 응답 시간 초과 (100초). 다시 시도해 주세요."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
