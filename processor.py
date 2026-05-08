# processor.py
from datetime import datetime
import streamlit as st
from engine import get_semantic_keywords, get_gemini_response
from database import get_ordinance_data
from storage import save_history

def handle_ai_analysis(user_query):
    """
    [UI-백엔드 브릿지 함수]
    app.py에서 이 함수만 호출하면 분석, DB탐색, 결과 저장까지 한 번에 끝냅니다.
    """
    # 1. 시맨틱 키워드 도출 (중요: 여기서 태그를 뽑아야 DB가 제13조를 찾습니다)
    semantic_tags = get_semantic_keywords(user_query)
    
    # 2. DB 탐색 (status와 context 확보)
    db_status, db_context = get_ordinance_data(user_query, semantic_tags)
    
    # 3. AI 응답 생성
    response_text = get_gemini_response(
        user_query=user_query,
        db_status=db_status,
        db_context=db_context,
        semantic_tags=semantic_tags
    )
    
    # 4. 대화방 방식으로 저장
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # chat_history가 없으면 빈 리스트 생성
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # selected_index가 없으면 None으로 생성
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None
    
    # 새 대화가 필요한 경우
    if st.session_state.selected_index is None or len(st.session_state.chat_history) == 0:
        new_chat = {
            "title": user_query[:20] + ("..." if len(user_query) > 20 else ""),
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
    
        st.session_state.chat_history.append(new_chat)
        st.session_state.selected_index = len(st.session_state.chat_history) - 1
    
    # 현재 대화방 찾기
    current_chat = st.session_state.chat_history[st.session_state.selected_index]
    
    # 혹시 messages가 없으면 생성
    if "messages" not in current_chat:
        current_chat["messages"] = []
    
    # 현재 대화방 안에 질문/답변 추가
    current_chat["messages"].append({
        "query": user_query,
        "response": response_text,
        "time": now
    })
    
    current_chat["updated_at"] = now
    
    # 저장
    save_history(st.session_state.chat_history)
    
    return response_text

# processor.py 내의 기존 generate_civil_document 함수를 아래 코드로 교체하세요.

def generate_civil_document(civil_type, site_address, civil_content):
    """
    민원 양식 전용 생성 함수
    주의: 메인 챗봇 히스토리와 섞이지 않도록 대화 기록 저장(save_history) 로직을 절대 포함하지 않습니다.
    """
    
    # 1. LLM 초기화 (기존에 사용하시던 모델 객체 생성 방식 그대로 사용하시면 됩니다)
    # 예: llm = ChatOpenAI(model_name="gpt-4o", temperature=0.3) 
    
    # 2. 민원 양식 전용 프롬프트 (개선사항 1, 2, 3, 4 반영)
    system_prompt = f"""
    당신은 용인시청 건축부서에 제출할 민원서를 작성하는 전문 행정사입니다.
    사용자의 입력 정보를 바탕으로 '오직 민원서 양식'만 간소화하여 바로 출력하세요.

    [작성 원칙 - 매우 중요]
    1. 결론, 핵심근거, 세부 해석, 관련 건축법/조례, 예상 검토사항 등의 내용은 절대 작성하지 마세요.
    2. 인사말이나 부연 설명 없이, 오직 아래의 [민원서 템플릿]에 맞춘 결과물만 텍스트로 출력하세요.
    3. 어조는 절대 공격적이거나 감정적이지 않아야 합니다. '불법', '당장 조치해라' 등의 거친 표현 대신, '불편을 겪고 있으니 행정적 지도를 요청드립니다', '개선 방안을 검토해 주시길 바랍니다' 등 정중하고 객관적인 행정 용어로 순화하세요.
    4. 내용은 핵심만 전달되도록 최대한 간소화하여 3~4문장 내외로 작성하세요.

    [민원서 템플릿]
    ■ 민원 제목: (민원 내용을 요약하여 정중한 제목 작성)
    ■ 대상 주소: {site_address}
    ■ 민원 유형: {civil_type}
    
    ■ 민원 요지 및 요청사항:
    (이곳에 순화되고 간소화된 민원 내용 작성)
    """

    user_prompt = f"다음 내용을 바탕으로 민원서를 작성해 주세요: {civil_content}"

    # 3. LLM 호출 (메모리나 체인을 사용하지 않고 단발성으로 호출하여 히스토리 오염 방지)
    # 프레임워크(LangChain, LlamaIndex 등)에 맞춰 호출 코드를 조정하세요.
    # 예시 (LangChain의 경우):
    # messages = [
    #     SystemMessage(content=system_prompt),
    #     HumanMessage(content=user_prompt)
    # ]
    # response = llm.invoke(messages)
    # result_text = response.content
    
    # 이 부분은 현재 사용 중인 llm 호출 방식에 맞게 수정하세요.
    result_text = llm_invoke_function(system_prompt, user_prompt) # 임시 함수명
    
    # 4. 결과 반환 (DB나 History 저장 로직 제거)
    return result_text
