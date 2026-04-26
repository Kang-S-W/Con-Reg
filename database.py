import pandas as pd
import re
import os

def get_ordinance_data(query):
    # 1. 각 파일별 실제 열 이름 매핑 (승욱 님의 파일 분석 결과 반영)
    file_configs = {
        "ordinance_basic.csv": {
            "name": "ordinance (조례명)",
            "content": "content",
            "link": "link",
            "category": "Category (주제)"
        },
        "statute.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        },
        "ord_borrowed.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        },
        "stat_borrowed.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        }
    }

    final_context = []
    
    def extract_article_snip(text, keyword):
        """방대한 원문에서 키워드 주변 조문만 추출하는 함수"""
        if pd.isna(text) or not text:
            return ""
        
        # 조문 제목 패턴 (제N조...)
        pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
        articles = list(re.finditer(pattern, text))
        
        hit = text.find(keyword)
        if hit == -1:
            return text[:2000] # 키워드 없으면 상단 2000자 반환
        
        start_pos, end_pos = 0, len(text)
        for i, art in enumerate(articles):
            if art.start() <= hit:
                start_pos = art.start()
                if i + 1 < len(articles):
                    end_pos = articles[i+1].start()
            else:
                break
        
        return text[start_pos:end_pos][:2500]

    try:
        # [Step 1] 조례 기본 DB 검색
        f_basic = "ordinance_basic.csv"
        if os.path.exists(f_basic):
            cfg = file_configs[f_basic]
            df = pd.read_csv(f_basic, encoding='utf-8-sig')
            
            # 결측치 제거 및 문자열 변환
            df[cfg['content']] = df[cfg['content']].fillna("")
            
            # 검색 수행
            res = df[df[cfg['content']].str.contains(query, na=False, case=False)]
            
            if not res.empty:
                row = res.iloc[0]
                snip = extract_article_snip(row[cfg['content']], query)
                final_context.append(
                    f"### [용인시/경기도 조례] {row[cfg['name']]}\n"
                    f"(주제: {row[cfg['category']]})\n{snip}\n"
                    f"링크: {row[cfg['link']]}"
                )
                
                # [Step 2] 차용 관계 추적 (문막 내 「...」 법령명 추출)
                refs = re.findall(r"「(.*?)」", snip)
                for ref_name in set(refs):
                    for f_other in ["statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]:
                        if os.path.exists(f_other):
                            cfg_o = file_configs[f_other]
                            df_o = pd.read_csv(f_other, encoding='utf-8-sig')
                            df_o[cfg_o['name']] = df_o[cfg_o['name']].fillna("")
                            
                            res_o = df_o[df_o[cfg_o['name']].str.contains(ref_name, na=False, case=False)]
                            if not res_o.empty:
                                r_row = res_o.iloc[0]
                                r_content = r_row[cfg_o['content']]
                                r_snip = extract_article_snip(r_content, query) if not pd.isna(r_content) else "상세 내용 없음"
                                final_context.append(f"### [연관/차용 법규] {r_row[cfg_o['name']]}\n{r_snip}")
                                break

        # [Step 3] 조례에 결과가 없을 경우 법령 DB 직접 검색
        if not final_context and os.path.exists("statute.csv"):
            cfg_s = file_configs["statute.csv"]
            df_s = pd.read_csv("statute.csv", encoding='utf-8-sig')
            df_s[cfg_s['content']] = df_s[cfg_s['content']].fillna("")
            
            res_s = df_s[df_s[cfg_s['content']].str.contains(query, na=False, case=False)]
            if not res_s.empty:
                row = res_s.iloc[0]
                final_context.append(f"### [상위 법령 검색 결과] {row[cfg_s['name']]}\n{row[cfg_s['content']][:2000]}")

    except Exception as e:
        # 에러 발생 시 로그를 정확히 반환하여 디버깅을 돕습니다.
        return f"DB 탐색 중 에러 발생: {str(e)}"

    return "\n\n---\n\n".join(final_context) if final_context else None
