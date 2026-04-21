import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        # 깃허브 코드에는 키를 절대 적지 않습니다.
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 주소를 v1으로 고정합니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 지침 주입 (영어 금지, 별표 및 슬래시 금지)
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하세요. 별표나 슬래시 기호를 절대 사용하지 마세요. 질문: {user_query}"
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 인용구 및 금지 기호 최종 필터링
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            # 에러 발생 시 상세 메시지 출력
            error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
            return f"서버 응답 오류: {error_msg}"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
