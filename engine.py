# engine.py
import streamlit as st
import requests
import json
import re
import time

def get_semantic_keywords(user_query):
    """[Step 1] 내부 검색 전략 수립을 위한 시맨틱 추출"""
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    analysis_prompt = f"질문: '{user_query}' / 이 질문과 관련된 법령 명칭과 전문 용어를 콤마(,)로 구분해서 5개만 나열해줘."
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip() if response.status_code == 200 else ""
    except: return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성:
    - 데이터베이스의 정보 부족 사실은 명시하되, 상세한 시스템 사정은 생략.
    - 일반 지식을 활용한 실질적 해답 제공에 집중.
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        # 데이터가 부족할 때: DB에 없다는 점을 짧게 고지하고 지식 동원
        status_instruction = """
        [데이터 보완 지침]
        제공된 데이터베이스에 직접적인 정보가 부족합니다.
        1. '### 세부 해석' 섹션의 첫 문장을 반드시 "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."로 시작하십시오.
        2. "데이터베이스에 해당 조항이 없다"는 사실은 언급해도 좋으나, 구체적으로 어떤 법이 누락되었는지 등 상세한 시스템 내부 사정은 민원인에게 설명하지 마십시오.
        3. 위 폴백(Fallback) 문구 고지 후에는 당신의 지식을 바탕으로 질문에 대한 명확한 해답을 상세히 기술하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 최우선 근거로 사용하여 답변하십시오."

    prompt = f"""
    사용자의 질문에 대해 아래 3개 항목으로 구성된 보고서를 작성하십시오.

    {status_instruction}

    [참조용 데이터베이스]: {db_context}
    [참조용 키워드]: {semantic_tags}

    작성 및 금지 규칙:
    1. 인삿말("민원인님~")과 자기소개("전문가로서~")를 절대 하지 마십시오. 바로 본론으로 시작합니다.
    2. 항목은 반드시 ### 결론, ### 핵심 근거, ### 세부 해석 3가지만 사용하십시오.
    3. '시맨틱 태그'나 '참조 키워드'와 같은 개발 시스템 용어는 절대 노출하지 마십시오.
    4. '### 핵심 근거'에는 질문과 관련된 상위 법령 명칭을 명확히 나열하십시오.
    5. '### 세부 해석'에서는 "알 수 없다"는 답변 대신, 일반 지식을 활용해 실질적인 정보와 해답을 상세히 기술하십시오.
    6. 별표(*)와 슬래시(/) 사용을 절대 금지합니다.

    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # 정제: 금지 기호 및 시스템 태그 흔적 제거
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                text = text.replace("*", "").replace("/", "")
                text = text.replace("[참조용 키워드]", "").replace("[시맨틱 태그]", "")
                return text.strip()
            time.sleep(2)
        except: continue
    return "시스템 응답에 실패했습니다. 잠시 후 다시 시도해 주세요."
