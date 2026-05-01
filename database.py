import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    """
    [데이터 로드 레이어]
    합의된 4개의 핵심 CSV 파일을 다양한 인코딩으로 안전하게 로드합니다.
    """
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
    [텍스트 정제 레이어]
    법령의 특성(제N조)을 반영하여 사용자 질문과 가장 밀접한 조문 단위를 절삭합니다.
    """
    if not text: return ""
    
    # 조문 시작 패턴 (예: 제1조(목적))
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    
    # 개요 질문이거나 조문 구분이 없는 경우 상단부 추출
    if intent_type == "overview" or not articles:
        end_idx = articles[3].start() if len(articles) > 3 else len(text)
        return text[:end_idx].strip()

    # 상세 질문: 키워드가 등장하는 조항을 정밀 탐색
    keywords = [kw for kw in query.split() if len(kw) > 1 and kw not in ["뭐야", "어떻게", "알려줘"]]
    hit_pos = -1
    for kw in keywords:
        pos = text.find(kw)
        if pos != -1:
            hit_pos = pos
            break
    
    if hit_pos == -1: return text[:1500] # 키워드 미발견 시 상단 1500자 반환

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

def get_ordinance_data(query, semantic_tags=""):
    """
    [심층 탐색 엔진]
    1. 시맨틱 태그 통합: engine.py에서 도출한 법률 단서를 검색어에 포함
    2. 데이터 밀도 제어: 누적 점수가 임계치(20점)에 도달할 때까지 5단계 폭포수 탐색
    3. 상태값 반환: 충실도(COMPLETE/INCOMPLETE)를 판별하여 AI의 답변 톤 결정
    """
    dbs = load_all_databases()
    if not dbs: return "NO_DB", "데이터베이스 파일을 찾을 수 없습니다."

    # 1. 시맨틱 레이어 연동 및 검색어 정제
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = list(set(query.split() + tags_list))
    combined_keywords = [kw for kw in combined_keywords if len(kw) > 1 and kw not in ["뭐야", "시기", "방법"]]

    # 2. 질문 의도 판별
    overview_keywords = ["뭐야", "목적", "정의", "취지", "설명", "개요"]
    intent = "overview" if any(kw in query for kw in overview_keywords) else "detail"

    final_context = []
    processed_sources = set()
    
    # 3. 데이터 만족도(밀도) 관리 변수
    total_density_score = 0
    SATISFACTION_THRESHOLD = 20 # 20점 도달 시 "충분한 정보"로 간주

    def calculate_row_score(name, content):
        """조문의 법률적 적합도를 수치화 (법령명 일치 시 가중치 5배)"""
        score = 0
        for kw in combined_keywords:
            if kw in name: score += 10 # 핵심 법령 명칭 매칭
            if kw in content: score += 2 # 본문 내 키워드 포함
        return score

    # 4. 5단계 폭포수 탐색 체계 (조례 및 위임법령 정계 정립)
    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "targets": ["용인시 건축 조례", "용인시 도시계획 조례"]},
        {"label": "위임법령 핵심", "file": "statute.csv", "targets": ["건축법", "건축법 시행령", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령"]},
        {"label": "조례 일반", "file": "ordinance_basic.csv", "region": "용인"},
        {"label": "위임법령", "file": "statute.csv", "all": True},
        {"label": "연관 법리", "file": ["ord_borrowed.csv", "stat_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        # 이미 충분한 정보 밀도를 확보했다면 하위 티어 탐색 생략 (최적화)
        if total_density_score >= SATISFACTION_THRESHOLD:
            break
        
        target_files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        
        for f_name in target_files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            
            # DB 파일별 컬럼 규격 대응
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            # 티어별 필터링 (명칭 기반 또는 지역 기반)
            if "targets" in tier:
                target_df = df[df[name_col].isin(tier["targets"])]
            elif "region" in tier:
                target_df = df[df['region (지자체)'].str.contains(tier["region"], na=False) if 'region (지자체)' in df.columns else df.index == -1]
            else:
                target_df = df
            
            # 유효 행 탐색 및 점수 합산
            for _, row in target_df.iterrows():
                row_name = str(row[name_col])
                if row_name in processed_sources: continue
                
                row_content = str(row[content_col])
                if any(kw in row_name or kw in row_content for kw in combined_keywords):
                    score = calculate_row_score(row_name, row_content)
                    
                    if score > 0:
                        snip = extract_smart_snip(row_content, query, intent)
                        final_context.append(f"### [{tier['label']}] {row_name}\n{snip}")
                        processed_sources.add(row_name)
                        total_density_score += score
                        
                        # 탐색 도중 임계치 도달 시 즉시 중단 (과부하 방지)
                        if total_density_score >= SATISFACTION_THRESHOLD:
                            break
            if total_density_score >= SATISFACTION_THRESHOLD:
                break

    # 5. 상태값(Status) 판별 및 결과 반환
    if not final_context:
        return "NO_DATA", "데이터베이스에서 관련 조문을 찾을 수 없습니다."

    combined_context = "\n\n---\n\n".join(final_context)
    
    # 점수에 따른 데이터 충실도 판단
    if total_density_score < SATISFACTION_THRESHOLD:
        status = "INCOMPLETE" # AI가 일반 지식으로 보완하도록 유도
        combined_context = f"[시스템 알림: 데이터 밀도 점수({total_density_score})가 기준치 미달임]\n{combined_context}"
    else:
        status = "COMPLETE" # DB 내용 중심의 전문 답변 유도

    return status, combined_context
