import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    """합의된 4개의 CSV 파일을 로드합니다."""
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

def extract_smart_snip(text, query, intent_type="detail"):
    """
    조문 단위(제N조)로 텍스트를 절삭합니다.
    - intent_type="overview": 제1조(목적)부터 도입부 추출
    - intent_type="detail": 키워드가 포함된 해당 조항 추출
    """
    if not text: return ""
    
    # 조문 시작 패턴 (예: 제1조(목적))
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    
    if intent_type == "overview" or not articles:
        # 개요 질문이면 문서 시작부터 약 3개 조항 또는 2000자 반환
        end_idx = articles[3].start() if len(articles) > 3 else len(text)
        return text[:end_idx].strip()

    # 상세 질문: 키워드가 등장하는 가장 적절한 조항 탐색
    # 불용어를 제외한 핵심 단어 추출
    keywords = [kw for kw in query.split() if len(kw) > 1 and kw not in ["뭐야", "어떻게", "알려줘"]]
    hit_pos = -1
    for kw in keywords:
        pos = text.find(kw)
        if pos != -1:
            hit_pos = pos
            break
    
    if hit_pos == -1: return text[:1500] # 키워드 못 찾으면 상단 반환

    # 키워드가 포함된 조항의 시작과 끝 찾기
    start_pos = 0
    end_pos = len(text)
    for i, art in enumerate(articles):
        if art.start() <= hit_pos:
            start_pos = art.start()
            if i + 1 < len(articles):
                end_pos = articles[i+1].start()
        else:
            break
            
    return text[start_pos:end_pos].strip()

def get_ordinance_data(query):
    dbs = load_all_databases()
    if not dbs: return "데이터베이스 파일을 찾을 수 없습니다."

    # 1. 질문 의도 파악 (단순 키워드 라우팅)
    overview_keywords = ["뭐야", "목적", "정의", "취지", "설명", "개요"]
    intent = "overview" if any(kw in query for kw in overview_keywords) else "detail"

    # 2. 핵심 6대 법령 정의
    tier1_names = ["용인시 건축 조례", "용인시 도시계획 조례"]
    tier2_names = ["건축법", "건축법 시행령", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령"]

    final_context = []
    processed_sources = set()

    def search_in_df(df, name_col, content_col, target_names=None, region=None):
        """특정 조건에 맞는 행을 찾아 결과에 추가"""
        mask = pd.Series(True, index=df.index)
        if target_names:
            mask &= df[name_col].isin(target_names)
        if region:
            mask &= (df['region (지자체)'].str.contains(region) if 'region (지자체)' in df.columns else False)
        
        res = df[mask]
        for _, row in res.iterrows():
            source_id = f"{row[name_col]}"
            if source_id in processed_sources: continue
            
            # 본문 내 키워드 존재 확인 (상세 질문일 경우)
            content = row[content_col]
            if intent == "detail" and not any(kw in content for kw in query.split() if len(kw) > 1):
                continue

            snip = extract_smart_snip(content, query, intent)
            final_context.append(f"### [근거 법규] {row[name_col]}\n{snip}")
            processed_sources.add(source_id)
            if len(final_context) >= 3: return True
        return False

    # 3. 5단계 폭포수 탐색 실행
    # Tier 1: 용인 핵심 2종 (ordinance_basic.csv)
    if "ordinance_basic.csv" in dbs:
        search_in_df(dbs["ordinance_basic.csv"], "ordinance (조례명)", "content", target_names=tier1_names)

    # Tier 2: 국가 핵심 4종 (statute.csv)
    if len(final_context) < 3 and "statute.csv" in dbs:
        search_in_df(dbs["statute.csv"], "Ordinance(법규명)", "Content(원문)", target_names=tier2_names)

    # Tier 3: 용인 일반 조례 (ordinance_basic.csv 중 region='용인시')
    if len(final_context) < 3 and "ordinance_basic.csv" in dbs:
        search_in_df(dbs["ordinance_basic.csv"], "ordinance (조례명)", "content", region="용인")

    # Tier 4: 경기도 및 국가 일반 (statute.csv)
    if len(final_context) < 3 and "statute.csv" in dbs:
        search_in_df(dbs["statute.csv"], "Ordinance(법규명)", "Content(원문)")

    # Tier 5: 차용 법리 (borrowed 파일들)
    if len(final_context) < 2:
        for f in ["ord_borrowed.csv", "stat_borrowed.csv"]:
            if f in dbs:
                search_in_df(dbs[f], "Ordinance(법규명)", "Content(원문)")

    return "\n\n---\n\n".join(final_context) if final_context else "관련된 법령 조항을 찾을 수 없습니다."
