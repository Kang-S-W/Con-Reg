import streamlit as st
import requests
import json
import re
import time
from database import load_law_links

def get_semantic_keywords(user_query):
    """[Step 1] 질문의 법률적 의도 분석"""
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

def apply_law_links(text):
    link_db = load_law_links()
    if not link_db:
        return text
    
    found_links = []
    # 비교용 텍스트 생성 (본문의 공백/특수문자 무시)
    clean_text = re.sub(r'[\s\.\,\(\)\[\]]', '', text)
    
    # 긴 이름부터 매칭 시도
    sorted_law_names = sorted(link_db.keys(), key=len, reverse=True)
    
    for law_name in sorted_law_names:
        law_name_no_space = law_name.replace(" ", "")
        
        if law_name_no_space in clean_text:
            url = link_db[law_name].strip()
            
            # [수정 핵심] 주소를 < > 로 감싸서 URL 끝의 ')'가 마크다운 구문과 섞이지 않게 보호합니다.
            # 또한 https:// 가 없는 경우 강제로 붙여주는 안전장치를 추가합니다.
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            link_entry = f"- **[{law_name}](<{url}>)**" 
            
            if link_entry not in found_links:
                found_links.append(link_entry)
    
    if found_links:
        link_section = "\n\n---\n\n### 🔗 관련 법령 원문 링크 (클릭 시 이동)\n\n" + "\n".join(found_links)
        return text + link_section
    return text

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성: 
    시스템 내부 사정(DB 구성 등)을 절대 언급하지 않는 '투명한 전문가' 모드입니다.
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # 데이터 충실도에 따른 보완 문구 결정
    fallback_header = ""
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        fallback_header = "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."

    prompt = f"""
    당신은 대한민국 행정 전문가입니다. 아래 지침을 엄격히 준수하여 보고서를 작성하십시오.

    [절대 금지 사항]
    - "제공된 데이터베이스에는 ~가 있다/없다"라는 말을 절대 하지 마십시오.
    - 시스템 내부 자료의 범위를 설명하거나 한계를 요약하는 문단을 만들지 마십시오.
    - [참조 데이터]와 같은 기술 용어를 본문에 노출하지 마십시오.

    [작성 가이드]
    1. ### 결론, ### 핵심 근거, ### 세부 해석 3개 항목만 사용하십시오.
    2. '세부 해석'의 첫 문장은 반드시 다음과 같이 시작하십시오: {fallback_header if fallback_header else "확인된 법규 데이터를 바탕으로 상세 해석을 제공합니다."}
    3. 당신이 보유한 모든 지식을 동원하여 실무적인 해답을 제공하십시오.
    4. 별표(*)와 슬래시(/)를 사용하지 마십시오.

    [참조 데이터]: {db_context}
    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # [안정성] 5회 재시도 로직 포함
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # [정제] 대괄호 태그 및 불필요한 메타 설명 제거
                text = re.sub(r"\[.*?\]", "", text)
                text = text.replace("*", "").replace("/", "")
                
                # AI가 습관적으로 뱉는 메타 문구 강제 삭제
                meta_trash = ["제공된 데이터베이스", "법령 자료는", "포함하고 있지 않습니다", "확인할 수 없습니다"]
                for trash in meta_trash:
                    text = text.replace(trash, "")
                
                # 기존: return text.strip()
                processed_text = text.strip()
                return apply_law_links(processed_text)
            time.sleep(2)
        except: continue
    return "시스템 엔진 응답 실패. 잠시 후 다시 시도해 주세요."
