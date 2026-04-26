import pandas as pd
import re
import os

def get_ordinance_data(query):
    # 파일 경로 정의
    files = {
        "basic": "ordinance_basic.csv",
        "statute": "statute.csv",
        "ord_borrow": "ord_borrowed.csv",
        "stat_borrow": "stat_borrowed.csv"
    }

    final_context = []
    
    def extract_article_snip(text, keyword):
        """방대한 원문에서 키워드가 포함된 특정 조문 구역만 잘라내는 함수"""
        # 조문 제목 패턴: 제N조(제목)
        pattern = r"제\d+조\s*\(.*?\)"
        articles = list(re.finditer(pattern, text))
        
        # 키워드 위치 확인
        hit = text.find(keyword)
        if hit == -1: return text[:2000] # 키워드 없으면 상단 2000자
        
        # 키워드가 속한 조문의 시작과 끝 찾기
        start_pos = 0
        end_pos = len(text)
        
        for i, art in enumerate(articles):
            if art.start() <= hit:
                start_pos = art.start()
                if i + 1 < len(articles):
                    end_pos = articles[i+1].start()
            else:
                break
        
        # 너무 짧거나 길 경우를 대비해 앞뒤 문맥 확보 (최대 2500자)
        return text[start_pos:end_pos][:2500]

    try:
        # [Step 1] 조례 기본 DB 검색 (가장 우선순위)
        if os.path.exists(files["basic"]):
            df_basic = pd.read_csv(files["basic"], encoding='utf-8-sig')
            # 띄어쓰기 무시 검색을 위해 주석: 조례명이나 내용에서 검색
            res_basic = df_basic[df_basic['content'].str.contains(query, na=False, case=False)]
            
            if not res_basic.empty:
                row = res_basic.iloc[0]
                snip = extract_article_snip(row['content'], query)
                final_context.append(f"### [용인시 조례] {row['ordinance']}\n(주제: {row['category']})\n{snip}\n출처: {row['link']}")
                
                # [Step 2] 차용/참조 관계 추적 (텍스트 내 「...」 법령명 추출)
                refs = re.findall(r"「(.*?)」", snip)
                for ref_name in set(refs):
                    # 법령 DB 및 차용 DB에서 재귀 검색
                    for f_key in ["statute", "ord_borrow", "stat_borrow"]:
                        df_ref = pd.read_csv(files[f_key], encoding='utf-8-sig')
                        res_ref = df_ref[df_ref['ordinance'].str.contains(ref_name, na=False, case=False)]
                        if not res_ref.empty:
                            r_row = res_ref.iloc[0]
                            final_context.append(f"### [연관 법령/차용 근거] {r_row['ordinance']}\n{r_row['content'][:1500]}")
                            break # 하나 찾으면 중단

        # [Step 3] 조례에 데이터가 아예 없는 경우 상위 법령 직접 검색
        if not final_context and os.path.exists(files["statute"]):
            df_stat = pd.read_csv(files["statute"], encoding='utf-8-sig')
            res_stat = df_stat[df_stat['content'].str.contains(query, na=False, case=False)]
            if not res_stat.empty:
                row = res_stat.iloc[0]
                final_context.append(f"### [상위 법령 직접 검색 결과] {row['ordinance']}\n{row['content'][:2000]}")

    except Exception as e:
        return f"데이터베이스 탐색 중 오류 발생: {str(e)}"

    return "\n\n---\n\n".join(final_context) if final_context else None
