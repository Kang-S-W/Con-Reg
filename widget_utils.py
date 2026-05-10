import streamlit as st
import base64

def inject_floating_button():
    # 로고 이미지를 Base64로 변환 (이미지 파일이 프로젝트 폴더에 있다고 가정)
    # 이미지 파일명을 'yongin_logo.png'로 가정했습니다.
    try:
        with open("yongin_logo.png", "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
    except FileNotFoundError:
        encoded = "" # 파일이 없을 경우 대비

    # 용인시 브랜드 컬러 추출
    # 퍼플: #9d338c (대략적) / 그린: #00b09b (대략적)
    
    st.markdown(
        f"""
        <style>
        .floating-button {{
            position: fixed;
            right: 20px;
            bottom: 100px; /* 챗봇 창 등과 겹치지 않게 높이 조절 */
            width: 200px;
            height: auto;
            background-color: white;
            color: #333;
            border: 2px solid #9d338c;
            border-radius: 50px 10px 50px 50px;
            padding: 10px 15px;
            box-shadow: 2px 5px 15px rgba(0,0,0,0.2);
            z-index: 9999;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            text-decoration: none !important;
        }}
        .floating-button:hover {{
            transform: scale(1.05);
            background-color: #f8f0f8;
            box-shadow: 2px 8px 20px rgba(157, 51, 140, 0.3);
        }}
        .floating-button img {{
            width: 30px;
            margin-right: 10px;
        }}
        .floating-button span {{
            font-size: 14px;
            font-weight: bold;
            line-height: 1.2;
        }}
        </style>
        
        <a href="https://www.yongin.go.kr/user/web/yicvplReq/BD_selectYicvplReq.do" target="_blank" class="floating-button">
            <img src="data:image/png;base64,{encoded}" />
            <span>답변이 마음에<br>안 드십니까?</span>
        </a>
        """,
        unsafe_allow_html=True
    )
