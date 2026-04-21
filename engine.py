import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # 시도해볼 모델과 주소의 조합들 (가장 확률 높은 순)
    endpoints = [
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-pro")
    ]
    
    instruction = """당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하세요. 
    1. 답변에 영어 번역을 절대 병기하지 마세요.
    2. 별표나 슬래시 기호를 절대 사용하지 마세요.
    3. [cite] 등 인용 표시를 모두 제거하세요.
    4. 단순 개념은 설명문으로, 사례는 1.결론~6.후속절차 항목으로 답하세요."""

    full_prompt = f"{instruction}\n\n질문: {user_query}"
    last_error = ""

    for ver, model in endpoints:
        try:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
            
            response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                text = result['candidates'][0]['content']['parts'][0]['text']
                # 특수기호 제거 필터링
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                text = text.replace("*", "").replace("/", "")
                return text
            else:
                last_error = result.get('error', {}).get('message', 'Unknown Error')
                continue # 다음 조합으로 넘어감
        except Exception as e:
            last_error = str(e)
            continue

    return f"모든 경로 시도 실패. 마지막 오류: {last_error}"
