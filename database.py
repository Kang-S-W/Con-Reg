import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    def safe_read_csv(file_path):
        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
        for enc in encodings:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except:
                continue
        return None

    db_files = ["ordinance_basic.csv", "statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]
    db_dict = {}
    for f in db_files:
        if os.path.exists(f):
            df = safe_read_csv(f)
            if df is not None:
                db_dict[f] = df.fillna("")
    return db_dict

def get_ordinance_data(query):
    dbs = load_all_databases()
    if not dbs:
        return "데이터베이스 파일을 찾을 수 없습니다."

    # 1. 파일별 열 이름 스키마 정의
    file_configs = {
        "ordinance_basic.csv": {"name": "ordinance (조례명)", "content": "content", "link": "link", "category": "Category (주제)"},
        "statute.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"},
        "ord_borrowed.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"},
        "stat_borrowed.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"}
    }

    # 2. [고도화] 키워드 전처리 (불용어 제거 및 핵심어 추출)
    # 질문에서 조사, 어미 등을 제거하고 의미 있는 명사 위주로 추출
    stop_words = ["뭐야", "알려줘", "알려주세요", "있어", "있나요", "어떻게", "대한", "의", "이", "가", "은", "는", "를", "을"]
    clean_query = re.sub(r'[^가-힣\s]', '', query) # 특수문자 제거
    keywords = [kw for kw in clean_query.split() if kw not in stop_words and len(kw) > 1]
    
    # 만약 키워드가 다 걸러졌다면 원본에서 단어 추출
    if not keywords:
        keywords = [kw for kw in query.split() if len(kw) > 1]

    is_urban_planning = any(kw in query for kw in ["용적률", "건폐율", "용도지역", "지구단위"])
    final_context = []
    processed_articles = set()

    # 3. [Tier 1] 핵심 6대 법령 정의
    tier1_names = [
        "용인시 건축 조례", "용인시 도시계획 조례", 
        "건축법", "건축법 시행령", 
        "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령"
    ]
    if is_urban_planning:
        tier1_names.insert(0, tier1_names.pop(tier1_names.index("용인시 도시계획 조례")))

    # 4. [개선된 검색 함수] 핵심 키워드 매칭 중심
    def optimized_search(file_list, label, max_results=3):
        for f_name in file_list:
            if f_name not in dbs: continue
            df = dbs[f_name]
            cfg = file_configs[f_name]
            
            # 핵심 키워드 중 하나라도 포함된 행 찾기 (OR 검색 후 점수 산정)
            # 여기서는 최소 절반 이상의 키워드가 포함된 경우를 검색
            match_threshold = max(1, len(keywords) // 2)
            
            def calculate_match(text):
                count = 0
                for kw in keywords:
                    if kw in text: count += 1
                return count

            df['match_score'] = df[cfg['content']].apply(calculate_match)
            res = df[df['match_score'] >= match_threshold].sort_values(by='match_score', ascending=False)

            for _, row in res.iterrows():
                art_name = row[cfg['name']]
                if art_name in processed_articles: continue
                
                snip = extract_article_snip(row[cfg['content']], keywords[0] if keywords else "")
                final_context.append(
                    f"### [{label}] {art_name}\n"
                    f"(분류: {row.get(cfg['category'], '일반')})\n{snip}\n"
                    f"링크: {row.get(cfg['link'], '정보 없음')}"
                )
                processed_articles.add(art_name)
                if len(final_context) >= 5: break

    # Tier 1 검색 (핵심 법령) - 질문에 법령 명칭이 포함된 경우 우선 검색
    for f_key in ["ordinance_basic.csv", "statute.csv"]:
        if f_key in dbs:
            df = dbs[f_key]
            cfg = file_configs[f_key]
            
            # 1순위: 조례명이 질문에 포함된 경우 해당 행은 무조건 검토
            for t_name in tier1_names:
                if t_name.replace(" ", "") in query.replace(" ", ""):
                    relevant_df = df[df[cfg['name']] == t_name]
                    for _, row in relevant_df.iterrows():
                        # 해당 조례 내에서 키워드 검색
                        if any(kw in row[cfg['content']] for kw in keywords):
                            snip = extract_article_snip(row[cfg['content']], keywords[0] if keywords else "")
                            final_context.append(f"### [최우선 근거: {t_name}] {row[cfg['name']]}\n{snip}")
                            processed_articles.add(row[cfg['name']])

    # Tier 2 & 3: 결과가 부족할 때만 확장 검색
    if len(final_context) < 3:
        optimized_search(["ordinance_basic.csv", "statute.csv"], "추가 참고 법규")
        optimized_search(["ord_borrowed.csv", "stat_borrowed.csv"], "연관/차용 법리")

    return "\n\n---\n\n".join(final_context) if final_context else None

def extract_article_snip(text, keyword):
    if pd.isna(text) or not text: return ""
    # 제N조 패턴 찾기
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    
    # 키워드가 있으면 키워드 위치를, 없으면 처음부터
    hit = text.find(keyword) if keyword else 0
    if hit == -1: hit = 0
    
    start_pos, end_pos = 0, len(text)
    for i, art in enumerate(articles):
        if art.start() <= hit:
            start_pos = art.start()
            if i + 1 < len(articles):
                end_pos = articles[i+1].start()
        else:
            break
    
    # '목적' 질문의 경우 제1조를 더 우선적으로 반환하도록 보정
    if "목적" in keyword and len(articles) > 0:
        if "목적" in text[articles[0].start():articles[0].end()]:
             start_pos = articles[0].start()
             end_pos = articles[1].start() if len(articles) > 1 else len(text)

    return text[start_pos:end_pos][:2000]
