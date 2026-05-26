import streamlit as st
import requests
import json
import re
import time
from database import load_law_links
from database import load_sitemap_db

def get_semantic_keywords(user_query):
    """[Step 1] 질문의 법률적 의도 분석"""
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    analysis_prompt = f"질문: '{user_query}' \n 이 질문과 관련된 법령 명칭과 전문 용어를 콤마(,)로 구분해서 5개만 나열한다."
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip() if response.status_code == 200 else ""
    except: return ""

def apply_law_links(text):
    link_db = load_law_links()
    if not link_db: return text
    
    found_links = []
    clean_text = re.sub(r'[\s\.\,\(\)\[\]]', '', text)
    sorted_law_names = sorted(link_db.keys(), key=len, reverse=True)
    
    for law_name in sorted_law_names:
        law_name_no_space = law_name.replace(" ", "")
        if law_name_no_space in clean_text:
            url = link_db[law_name].strip()
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            link_entry = f"- [{law_name}]|||{url}|||"
            if link_entry not in found_links:
                found_links.append(link_entry)
    
    if found_links:
        link_section = "\n\n---\n\n### 관련 법령 원문 링크\n\n" + "\n".join(found_links)
        return text + link_section
    return text

def get_relevant_sitemap(user_query):
    """
    용인시청 사이트맵 DB에서 사용자의 질문과 가장 관련성이 높은 메뉴를 독립적으로 추론합니다.
    """
    df = load_sitemap_db()
    if df is None or df.empty:
        return ""
        
    sitemap_context = []
    for idx, row in df.iterrows():
        sitemap_context.append({
            "index": idx,
            "menu": row['menu (메뉴명)'],
            "function": row['function (기능)']
        })
    
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
당신은 용인시청 행정 시스템 안내 전문가다.
다음은 용인시청 홈페이지의 건축 민원 관련 행정 사이트맵 데이터다:

{json.dumps(sitemap_context, ensure_ascii=False, indent=2)}

[사용자 민원 질문]:
"{user_query}"

위 사용자 질문의 의도와 행정 목적을 분석하여, 민원을 해결하기 위해 접속해야 하는 가장 밀접한 행정 웹페이지를 최대 2개 선택한다.
만약 질문과 연관된 행정 메뉴가 전혀 없다면 빈 리스트 []를 반환한다.

반드시 아래 JSON 형식으로만 답변하고 어떠한 서론이나 추가 설명도 포함하지 않는다:
[
  {{"index": 선택한_메뉴의_index, "reason": "선택한 행정적 이유"}}
]
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        if response.status_code == 200:
            result_text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            selected_items = json.loads(result_text)
            found_links = []
            
            for item in selected_items:
                idx = int(item["index"])
                if 0 <= idx < len(df):
                    menu_path = df.iloc[idx]['menu (메뉴명)'].strip()
                    menu_name = menu_path.split(">")[-1].strip() 
                    link = df.iloc[idx]['link (링크)'].strip()
                    
                    if not link.startswith(('http://', 'https://')):
                        link = 'https://' + link
                        
                    found_links.append(f"- **{menu_name} 안내 웹페이지 바로가기**: [{menu_path}]|||{link}|||")
            
            if found_links:
                return "\n\n---\n\n### 용인시청 홈페이지 행정 서비스 연계\n" + "\n".join(found_links)
    except Exception as e:
        st.error(f"사이트맵 내부 추론 오류 발생: {e}")
        return ""
        
    return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성 (잠정적 답변 제공 및 단서 조항 추가)
    """
    import streamlit as st
    import requests
    import json
    import re
    import time
    
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    fallback_header = ""
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        fallback_header = "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변한다."

    prompt = f"""
    당신은 대한민국 건축 행정 전문가다. 아래 지침을 엄격히 준수하여 보고서를 작성한다.

    [절대 금지 사항]
    - "제공된 데이터베이스에는 ~가 있다 없다"라는 말을 절대 하지 않는다.
    - 시스템 내부 자료의 범위를 설명하거나 한계를 요약하는 문단을 만들지 않는다.
    - 영어 번역이나 괄호 병기 표기를 제목 및 소제목에 포함하지 않는다.
    - [참조 데이터]와 같은 기술 용어를 본문에 노출하지 않는다.

    [작성 가이드]
    1. 서술어는 반드시 '~다', '~한다' 형태의 객관적인 문서체로 끝맺는다.
    2. 제목은 ### 결론, ### 핵심 근거, ### 세부 해석 3개 항목만 사용한다.
    3. '세부 해석'의 첫 문장은 반드시 다음과 같이 시작한다: {fallback_header if fallback_header else "확인된 법규 데이터를 바탕으로 상세 해석을 제공한다."}
    4. 당신이 보유한 모든 지식을 동원하여 실무적인 해답을 제공한다.

    [조건부 답변 및 단서 조항 시스템]
    1. (조건부 판단) 제공된 [참조 데이터]가 특정 조건(용도지역, 대지 면적, 층수 등)에 따라 기준이 다르게 적용되는 분기형 조항인지 확인한다.
    2. (잠정적 답변 제공) 사용자의 [질문]에 필수 조건이 누락되어 있더라도 절대 답변을 거부하지 않는다. 확인 가능한 원칙, 가장 일반적인 기준, 또는 조건별 경우의 수를 요약하여 우선적으로 '결론'과 '세부 해석'을 온전하게 제공한다.
    3. (안전장치 및 역질문) 답변을 제공한 후, '세부 해석'의 가장 마지막에 반드시 다음과 같은 형식의 단서 조항을 추가한다: "다만, 본 규정은 [누락된 조건]에 따라 적용 기준이 달라질 수 있다. 정확한 행정 해석을 위해 대상지의 [누락된 조건]을 추가로 제시하기 바란다."

    [참조 데이터]: {db_context}
    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                text = re.sub(r"\[.*?\]", "", text)
                text = text.replace("*", "").replace("/", "")
                
                meta_trash = ["제공된 데이터베이스", "법령 자료는", "포함하고 있지 않습니다", "확인할 수 없습니다"]
                for trash in meta_trash:
                    text = text.replace(trash, "")
                
                processed_text = text.strip()
                
                final_text = apply_law_links(processed_text)
                sitemap_text = get_relevant_sitemap(user_query)
                
                return final_text + sitemap_text
            time.sleep(2)
        except: continue
    return "시스템 엔진 응답 실패. 잠시 후 다시 시도해 주기 바랍니다. 응답가능시간인 100초 이내 실패시 질문 내용을 구체화하시기 바랍니다"
