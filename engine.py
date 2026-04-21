import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 429 오류와 404 오류를 동시에 피하기 위해 1.5 Flash 모델로 고정합니다.
        # 무료 키에서 가장 작동 확률이 높은 v1beta 엔드포인트를 사용합니다.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 지침을 질문 본문에 직접 포함 (별표, 슬래시, 영어 병기 금지)
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 건축 조례 전문가입니다. 한국어로만 답변하세요. 별표나 슬래시 기호를 절대 사용하지 마세요. 인용 표시도 제거하세요. 질문: {user_query}"
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 불필요한 기호 최종 필터링
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            # 429 오류 발생 시 사용자에게 대기 시간을 안내합니다.
            error_detail = result.get('error', {}).get('message', '알 수 없는 오류')
            return f"시스템 일시 과부하: {error_detail}"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
