import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    def safe_read_csv(file_path):
        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
        for enc in encodings:
            try: return pd.read_csv(file_path, encoding=enc)
            except: continue
        return None
    db_files = ["ordinance_basic.csv", "statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]
    return {f: df.fillna("") for f in db_files if os.path.exists(f) and (df := safe_read_csv(f)) is not None}

def extract_smart_snip(text, query, semantic_tags=""):
    """
    [완전 개편] 제1조(목적)를 건너뛰고 '시기', '주기', '점검' 등 실무 키워드가 
    집중된 실제 조문을 우선적으로 발췌합니다.
    """
    if not text: return ""
    
    # 조문 단위 분할
    pattern = r"(제\d+조(?:의\d+)?\s*\(.*?\))"
    sections = re.split(pattern, text)
    
    articles = []
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            header = sections[i]
            content = sections[i+1] if i+1 < len(sections) else ""
            articles.append(header + content)
    else:
        return text[:2000]

    # 실무 키워드 우선순위 (목적/정의 제외)
    search_keywords = [kw for kw in set(query.split() + semantic_tags.split(',')) if len(kw) > 1]
    priority_keywords = [kw for kw in search_keywords if kw not in ["건축물", "관리법", "조례", "목적", "정의"]]
    
    selected_articles = []
    # 1순위: 실무 키워드가 포함된 조항 검색
    for art in articles:
        if any(kw in art for kw in priority_keywords):
            selected_articles.append(art.strip())
        if len(selected_articles) >= 3: break
            
    # 2순위: 1순위가 없을 경우 일반 키워드로 검색
    if not selected_articles:
        for art in articles:
            if any(kw in art for kw in search_keywords):
                selected_articles.append(art.strip())
            if len(selected_articles) >= 2: break

    return "\n\n".join(selected_articles) if selected_articles else articles[0][:1500]

def get_ordinance_data(query, semantic_tags=""):
    dbs = load_all_databases()
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = [kw for kw in set(query.split() + tags_list) if len(kw) > 1]
    
    final_context, processed_sources, total_density_score = [], set(), 0
    # 임계치를 높여 더 많은 데이터를 수집하도록 유도
    SATISFACTION_THRESHOLD = 40 

    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "keywords": ["건축물관리", "건축 조례"]},
        {"label": "위임법령 핵심", "file": "statute.csv", "keywords": ["건축물관리법", "건축법"]},
        {"label": "조례 일반", "file": "ordinance_basic.csv", "region": "용인"},
        {"label": "위임법령", "file": "statute.csv", "all": True}
    ]

    for tier in tier_configs:
        # [핵심 변경] '위임법령' 티어는 점수와 상관없이 무조건 탐색을 수행함
        if total_density_score >= SATISFACTION_THRESHOLD and "위임법령" not in tier["label"]:
            continue
            
        files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        for f_name in files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            if "keywords" in tier:
                mask = df[name_col].apply(lambda x: any(k in str(x) for k in tier["keywords"]))
                target_df = df[mask]
            elif "region" in tier:
                target_df = df[df['region (지자체)'].str.contains(tier["region"], na=False) if 'region (지자체)' in df.columns else df.index == -1]
            else:
                target_df = df
            
            for _, row in target_df.iterrows():
                name = str(row[name_col])
                if name in processed_sources: continue
                content = str(row[content_col])
                
                if any(kw in name or kw in content for kw in combined_keywords):
                    # 실무 키워드가 본문에 있을 때 점수를 더 높게 부여
                    score = sum(15 if kw in name else 5 for kw in combined_keywords if kw in name or kw in content)
                    snip = extract_smart_snip(content, query, semantic_tags)
                    
                    if snip:
                        final_context.append(f"### [{tier['label']}] {name}\n{snip}")
                        processed_sources.add(name)
                        total_density_score += score
                    
                    if total_density_score >= 60: break # 하드 리밋

    if not final_context: return "NO_DATA", "검색 결과 없음"
    status = "COMPLETE" if total_density_score >= SATISFACTION_THRESHOLD else "INCOMPLETE"
    return status, "\n\n---\n\n".join(final_context)
