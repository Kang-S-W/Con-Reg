import streamlit as st
import requests

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 현재 API 키로 접근 가능한 모든 모델 리스트를 요청합니다.
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            # 모델 이름들만 추출 (예: models/gemini-1.5-flash)
            model_list = [m['name'] for m in result.get('models', [])]
            if not model_list:
                return "현재 키로 접근 가능한 모델이 하나도 없습니다. API 활성화를 확인하세요."
            
            # 리스트를 보기 좋게 출력
            return "✅ 접근 가능한 모델 리스트:\n" + "\n".join(model_list)
        else:
            return f"❌ 리스트 호출 실패: {result.get('error', {}).get('message')}"

    except Exception as e:
        return f"❌ 진단 중 오류 발생: {str(e)}"
