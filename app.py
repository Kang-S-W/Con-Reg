import streamlit as st
import time
from engine import get_gemini_response
from database import get_ordinance_data

# 페이지 설정 (최상단에 한 번만 실행)
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# 디자인 서식 적용
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    .report-card { padding: 25px; border-radius: 8px; background-color: #ffffff; border: 1px solid #eeeeee; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# 좌측 사이드바 구성
with st.sidebar:
    st.title("플랫폼 제어")
    st.success("시스템 정상 작동")
    st.divider()
    
    st.subheader("시스템 메뉴")
    st.button("화면 모드 전환")
    st.button("플랫폼 가동 현황")
    st.button("데이터 관리 화면")
    st.divider()
    
    st.subheader("대화 이력")
    st.caption("건축선 후퇴 거리 문의")
    st.caption("용인시 일조권 이격 거리")
    st.divider()
    st.button("사용자 접속 및 등록")

# 상단 제목
st.title("건축 조례 및 법령 해석 지원 플랫폼")

# 상단 메뉴 4개 유지
tab_list = ["1. 프로젝트 개요", "2. 인공지능 분석", "3. 건축 시뮬레이션", "4. 민원 양식 생성"]
tabs = st.tabs(tab_list)

# 1. 프로젝트 개요
with tabs[0]:
    st.header("프로젝트 개요")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 프로젝트 목적")
        st.write("건축 실무 현장에서 반복되는 법령 및 조례 해석의 비효율성을 개선하고자 합니다.")
        st.write("조례를 잘못 해석하여 발생하는 행정 불이익과 경제적 손실을 방지하는 것을 핵심 목표로 합니다.")
    
    with col2:
        st.subheader("2. 프로젝트 범위")
        st.write("지역 범위 : 경기도 용인시를 1차적 대상으로 합니다.")
        st.write("데이터 범위 : 용인시 조례와 경기도 조례, 그 상위 법령 13개와 차용법규 125개 규정을 통합합니다.")

    st.subheader("3. 시스템 운영 체계")
    st.write("질문 분석부터 근거 추출 및 불확실성 검토까지 이어지는 8단계 공정을 거쳐 답변을 생성합니다.")

# 2. 인공지능 분석
with tabs[1]:
    st.header("인공지능 규제 분석")
    # 탭 내부의 단일 입력창
    user_query = st.chat_input("분석이 필요한 건축 규제에 대해 입력해 주세요")
    
    if user_query:
        # 8단계 분석 시뮬레이션 상태 표시
        with st.status("단계별 규제 분석 진행 중", expanded=True) as status:
            st.write("쟁점 파악 및 대상 지역 식별 진행")
            time.sleep(0.5)
            st.write("상위 법령 및 지자체 조례 조문 대조")
            time.sleep(0.5)
            st.write("근거 조문 추출 및 답변 초안 구성")
            time.sleep(0.5)
            status.update(label="분석 완료", state="complete", expanded=False)

        # 분석 결과 출력 공간
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("건축 규제 검토 보고서")
        
        # 데이터베이스 우선 조회
        db_info = get_ordinance_data(user_query)
        
        if db_info:
            st.write("**1. 판단 결론**")
            st.info(db_info['conclusion'])
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**2. 적용 지역**")
                st.write(db_info['region'])
                st.write("**3. 핵심 근거 조문**")
                st.write(db_info['law'])
            with c2:
                st.write("**4. 해석 설명**")
                st.write(db_info['detail'])
                st.write("**6. 후속 절차**")
                st.write(db_info['next'])
            st.write("**5. 추가 확인 사항**")
            st.warning(db_info['check'])
        else:
            # 데이터베이스에 결과가 없을 경우 제미나이 실행
            with st.spinner("제미나이 엔진이 조례를 분석하고 있습니다"):
                try:
                    ai_answer = get_gemini_response(user_query)
                    st.write(ai_answer)
                except Exception as e:
                    st.error("AI 엔진 연결에 실패했습니다. API 키 설정을 확인해 주세요.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# 3. 건축 시뮬레이션 및 4. 민원 양식
with tabs[2]:
    st.header("건축선 및 일조권 시각화")
    st.write("준비 중인 기능입니다.")

with tabs[3]:
    st.header("행정 민원 지원")
    st.write("준비 중인 기능입니다.")

# 하단 면책 고지
st.divider()
st.caption("본 서비스는 행정기관의 최종 유권해석을 대체하지 않으며, 실제 인허가 신청 전 관할 행정청의 확인이 필요합니다.")
