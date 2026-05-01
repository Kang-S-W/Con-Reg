import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    """
    합의된 4개의 CSV 파일을 로드합니다.
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
    조문 단위(제N조)로 텍스트를 절삭합니다.
    """
    if not text: return ""
    
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    
    if intent_type == "overview" or not articles:
        end_idx = articles[3].start() if len(articles) > 3 else len(text)
        return text[:end_idx].strip()

    keywords = [kw for kw in query.split() if len(kw) > 1 and kw not in ["뭐야", "어떻게", "알려줘"]]
    hit_pos = -1
    for kw in keywords:
        pos = text.find(kw)
        if pos != -1:
            hit_pos = pos
            break
    
    if hit_pos == -1: return text[:1500]

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
    [지능형 탐색 엔진]
    1. 시맨틱 태그를 검색어에 통합하여 의미론적 검색 수행
    2. 데이터 밀도 점수(Satisfaction Score)를 계산하여 탐색 깊이 결정
    3. 탐색 결과의 충실도 상태(Status)를 함께 반환
    """
    dbs = load_all_databases()
    if not dbs: return "NO_DB", "데이터베이스 파일을 찾을 수 없습니다."

    # 1. 키워드 통합 및 정제
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = list(set(query.split() + tags_list))
    # 불용어 및 짧은 단어 필터링
    combined_keywords = [kw for kw in combined_keywords if len(kw) > 1 and kw not in ["뭐야", "시기", "방법"]]

    # 2. 질문 의도 판별
    overview_keywords = ["뭐야", "목적", "정의", "취지", "설명", "개요"]
    intent = "overview" if any(kw in query for kw in overview_keywords) else "detail"

    final_context = []
    processed_sources = set()
    
    # 3. 데이터 밀도 제어 설정
    total_density_score = 0
    SATISFACTION_THRESHOLD = 20  # 목표 점수 20점

    def calculate_row_score(name, content):
        """조문의 정보 가치를 점수화합니다."""
        score = 0
        for kw in combined_keywords:
            if kw in name: score += 10 # 법령 명칭(제목) 매칭 시 고점 부여
            if kw in content: score += 2 # 본문 매칭 시 가산점
        return score

    # 4. 정정된 5단계 폭포수 탐색 체계
    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "targets": ["용인시 건축 조례", "용인시 도시계획 조례"]},
        {"label": "위임법령 핵심", "file": "statute.csv", "targets": ["건축법", "건축법 시행령", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령"]},
        {"label": "조례 일반", "file": "ordinance_basic.csv", "region": "용인"},
        {"label": "위임법령", "file": "statute.csv", "all": True},
        {"label": "연관 법리", "file": ["ord_borrowed.csv", "stat_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        # 데이터 만족도 체크: 임계치 도달 시 탐색 중단 (무한 루프 및 과부하 방지)
        if total_density_score >= SATISFACTION_THRESHOLD:
            break
        
        target_files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        
        for f_name in target_files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            # 파일별 컬럼명 대응
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            # 필터링 로직 (핵심 법령 지정 또는 지자체 필터링)
            if "targets" in tier:
                target_df = df[df[name_col].isin(tier["targets"])]
            elif "region" in tier:
                target_df = df[df['region (지자체)'].str.contains(tier["region"], na=False) if 'region (지자체)' in df.columns else df.index == -1]
            else:
                target_df = df
            
            # 검색 및 점수 누적
            for _, row in target_df.iterrows():
                row_name = str(row[name_col])
                if row_name in processed_sources: continue
                
                row_content = str(row[content_col])
                # 제목이나 본문에 키워드가 포함된 경우만 처리
                if any(kw in row_name or kw in row_content for kw in combined_keywords):
                    score = calculate_row_score(row_name, row_content)
                    
                    if score > 0:
                        snip = extract_smart_snip(row_content, query, intent)
                        final_context.append(f"### [{tier['label']}] {row_name}\n{snip}")
                        processed_sources.add(row_name)
                        total_density_score += score
                        
                        # 티어 내 탐색 중 점수가 충족되면 즉시 중단
                        if total_density_score >= SATISFACTION_THRESHOLD:
                            break
            if total_density_score >= SATISFACTION_THRESHOLD:
                break

    # 5. 결과 반환 및 상태 결정
    if not final_context:
        return "NO_DATA", "데이터베이스에서 관련 조문을 찾을 수 없습니다."

    combined_context = "\n\n---\n\n".join(final_context)
    
    # 누적 점수가 임계치에 미달하면 INCOMPLETE 상태 반환
    if total_density_score < SATISFACTION_THRESHOLD:
        status = "INCOMPLETE"
        # AI가 인지할 수 있도록 컨텍스트 상단에 안내 삽입
        combined_context = f"[시스템 알림: 데이터 밀도 점수({total_density_score})가 부족함]\n{combined_context}"
    else:
        status = "COMPLETE"

    return status, combined_context
