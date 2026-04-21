import streamlit as st
import time

# 웹사이트 기본 설정
st.set_page_config(page_title="건축조례 AI 플랫폼", layout="wide")

# 사이드바 메뉴 구성
menu = st.sidebar.selectbox("메뉴 선택", ["프로젝트 개요", "데이터베이스 현황", "AI 규제 질의", "민원 연계 시스템"])

# 1. 프로젝트 개요 페이지
if menu == "프로젝트 개요":
    st.header("AI 기반 건축조례 지원 플랫폼")
    st.subheader("Al-Based Construction Regulation Support Platform")
    st.write("본 플랫폼은 건축 실무에서의 법령·조례 해석 비효율성을 해결하기 위한 목적으로 개발되었습니다[cite: 3].")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**주요 목표**\n1. 조례와 상위법령의 정합적 연결 [cite: 46]\n2. 자연어 질문의 구조화 [cite: 47]\n3. 근거 중심의 답변 생성 [cite: 51]")
    with col2:
        st.success("**기대 효과**\n- 조례 오인에 따른 경제적 손실 방지 [cite: 182]\n- 반복 민원 대응 부담 완화 [cite: 184]")

# 2. 데이터베이스 현황 페이지
elif menu == "데이터베이스 현황":
    st.header("법규 데이터베이스 구축 현황")
    st.write("용인시 및 경기도를 중심으로 총 125개의 법규 데이터가 구조화되어 있습니다.")
    
    st.table({
        "구분": ["조례 (용인/경기)", "위임 상위 법령", "의미 차용 법규"],
        "개수": ["7개 [cite: 474]", "13개 [cite: 477]", "105개 [cite: 479, 481]"],
        "주요 항목": ["건축 조례, 도시계획 조례 등", "건축법, 국토계획법 등", "민법, 지방세법 등"]
    })
    st.caption("ChromaDB 기반 벡터 데이터베이스로 구축 중입니다[cite: 536, 574].")

# 3. AI 규제 질의 페이지 (핵심 기능)
elif menu == "AI 규제 질의":
    st.header("AI 기반 건축 규제 분석")
    query = st.text_input("질문을 입력하세요 (예: 용인시 일조권 높이 제한은?)")
    
    if query:
        # 기획안의 8단계 분석 프로세스 시연 [cite: 92, 736]
        with st.status("단계별 법규 분석 수행 중...", expanded=True) as status:
            st.write("1~2. 질문 분석 및 지역 식별 중... [cite: 634, 636]")
            time.sleep(1)
            st.write("3~4. 조례 DB 선택 및 상위법령 매칭 중... [cite: 677, 664]")
            time.sleep(1)
            st.write("5~7. 조문 추출 및 불확실성 검토 중... [cite: 673, 666]")
            time.sleep(1)
            status.update(label="분석 완료", state="complete", expanded=False)
        
        # 6개 슬롯 표준 응답 스키마 출력 [cite: 131, 653]
        st.subheader("분석 결과")
        st.info("**1. 결론:** 높이 10m 이하 부분은 1.5m 이상 이격 필요 (시연용)")
        st.write("**2. 적용 지역:** 경기도 용인시 [cite: 134]")
        st.write("**3. 핵심 근거 조문:** 용인시 건축 조례 제36조 [cite: 135]")
        st.write("**4. 세부 설명:** 정북방향 대지경계선으로부터의 거리 준수 [cite: 136]")
        st.warning("**5. 추가 확인 항목:** 대상지의 용도지역 및 대지 현황 [cite: 138]")
        st.write("**6. 담당 기관 및 후속 절차:** 용인시청 건축과 안내 [cite: 139]")

# 4. 민원 연계 시스템 페이지
elif menu == "민원 연계 시스템":
    st.header("민원 연계 및 후속 절차")
    st.write("AI 분석 결과에 따라 관할 기관 문의나 민원 절차로 연결합니다[cite: 33, 57].")
    
    st.button("법령해석요청서 초안 자동 생성 [cite: 1636]")
    st.button("용인시 전자민원 창구 바로가기 [cite: 1630]")