# processor.py
import streamlit as st
from engine import get_semantic_keywords, get_gemini_response
from database import get_ordinance_data

def process_architectural_query(user_query):
    """
    UI로부터 쿼리를 받아 전체 분석 파이프라인을 실행합니다.
    1. 시맨틱 키워드 추출
    2. DB 탐색 (상태값 및 컨텍스트 확보)
    3. 최종 AI 보고서 생성
    """
    # [Step 1] 법률적 단서(시맨틱 키워드) 도출
    semantic_tags = get_semantic_keywords(user_query)
    
    # [Step 2] 데이터베이스 탐색 (밀도 점수 및 상태값 반환)
    db_status, db_context = get_ordinance_data(user_query, semantic_tags)
    
    # [Step 3] 최종 AI 응답 생성 (상태값에 따른 지능형 폴백 포함)
    response_text = get_gemini_response(
        user_query=user_query,
        db_status=db_status,
        db_context=db_context,
        semantic_tags=semantic_tags
    )
    
    return response_text
