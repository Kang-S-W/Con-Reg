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
    [핀포인트 추출] 모든 조문을 검토하여 검색어 밀도가 가장 높은 핵심 조항을 반환합니다.
    """
    if not text: return ""
    
    # 조문 단위로 강제 분할
    pattern = r"(제\d+조(?:의\d+)?\s*\(.*?\))"
    raw_sections = re.split(pattern, text)
    
    articles = []
    if len(raw_sections) > 1:
        for i in range(1, len(raw_sections), 2):
            header = raw_sections[i]
            body = raw_sections[i+1] if i+1 < len(raw_sections) else ""
            articles.append(header + body)
    else:
        return text[:1500]

    # 가중치 키워드 (목적, 정의 등 서술적 단어는 배제)
    search_keywords = [kw for kw in set(query.split() + semantic_tags.split(',')) if len(kw) > 1]
    priority_keywords = [kw for kw in search_keywords if kw not in ["건축물", "관리법", "조례", "목적", "정의"]]

    scored_articles = []
    for art in articles:
        # 실무 키워드가 포함될수록 높은 점수 부여
        score = sum(20 if kw in art else 0 for kw in priority_keywords)
        # 조문 번호가 뒤쪽일수록(실무 조항일 확률) 약간의 가중치
        if score > 0:
            scored_articles.append((score, art.strip()))

    # 점수 높은 순으로 정렬 후 상위 2~3개 조항만 결합
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_articles = [art for _, art in scored_articles[:3]]

    return "\n\n".join(top_articles) if top_articles else articles[0][:1000]

def get_ordinance_data(query, semantic_tags=""):
    dbs = load_all_databases()
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = [kw for kw in set(query.split() + tags_list) if len(kw) > 1]
    
    final_context, processed_sources, total_density_score = [], set(), 0
    # 임계치를 대폭 상향하여 더 깊게 탐색
    SATISFACTION_THRESHOLD = 40 

    tier_configs = [
        # 조례보다 법령(Statute)에 더 높은 우선순위를 부여할 수 있도록 구성
        {"label": "위임법령 핵심", "file": "statute.csv", "keywords": ["건축물관리법", "시행령"]},
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "keywords": ["건축물관리", "용인시"]},
        {"label": "기타 법령", "file": ["statute.csv", "stat_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        # '핵심'이 들어간 데이터는 점수가 충분해도 무조건 훑음
        if total_density_score >= SATISFACTION_THRESHOLD and "핵심" not in tier["label"]:
            continue
            
        files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        for f_name in files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            # 필터링 및 탐색
            if "keywords" in tier:
                mask = df[name_col].apply(lambda x: any(k in str(x) for k in tier["keywords"]))
                target_df = df[mask]
            else:
                target_df = df
            
            for _, row in target_df.iterrows():
                name = str(row[name_col])
                if name in processed_sources: continue
                content = str(row[content_col])
                
                if any(kw in name or kw in content for kw in combined_keywords):
                    snip = extract_smart_snip(content, query, semantic_tags)
                    # 실제 가치 있는 조문(snip)이 추출되었을 때만 결과에 추가
                    if len(snip) > 50:
                        final_context.append(f"### [{tier['label']}] {name}\n{snip}")
                        processed_sources.add(name)
                        total_density_score += 20 # 조문 확보 시 큰 점수 부여
                    
                    if total_density_score >= 80: break # 하드 리밋

    if not final_context: return "NO_DATA", "검색 결과 없음"
    return "COMPLETE", "\n\n---\n\n".join(final_context)
