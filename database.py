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
    if not text: return ""
    pattern = r"(제\d+조(?:의\d+)?\s*\([^)]*\))"
    sections = re.split(pattern, text)
    articles = []
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            articles.append(sections[i] + (sections[i+1] if i+1 < len(sections) else ""))
    else: return text[:1500]

    keywords = [kw for kw in set(query.split() + semantic_tags.split(',')) if len(kw) > 1]
    priority_kws = [k for k in keywords if k not in ["법", "조례", "목적", "정의"]]

    scored_articles = []
    for art in articles:
        score = sum(20 if kw in art else 0 for kw in priority_kws)
        if score > 0: scored_articles.append((score, art.strip()))
    
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([art for _, art in scored_articles[:3]]) if scored_articles else articles[0][:1000]

def get_ordinance_data(query, semantic_tags=""):
    dbs = load_all_databases()
    
    known_laws = set()
    for f_name, df in dbs.items():
        name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
        if name_col in df.columns:
            known_laws.update(df[name_col].dropna().unique().tolist())
            
    known_laws_sorted = sorted(list(known_laws), key=len, reverse=True)
    target_law_name = None
    query_no_space = query.replace(" ", "")
    
    for law in known_laws_sorted:
        if str(law).replace(" ", "") in query_no_space:
            target_law_name = str(law)
            break

    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = [kw for kw in set(query.split() + tags_list) if len(kw) > 1]
    
    if target_law_name:
        combined_keywords.append(target_law_name)

    final_context, processed_sources, total_density_score = [], set(), 0
    SATISFACTION_THRESHOLD = 35 

    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "keywords": ["용인", "건축 조례"]},
        {"label": "위임법령", "file": "statute.csv", "all": True},
        {"label": "차용 연관법규", "file": ["stat_borrowed.csv", "ord_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        is_core_tier = (tier['label'] == "조례 핵심")
        
        if total_density_score >= SATISFACTION_THRESHOLD and is_core_tier:
            continue
            
        files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        for f_name in files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            for _, row in df.iterrows():
                name = str(row[name_col])
                if name in processed_sources: continue
                
                if target_law_name and is_core_tier:
                    if target_law_name in df[name_col].values and name != target_law_name:
                        continue

                content = str(row[content_col])
                
                if any(kw in name or kw in content for kw in combined_keywords):
                    snip = extract_smart_snip(content, query, semantic_tags)
                    if len(snip) > 30:
                        final_context.append(f"### [{tier['label']}] {name}\n{snip}")
                        processed_sources.add(name)
                        total_density_score += 15 
                    
                    if total_density_score >= 80: break 
    
    status = "COMPLETE" if total_density_score >= SATISFACTION_THRESHOLD else "INCOMPLETE"
    return status, "\n\n---\n\n".join(final_context)

@st.cache_data
def load_law_links():
    path = "link.csv"
    if os.path.exists(path):
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                df = pd.read_csv(path, encoding=enc)
                df.columns = [c.strip() for c in df.columns]
                if '법규명' in df.columns and '원문링크' in df.columns:
                    links = {}
                    for k, v in zip(df['법규명'], df['원문링크']):
                        url = str(v).strip()
                        if url.startswith("www."):
                            url = "https:__" + url
                        links[str(k).strip()] = url.replace("_", chr(47))
                    return links
            except: continue
    return {}

@st.cache_data
def load_sitemap_db():
    path = "용인시청사이트맵.csv"
    if os.path.exists(path):
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                df = pd.read_csv(path, encoding=enc)
                df.columns = [c.strip() for c in df.columns]
                return df
            except:
                continue
    return None
