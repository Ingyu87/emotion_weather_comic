import streamlit as st
import requests
import json
import re
from datetime import datetime
import time

# 시크릿 키 불러오기
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

# 페이지 설정
st.set_page_config(
    page_title="4컷 만화 스토리보드 생성기",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp, .stApp *, .stMarkdown, .stMarkdown * {
        color: #000000 !important;
    }
    
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea,
    .stTextInput input,
    .stTextArea textarea {
        color: #ffffff !important;
        background-color: #2c3e50 !important;
    }
    
    .stCode, .stCode *, code, pre {
        color: #ffffff !important;
        background: #2c3e50 !important;
    }
    
    /* 모든 버튼과 클릭 요소의 커서 문제 완전 해결 */
    .stButton > button, 
    .stButton > button *,
    .stButton button,
    button,
    [data-testid="stButton"] > button,
    [data-testid="stButton"] button,
    [data-testid="stButton"],
    .stButton,
    div[data-testid="stButton"],
    div[data-testid="stButton"] > button,
    .element-container button {
        color: white !important;
        background: #3498db !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        border: none !important;
    }
    
    .stButton > button:hover, 
    .stButton > button *:hover,
    .stButton button:hover,
    button:hover,
    [data-testid="stButton"] > button:hover,
    [data-testid="stButton"] button:hover,
    [data-testid="stButton"]:hover,
    .stButton:hover,
    div[data-testid="stButton"]:hover,
    div[data-testid="stButton"] > button:hover,
    .element-container button:hover {
        cursor: pointer !important;
        background: #2980b9 !important;
        pointer-events: auto !important;
    }
    
    .stButton > button:disabled, 
    .stButton > button:disabled *,
    .stButton button:disabled,
    button:disabled,
    [data-testid="stButton"] > button:disabled,
    [data-testid="stButton"] button:disabled,
    div[data-testid="stButton"] > button:disabled,
    .element-container button:disabled {
        cursor: not-allowed !important;
        background: #95a5a6 !important;
        opacity: 0.5 !important;
        color: #ffffff !important;
    }
    
    /* 라디오 버튼과 모든 클릭 가능한 요소들 */
    [role="button"],
    .stRadio > div,
    .stRadio label,
    .stRadio,
    input[type="radio"],
    .stSelectbox,
    .stTextInput,
    .stTextArea {
        cursor: pointer !important;
    }
    
    /* 전체 앱에서 커서 문제 해결 */
    * {
        cursor: default;
    }
    
    button, input, select, textarea, [role="button"], .stButton, [data-testid="stButton"] {
        cursor: pointer !important;
    }
    
    /* 워터마크 예쁘게 꾸미기 - 왼쪽 하단 */
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 12px;
        color: #ffffff;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 8px 16px;
        border-radius: 20px;
        z-index: 99999;
        pointer-events: none;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: watermarkFloat 3s ease-in-out infinite;
    }
    
    @keyframes watermarkFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    /* 코드 블록 복사 버튼 스타일링 */
    .stCode {
        position: relative;
    }
    
    .stCode:hover::after {
        content: "📋";
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(52, 152, 219, 0.9);
        color: white;
        padding: 5px 8px;
        border-radius: 8px;
        font-size: 12px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Noto Sans KR', sans-serif;
    }
    .main-container {
        background: rgba(255, 255, 255, 0.98);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 1rem auto;
        max-width: 1200px;
    }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .step-indicator {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .step {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 1rem;
        font-weight: bold;
    }
    .step.active {
        background: #3498db;
        color: white;
    }
    .step.completed {
        background: #27ae60;
        color: white;
    }
    .step.inactive {
        background: #ecf0f1;
        color: #000000;
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        border-radius: 10px;
        border: none;
        background: #3498db;
        color: white;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .safety-guide {
        display: flex;
        gap: 2rem;
        align-items: flex-start;
        margin-bottom: 2rem;
    }
    
    .safety-guide-left {
        flex: 1;
        background: #fff8e1;
        border: 2px solid #ffc107;
        border-radius: 15px;
        padding: 1.5rem;
    }
    
    .safety-guide-right {
        flex: 1;
        background: #e8f5e8;
        border: 2px solid #28a745;
        border-radius: 15px;
        padding: 1.5rem;
    }
    
    .safety-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .safety-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .safety-list li {
        margin-bottom: 0.8rem;
        padding-left: 1.5rem;
        position: relative;
        line-height: 1.4;
    }
    
    .safety-list li:before {
        content: "•";
        position: absolute;
        left: 0;
        color: #666;
        font-weight: bold;
    }
    
    .prohibited-list li:before {
        content: "⚠️";
        font-size: 1rem;
    }
    
    .recommended-list li:before {
        content: "✅";
        font-size: 1rem;
    }
    
    .next-step-container {
        text-align: center;
        padding: 2rem;
        margin-top: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        position: relative;
        overflow: hidden;
    }
    
    .next-step-text {
        color: white;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .next-step-emoji {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    
    @media (max-width: 768px) {
        .safety-guide {
            flex-direction: column;
            gap: 1rem;
        }
        
        .main-container {
            max-width: 95%;
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    today = datetime.now().strftime("%Y-%m-%d")
    
    if "last_date" not in st.session_state or st.session_state.last_date != today:
        st.session_state.call_count = 0
        st.session_state.last_date = today
    
    defaults = {
        "call_count": 0,
        "current_step": 1,
        "age_group": None,
        "gender": None,
        "art_style": None,
        "situation": None,
        "emotion": None,
        "reason": None,
        "emotion_options": ([], []),
        "scenes": [],
        "scene_prompts": [],
        "last_date": today
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_text_input(text, min_length=5, max_length=200, field_name="입력"):
    if not text or not text.strip():
        return False, f"{field_name}을 입력해주세요."
    
    text = text.strip()
    if len(text) < min_length:
        return False, f"{field_name}은 최소 {min_length}자 이상 입력해주세요."
    
    if len(text) > max_length:
        return False, f"{field_name}은 최대 {max_length}자까지 입력 가능합니다."
    
    return True, ""

def validate_age_group(age_group):
    valid_ages = ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"]
    return age_group in valid_ages

def get_emotion_traffic_light(emotion):
    positive_emotions = ["기쁨", "행복", "감사", "뿌듯함", "만족", "희망", "신남", "설렘", "평온", "자신감"]
    negative_emotions = ["슬픔", "화남", "답답함", "걱정", "두려움", "실망", "부끄러움", "외로움", "스트레스", "짜증"]
    
    if emotion in positive_emotions:
        return {
            "color": "🟢",
            "status": "초록불",
            "message": "건강하고 긍정적인 감정이에요! 이런 감정을 잘 표현하고 나누어보세요.",
            "css_color": "#28a745"
        }
    elif emotion in negative_emotions:
        return {
            "color": "🔴", 
            "status": "빨간불",
            "message": "힘들고 어려운 감정이네요. 이런 감정은 혼자 담아두지 말고 선생님이나 부모님께 도움을 요청하는 것이 좋아요.",
            "css_color": "#dc3545"
        }
    else:
        return {
            "color": "🟡",
            "status": "노란불", 
            "message": "복잡한 감정이에요. 천천히 생각해보고 감정을 정리해보세요.",
            "css_color": "#ffc107"
        }

def ask_gemini(prompt, model="models/gemini-1.5-pro-latest"):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        
        result = response.json()
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        inappropriate_words = [
            "바보", "멍청", "죽어", "꺼져", "시발", "개새", "병신", "미친",
            "혐오", "차별", "따돌림", "왕따", "괴롭히", "폭력", "때리", "싸우",
            "비키니", "키스", "연애", "사랑", "섹시", "예쁘", "잘생", "몸매",
            "담배", "술", "마약", "도박", "자해", "칼", "위험한",
            "트럼프", "김정은", "윤석열", "문재인", "박근혜", "이재명", 
            "바이든", "푸틴", "시진핑", "정치인", "대통령", "국회의원"
        ]
        
        for word in inappropriate_words:
            if word in generated_text:
                return f"[안전 필터] 부적절한 내용이 생성되어 다시 생성합니다. 안전한 내용으로 대체됩니다."
        
        return generated_text
        
    except requests.exceptions.Timeout:
        return "[오류] 요청 시간이 초과되었습니다."
    except requests.exceptions.RequestException as e:
        return f"[오류] 네트워크 오류: {str(e)}"
    except KeyError:
        return "[오류] API 응답 형식이 올바르지 않습니다."
    except Exception as e:
        return f"[오류] 예상치 못한 오류: {str(e)}"

def fetch_emotions(situation):
    positive_emotions = ["기쁨", "행복", "감사", "뿌듯함", "만족", "희망", "신남", "설렘", "평온", "자신감"]
    negative_emotions = ["슬픔", "화남", "답답함", "걱정", "두려움", "실망", "부끄러움", "외로움", "스트레스", "짜증"]
    return positive_emotions, negative_emotions

def render_step_indicator(current_step):
    steps = ["👤", "📝", "😊", "💭", "🎨"]
    
    html = '<div class="step-indicator">'
    for i, icon in enumerate(steps, 1):
        if i < current_step:
            css_class = "step completed"
        elif i == current_step:
            css_class = "step active"
        else:
            css_class = "step inactive"
        
        html += f'<div class="{css_class}">{icon}</div>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

def render_progress_bar(progress):
    html = f'''
    <div style="width: 100%; height: 6px; background: #ecf0f1; border-radius: 3px; margin: 1rem 0;">
        <div style="width: {progress}%; height: 100%; background: #3498db; border-radius: 3px; transition: width 0.3s ease;"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# 메인 실행
init_session_state()

if st.session_state.call_count >= 100:
    st.error("🚫 오늘은 100회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
    st.stop()

st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📋 4컷 만화 스토리보드 생성기</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">감정과 상황을 바탕으로 4컷 만화 스토리보드와 최적화된 이미지 프롬프트를 만들어보세요!</p>', unsafe_allow_html=True)

render_step_indicator(st.session_state.current_step)

progress = (st.session_state.current_step - 1) * 25
render_progress_bar(progress)

if st.session_state.current_step == 1:
    # 안전 사용 안내 (HTML 렌더링이 아닌 Streamlit 네이티브 컴포넌트 사용)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🚫 이런 내용은 차단돼요")
        st.markdown("""
        - ⚠️ 욕설, 폭언, 혐오 표현
        - ⚠️ 폭력적이거나 위험한 내용  
        - ⚠️ 부적절한 성적 표현
        - ⚠️ 정치적 인물이나 논란적 내용
        - ⚠️ 의미 없는 글자 나열
        """)
    
    with col2:
        st.markdown("#### ✅ 이런 건전한 내용을 사용해주세요")
        st.markdown("""
        - ✅ 친구와의 우정 이야기
        - ✅ 학교에서의 즐거운 경험
        - ✅ 가족과의 따뜻한 시간
        - ✅ 새로운 것을 배우는 기쁨
        - ✅ 도움을 주고받는 경험
        """)
    
    st.info("""
    🎨 **감정 표현 4컷 만화 만들기**
    
    📚 교육 목표: 자신의 감정을 인식하고 표현하는 능력 향상  
    🎯 결과물: 4컷 만화 스토리보드 + AI 이미지 생성용 프롬프트
    """)
    
    st.subheader("👤 사용자 나이대를 선택하세요")
    st.markdown("만화 스타일과 내용을 맞춤화하기 위해 나이대를 선택해주세요.")
    
    age_options = ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"]
    selected_age = st.radio("나이대 선택", age_options, horizontal=True)
    
    age_descriptions = {
        "초등학교 1~2학년": "🌟 간단하고 귀여운 스타일의 만화를 만들어요!",
        "초등학교 3~4학년": "🎨 조금 더 자세하고 재미있는 스토리를 만들어요!",
        "초등학교 5~6학년": "📖 감정 표현이 풍부하고 깊이 있는 만화를 만들어요!",
        "교사": "🎓 교육용으로 활용할 수 있는 전문적인 스토리보드를 만들어요!"
    }
    
    if selected_age:
        st.info(f"✨ {age_descriptions[selected_age]}")
    
    st.markdown("### 👦👧 주인공 성별을 선택하세요")
    gender = st.radio("성별 선택", ["남자", "여자"], horizontal=True)
    
    if gender:
        gender_emoji = "👦" if gender == "남자" else "👧"
        st.info(f"{gender_emoji} {gender} 주인공으로 만화를 만들어요!")
    
    st.markdown("### 🎨 만화/사진 스타일을 선택하세요")
    st.markdown("원하는 스타일을 클릭해보세요! 각각 다른 느낌의 만화가 만들어져요.")
    
    art_styles = {
        "귀여운 애니메이션": {"emoji": "🌟", "desc": "지브리, 디즈니 같은 부드럽고 따뜻한 스타일"},
        "한국 웹툰": {"emoji": "📱", "desc": "네이버 웹툰 같은 깔끔하고 현대적인 스타일"}, 
        "3D 캐릭터": {"emoji": "🎭", "desc": "픽사, 토이스토리 같은 입체적이고 생동감 있는 스타일"},
        "피규어 형태": {"emoji": "🧸", "desc": "레고, 플레이모빌 같은 귀여운 장난감 스타일"},
        "낙서 형태": {"emoji": "✏️", "desc": "공책에 그린 듯한 자유롭고 친근한 손그림 스타일"},
        "수채화": {"emoji": "🖼️", "desc": "부드럽고 몽환적인 수채화 일러스트 스타일"},
        "동화책": {"emoji": "📚", "desc": "따뜻하고 상상력 가득한 동화책 삽화 스타일"},
        "실제 사진": {"emoji": "📸", "desc": "실제 아이들이 연기하는 사진 스타일"},
        "인형극": {"emoji": "🎪", "desc": "인형이나 마네킹을 이용한 인형극 사진 스타일"},
        "클레이 모델": {"emoji": "🏺", "desc": "찰흙이나 클레이로 만든 캐릭터 사진 스타일"}
    }
    
    col1, col2, col3 = st.columns(3)
    
    style_names = list(art_styles.keys())
    selected_style = st.session_state.get('art_style', None)
    
    for i, style_name in enumerate(style_names):
        col_idx = i % 3
        if col_idx == 0:
            current_col = col1
        elif col_idx == 1:
            current_col = col2
        else:
            current_col = col3
            
        with current_col:
            style_info = art_styles[style_name]
            
            if st.button(f"{style_info['emoji']} {style_name}", key=f"style_{style_name}", use_container_width=True):
                st.session_state.art_style = style_name
                st.success(f"✨ {style_name} 스타일을 선택했어요!")
                st.rerun()
    
    if selected_style:
        st.markdown("---")
        style_info = art_styles[selected_style]
        st.markdown(f"""
        <div class="success-animation" style="background: #e8f5e8; border: 2px solid #27ae60; padding: 1rem; border-radius: 15px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{style_info['emoji']}</div>
            <div style="font-size: 1.2rem; font-weight: bold; color: #27ae60; margin-bottom: 0.5rem;">선택한 스타일: {selected_style}</div>
            <div style="color: #2d5016;">{style_info['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div class="next-step-container">
        <div class="next-step-emoji">🚀</div>
        <div class="next-step-text">모든 정보가 준비되었어요! 다음 단계로 넘어가 볼까요?</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        if st.button("✨ 다음 단계로 GO! ✨", key="step1_next", use_container_width=True):
            if validate_age_group(selected_age) and gender and st.session_state.get('art_style'):
                st.session_state.age_group = selected_age
                st.session_state.gender = gender
                st.session_state.current_step = 2
                st.balloons()
                st.rerun()
            else:
                missing = []
                if not gender:
                    missing.append("성별")
                if not st.session_state.get('art_style'):
                    missing.append("화풍")
                st.error(f"{'과 '.join(missing)}을 선택해주세요!")

elif st.session_state.current_step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 어떤 상황인가요?")
    
    age_situations = {
        "초등학교 1~2학년": [
            "급식시간에 좋아하는 반찬이 나왔을 때",
            "친구와 놀이터에서 함께 놀았을 때", 
            "선생님께 칭찬을 받았을 때",
            "새로운 친구와 인사를 나눴을 때",
            "미술 시간에 그림을 그렸을 때"
        ],
        "초등학교 3~4학년": [
            "체육시간에 피구를 하다가 공에 맞았을 때",
            "숙제를 깜빡하고 학교에 왔을 때",
            "시험에서 예상보다 좋은 점수를 받았을 때",
            "친구와 다툰 후 화해했을 때",
            "발표를 하는데 긴장되었을 때"
        ],
        "초등학교 5~6학년": [
            "학급 임원 선거에서 떨어졌을 때",
            "친한 친구가 다른 학교로 전학갔을 때",
            "어려운 수학 문제를 혼자 풀었을 때",
            "단체 활동에서 의견이 안 맞았을 때",
            "졸업식을 앞두고 친구들과 시간을 보낼 때"
        ],
        "교사": [
            "학생이 처음으로 어려운 개념을 이해했을 때",
            "학급에서 갈등이 일어나 중재해야 할 때", 
            "공개수업을 앞두고 준비하는 상황",
            "학부모와 상담하는 시간",
            "동료 교사와 협업하여 프로젝트를 진행할 때"
        ]
    }
    
    current_age = st.session_state.age_group or "초등학교 1~2학년"
    situations = age_situations.get(current_age, age_situations["초등학교 1~2학년"])
    
    st.markdown(f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
        <strong>💡 {current_age} 학교생활 상황 예시:</strong><br>
        {'<br>'.join([f'• {situation}' for situation in situations])}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("위 예시를 참고하거나, 직접 경험한 학교생활 상황을 자세히 적어주세요.")
    
    situation = st.text_area(
        "상황 설명",
        placeholder=f"예: {situations[0]}",
        height=100,
        key="situation_input"
    )
    
    char_count = len(situation) if situation else 0
    st.caption(f"글자 수: {char_count}/200")
    
    situation_valid = len(situation.strip()) >= 10 if situation else False
    
    if situation and len(situation.strip()) >= 5:
        # AI 기반 실시간 문맥 검증 (키워드 체크 먼저 하지 않고 문맥으로 판단)
        try:
            context_check_prompt = f"""
다음 텍스트가 초등학생에게 적합한지 문맥을 고려하여 판단해주세요:

텍스트: "{situation}"

판단 기준:
- 문맥상 폭력적이거나 위험한 의도가 있는가?
- 문맥상 욕설이나 혐오 표현의 의도가 있는가?
- 문맥상 성적이거나 부적절한 내용인가?
- 정치적 인물이나 논란적 내용인가?
- 의미있는 교육적 상황인가?
- 초등학생 교육환경에 적합한가?

문맥 예시:
- "친구와 죽 먹기" → 적합 (음식을 먹는 이야기)
- "괴물을 죽이기" → 부적절 (폭력적 내용)
- "김정은 만나기" → 부적절 (정치적 인물)
- "시험을 망쳤어" → 적합 (학교 상황 표현)
- "선생님이 미쳤다고 했어" → 부적절 (부적절한 표현)

문맥상 의미를 종합적으로 고려하여 "적합" 또는 "부적절" 중 하나로만 답변하세요.
특히 욕설의 변형이나 은어, 부적절한 표현이 숨어있는지 주의깊게 살펴보세요:
"""
            
            ai_response = ask_gemini(context_check_prompt)
            
            if ai_response and "부적절" in ai_response:
                if has_inappropriate:
                    st.error("🚨 부적절한 내용이 감지되었습니다!")
                    st.warning("""
                    **디지털 시민 교육**: 학교에서는 모든 친구들이 안전하고 편안하게 느낄 수 있는 내용만 사용해야 해요.
                    
                    **건전한 내용으로 바꿔주세요**:
                    - 친구와 사이좋게 놀이터에서 놀았을 때
                    - 선생님께 칭찬을 받아서 기뻤을 때  
                    - 새로운 것을 배워서 뿌듯했을 때
                    - 친구에게 도움을 주거나 받았을 때
                    - 가족과 함께 즐거운 시간을 보냈을 때
                    """)
                    situation_valid = False
            elif ai_response and "적합" in ai_response:
                if len(situation.strip()) >= 10:
                    st.success("✅ 훌륭한 상황 설명이에요! 건전하고 교육적인 내용으로 멋진 만화를 만들 수 있을 거예요! 👍")
                    situation_valid = True
                else:
                    situation_valid = False
            else:
                # AI 응답이 애매하면 기본 키워드로 한번 더 체크 (더 강화된 키워드 리스트)
                inappropriate_words = [
                    "시발", "병신", "김정은", "트럼프", "윤석열", "죽어", "꺼져", "좆", "씨발", "개새끼",
                    "바보", "멍청", "미친", "년", "새끼", "개새", "처먹", "좋이나", "쳐먹", "개소리",
                    "좋아", "좋이", "처", "먹", "쳐", "개", "병", "신", "미", "친"
                ]
                has_inappropriate = any(word in situation.lower().replace(" ", "") for word in inappropriate_words)
                
                if has_inappropriate:
                    st.error("🚨 부적절한 표현이 포함되어 있어요!")
                    situation_valid = False
                else:
                    situation_valid = len(situation.strip()) >= 10
        except:
            # AI 검증 실패 시 기본 키워드 체크 (더 강화된 키워드 리스트)
            inappropriate_words = [
                "시발", "병신", "김정은", "트럼프", "윤석열", "죽어", "꺼져", "좆", "씨발", "개새끼",
                "바보", "멍청", "미친", "년", "새끼", "개새", "처먹", "좋이나", "쳐먹", "개소리",
                "좋아", "좋이", "처", "먹", "쳐", "개", "병", "신", "미", "친"
            ]
            has_inappropriate = any(word in situation.lower().replace(" ", "") for word in inappropriate_words)
            
            if has_inappropriate:
                st.error("🚨 부적절한 표현이 포함되어 있어요!")
                situation_valid = False
            else:
                situation_valid = len(situation.strip()) >= 10
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        if st.button("🎭 감정 선택하러 가기! 🎭", disabled=not situation_valid, key="step2_next", use_container_width=True):
            if situation_valid:
                is_valid, message = validate_text_input(situation, min_length=10, max_length=200, field_name="상황 설명")
                if is_valid:
                    st.session_state.situation = situation.strip()
                    st.session_state.emotion_options = fetch_emotions(st.session_state.situation)
                    st.session_state.current_step = 3
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("적절한 상황을 입력해주세요!")
    
    st.markdown("---")
    
    # 다음 단계 안내를 Streamlit 네이티브로 변경
    st.info("📝 좋은 상황 설명이에요! 이제 감정을 선택해볼까요?")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("😊 이 상황에서 느낀 감정을 선택하세요")
    st.markdown("가장 강하게 느꼈던 감정 하나를 골라주세요.")
    
    st.markdown("### 🌟 긍정적인 감정")
    pos_cols = st.columns(5)
    for i, emotion in enumerate(st.session_state.emotion_options[0]):
        with pos_cols[i % 5]:
            if st.button(f"😊 {emotion}", key=f"pos_{emotion}", use_container_width=True):
                st.session_state.emotion = emotion
                st.session_state.current_step = 4
                st.success(f"✨ '{emotion}' 감정을 선택했어요!")
                time.sleep(0.5)
                st.rerun()
    
    st.markdown("### 😔 부정적인 감정")
    neg_cols = st.columns(5)
    for i, emotion in enumerate(st.session_state.emotion_options[1]):
        with neg_cols[i % 5]:
            if st.button(f"😔 {emotion}", key=f"neg_{emotion}", use_container_width=True):
                st.session_state.emotion = emotion
                st.session_state.current_step = 4
                st.success(f"✨ '{emotion}' 감정을 선택했어요!")
                time.sleep(0.5)
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🚥 감정 신호등이란?")
    st.markdown("""
    **🟢 초록불 감정**: 건강하고 긍정적인 감정들 - 잘 표현하고 나누어보세요!
    
    **🟡 노란불 감정**: 주의가 필요한 복잡한 감정들 - 천천히 생각해보세요
    
    **🔴 빨간불 감정**: 힘들고 어려운 감정들 - 도움을 요청하는 것이 좋아요
    """)
    
    if st.button("⬅️ 이전"):
        st.session_state.current_step = 2
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"💭 '{st.session_state.emotion}' 감정을 느낀 이유는 무엇인가요?")
    st.markdown("그 감정을 느끼게 된 구체적인 이유나 생각을 적어주세요.")
    
    reason = st.text_area(
        "감정의 이유",
        placeholder=f"예: {st.session_state.emotion}을 느낀 이유는...",
        height=100,
        key="reason_input"
    )
    
    char_count = len(reason) if reason else 0
    st.caption(f"글자 수: {char_count}/150")
    
    reason_valid = len(reason.strip()) >= 5 if reason else False
    
    if reason and len(reason.strip()) >= 3:
        # AI 기반 실시간 문맥 검증 (감정 이유도 문맥으로 판단)
        try:
            reason_check_prompt = f"""
다음 감정의 이유가 초등학생에게 적합한지 문맥을 고려하여 판단해주세요:

텍스트: "{reason}"

판단 기준:
- 문맥상 폭력적이거나 위험한 의도가 있는가?
- 문맥상 욕설이나 혐오 표현의 의도가 있는가?
- 문맥상 성적이거나 부적절한 내용인가?
- 정치적 인물이나 논란적 내용인가?
- 의미있는 감정 표현인가?
- 초등학생 교육환경에 적합한가?

문맥 예시:
- "죽도록 열심히 했는데" → 적합 (열심히 노력했다는 의미)
- "친구를 죽이고 싶었어" → 부적절 (폭력적 표현)
- "미친듯이 기뻤어" → 적합 (매우 기뻤다는 의미)
- "선생님이 미쳤다고 생각해" → 부적절 (비하 표현)

문맥상 의미를 종합적으로 고려하여 "적합" 또는 "부적절" 중 하나로만 답변하세요:
"""
            
            ai_response = ask_gemini(reason_check_prompt)
            
            if ai_response and "부적절" in ai_response:
                st.error("🚨 부적절한 감정 표현이 감지되었습니다!")
                st.warning("""
                **감정 교육**: 감정의 이유를 표현할 때도 건전하고 교육적인 언어를 사용해야 해요.
                
                **건전한 표현으로 바꿔주세요**:
                - "친구가 나를 이해해주지 않아서 속상했어요"
                - "기대했던 것과 달라서 실망스러웠어요"  
                - "새로운 도전이라 긴장되고 두려웠어요"
                - "노력한 만큼 결과가 나와서 뿌듯했어요"
                - "친구들과 함께 해서 더욱 즐거웠어요"
                """)
                reason_valid = False
            elif ai_response and "적합" in ai_response:
                if len(reason.strip()) >= 5:
                    st.success("✅ 감정을 훌륭하게 표현해주셨어요! 이런 솔직하고 건전한 감정 표현이 좋은 교육 자료가 됩니다! 👏")
                    reason_valid = True
                else:
                    reason_valid = False
            else:
                # AI 응답이 애매하면 기본 키워드로 한번 더 체크
                inappropriate_words = ["시발", "병신", "김정은", "트럼프", "앙착의와잡괴", "좆", "씨발", "개새끼"]
                has_inappropriate = any(word in reason.lower() for word in inappropriate_words)
                
                if has_inappropriate:
                    st.error("🚨 부적절한 표현이 포함되어 있어요!")
                    reason_valid = False
                else:
                    reason_valid = len(reason.strip()) >= 5
        except:
            # AI 검증 실패 시 기본 키워드 체크
            inappropriate_words = ["시발", "병신", "김정은", "트럼프", "앙착의와잡괴", "좆", "씨발", "개새끼"]
            has_inappropriate = any(word in reason.lower() for word in inappropriate_words)
            
            if has_inappropriate:
                st.error("🚨 부적절한 표현이 포함되어 있어요!")
                reason_valid = False
            else:
                reason_valid = len(reason.strip()) >= 5
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 3
            st.rerun()
    
    with col3:
        if st.button("🎬 스토리보드 만들기! 🎬", disabled=not reason_valid, key="step4_final", use_container_width=True):
            if reason_valid:
                is_valid, message = validate_text_input(reason, min_length=5, max_length=150, field_name="감정의 이유")
                if is_valid:
                    st.session_state.reason = reason.strip()
                    st.session_state.current_step = 5
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("적절한 이유를 입력해주세요!")
    
    st.markdown("---")
    
    # 다음 단계 안내를 Streamlit 네이티브로 변경
    st.info("🎨 감정의 이유까지 완성! 이제 멋진 스토리보드를 만들어볼까요?")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 당신만의 4컷 만화 스토리보드가 완성되었어요!")
    
    with st.expander("📋 입력 정보 확인", expanded=False):
        st.write(f"**👤 나이대:** {st.session_state.age_group}")
        st.write(f"**👦👧 성별:** {st.session_state.gender}")
        st.write(f"**🎨 화풍:** {st.session_state.art_style}")
        st.write(f"**📝 상황:** {st.session_state.situation}")
        st.write(f"**😊 감정:** {st.session_state.emotion}")
        st.write(f"**💭 이유:** {st.session_state.reason}")
        
        if st.session_state.emotion:
            traffic_light = get_emotion_traffic_light(st.session_state.emotion)
            st.write(f"**🚥 감정 신호등:** {traffic_light['color']} {traffic_light['status']}")
    
    traffic_light = get_emotion_traffic_light(st.session_state.emotion)
    st.markdown(f"""
    <div style="background: {traffic_light['css_color']}15; border: 2px solid {traffic_light['css_color']}; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
        <h4 style="color: {traffic_light['css_color']}; margin-bottom: 0.5rem;">🚥 감정 신호등 결과: {traffic_light['color']} {traffic_light['status']}</h4>
        <p style="color: {traffic_light['css_color']}; margin-bottom: 0; font-weight: 500;">{traffic_light['message']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.scenes:
        with st.spinner("📋 AI가 당신의 이야기를 4컷 만화 스토리보드로 만들고 있어요..."):
            summary_prompt = f"""
나이대: {st.session_state.age_group}
상황: {st.session_state.situation}
감정: {st.session_state.emotion}
이유: {st.session_state.reason}

위 정보를 바탕으로 4컷 만화의 각 장면을 간단명료하게 설명해주세요.
각 장면은 한 문장으로, 번호와 함께 작성해주세요.

다음 형식으로 작성해주세요:
1. [첫 번째 장면 설명]
2. [두 번째 장면 설명]
3. [세 번째 장면 설명]
4. [네 번째 장면 설명]
"""
            
            result = ask_gemini(summary_prompt)
            
            if result and "[오류]" not in result:
                scenes = []
                lines = result.strip().split("\n")
                
                for line in lines:
                    line = line.strip()
                    if re.match(r'^\d+\.', line):
                        scene_text = re.sub(r'^\d+\.\s*', '', line).strip()
                        if scene_text:
                            scenes.append(scene_text)
                
                if len(scenes) < 4:
                    default_scenes = [
                        f"{st.session_state.age_group} 학생이 {st.session_state.situation}를 경험합니다",
                        f"상황이 진행되면서 {st.session_state.emotion} 감정이 생겨납니다",
                        f"{st.session_state.reason} 때문에 감정이 더욱 강해집니다",
                        f"상황이 마무리되며 감정을 정리합니다"
                    ]
                    scenes = default_scenes
                
                st.session_state.scenes = scenes[:4]
            else:
                st.session_state.scenes = [
                    f"{st.session_state.age_group} 학생이 상황을 경험합니다",
                    f"상황에서 {st.session_state.emotion} 감정을 느낍니다",
                    f"{st.session_state.reason} 때문입니다",
                    f"감정을 정리하고 마무리합니다"
                ]
    
    if st.session_state.scenes:
        st.success(f"✅ {len(st.session_state.scenes)}개의 장면이 생성되었습니다!")
        
        if not st.session_state.scene_prompts:
            with st.spinner("🎨 각 장면별 최적화된 이미지 프롬프트를 생성하고 있어요..."):
                character_desc = f"{'Korean elementary school boy' if st.session_state.gender == '남자' else 'Korean elementary school girl'}"
                age_desc = st.session_state.age_group
                
                for i, scene in enumerate(st.session_state.scenes):
                    prompt_generation_request = f"""
다음 정보로 K-6 학생용 안전한 단일 장면 이미지 생성용 영어 프롬프트를 만들어주세요:

캐릭터 정보:
- 나이대: {st.session_state.age_group}
- 성별: {st.session_state.gender}
- 상황: {st.session_state.situation}
- 감정: {st.session_state.emotion}
- 이 장면: {scene}

안전 요구사항 (반드시 준수):
1. K-6 학생에게 적합한 건전한 내용만
2. 폭력, 성적 내용, 위험한 행동 절대 금지
3. 교육적이고 긍정적인 내용
4. 학교 환경에 적합한 상황

기술 요구사항:
1. 단일 장면만 묘사 (4컷 중 {i+1}번째 컷)
2. 동일한 캐릭터가 4개 프롬프트 모두에 등장
3. 일관된 화풍 유지 (cute anime/manga style)
4. 영어로 작성
5. 한국 초등학생 캐릭터

안전하고 교육적인 프롬프트만 간결하게 출력해주세요:
"""
                    
                    ai_prompt = ask_gemini(prompt_generation_request)
                    if ai_prompt and "[오류]" not in ai_prompt:
                        clean_prompt = ai_prompt.strip()
                        if ":" in clean_prompt:
                            clean_prompt = clean_prompt.split(":")[-1].strip()
                        
                        safe_prompt = f"Safe for children, educational content. Cute anime/manga style illustration of a {character_desc} ({age_desc}) showing {st.session_state.emotion} emotion. {clean_prompt}. Wholesome, school-appropriate, consistent character design, colorful, child-friendly art style."
                        st.session_state.scene_prompts.append(clean_prompt)
                    else:
                        default_prompt = f"Safe for children, educational content. Cute anime/manga style illustration of a {character_desc} ({age_desc}) showing {st.session_state.emotion} emotion in this scene: {scene}. Wholesome, school-appropriate, consistent character design, colorful, child-friendly art style."
                        st.session_state.scene_prompts.append(default_prompt)
        
        for i, scene in enumerate(st.session_state.scenes):
            st.markdown(f"### 🎬 컷 {i+1}")
            st.write(f"**장면 설명:** {scene}")
            
            if len(st.session_state.scene_prompts) > i:
                st.markdown("**🤖 이 컷의 개별 프롬프트:**")
                st.code(st.session_state.scene_prompts[i], language="text")
            
            st.divider()
    else:
        st.error("❌ 장면 생성에 실패했습니다. '다시 만들기' 버튼을 눌러 다시 시도해주세요.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 다시 만들기"):
            keys_to_reset = ["age_group", "gender", "art_style", "situation", "emotion", "reason", "scenes", "scene_prompts", "emotion_options", "counted"]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.current_step = 1
            st.rerun()
    
    with col2:
        if st.button("📝 수정하기"):
            st.session_state.current_step = 4
            st.rerun()
    
    with col3:
        if st.button("📤 공유하기"):
            st.balloons()
            st.success("🎉 멋진 4컷 만화 스토리보드가 완성되었어요! 프롬프트를 복사해서 AI 이미지 생성 사이트에서 만들어보세요!")
    
    if st.session_state.scenes and not hasattr(st.session_state, 'counted'):
        st.session_state.call_count += 1
        st.session_state.counted = True
        
    if st.session_state.scenes and st.session_state.scene_prompts:
        st.markdown("---")
        st.markdown("### 🎬 4컷 만화 생성 프롬프트")
        
        character_desc = f"{'Korean elementary school boy' if st.session_state.gender == '남자' else 'Korean elementary school girl'}"
        
        style_prompts = {
            "귀여운 애니메이션": "Studio Ghibli style, Disney animation style, soft colors, magical atmosphere",
            "한국 웹툰": "Korean webtoon style, clean lines, vibrant colors, modern digital art",
            "3D 캐릭터": "Pixar 3D animation style, volumetric lighting, detailed textures, playful 3D characters",
            "피규어 형태": "LEGO minifigure style, Playmobil toy style, cute figurine aesthetic", 
            "낙서 형태": "Hand-drawn doodle style, sketch-like, casual drawing, notebook doodle aesthetic",
            "수채화": "Watercolor illustration, soft brushstrokes, gentle colors, dreamy atmosphere",
            "동화책": "Children's book illustration, storybook art style, warm and cozy",
            "실제 사진": "Real photography, candid photo of children, natural lighting, documentary style",
            "인형극": "Puppet show photography, marionette style, theatrical lighting, stage setting",
            "클레이 모델": "Clay animation style, stop-motion photography, plasticine characters"
        }
        
        art_style_prompt = style_prompts.get(st.session_state.art_style, "cute anime/manga style")
        
        four_panel_prompt = f"""Create a 4-panel comic strip (네컷 만화) with consistent character design throughout all panels:

Character: {character_desc} ({st.session_state.age_group})
Art Style: {art_style_prompt}
Story theme: {st.session_state.situation}
Main emotion: {st.session_state.emotion}
Reason for emotion: {st.session_state.reason}

Panel 1: {st.session_state.scenes[0] if len(st.session_state.scenes) > 0 else ""}
Panel 2: {st.session_state.scenes[1] if len(st.session_state.scenes) > 1 else ""}
Panel 3: {st.session_state.scenes[2] if len(st.session_state.scenes) > 2 else ""}
Panel 4: {st.session_state.scenes[3] if len(st.session_state.scenes) > 3 else ""}

Safety requirements: Safe for children, educational content, wholesome, school-appropriate, consistent character design across all panels, colorful, child-friendly."""
        
        st.markdown("**🎨 아래 프롬프트를 복사해서 AI 이미지 생성 사이트에 붙여넣으세요:**")
        
        # 복사 기능이 있는 텍스트 영역
        st.code(four_panel_prompt, language="text")
        
        # 복사 버튼 추가
        if st.button("📋 프롬프트 복사하기", key="copy_prompt"):
            st.success("✅ 프롬프트가 복사되었습니다! AI 이미지 생성 사이트에 붙여넣어 주세요!")
        
        # JavaScript로 실제 복사 기능 구현
        st.markdown(f"""
        <script>
        function copyToClipboard() {{
            navigator.clipboard.writeText(`{four_panel_prompt.replace('`', '\\`')}`);
        }}
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🌐 추천 이미지 생성 사이트")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎨 DALL-E 3**
            - [ChatGPT Plus](https://chat.openai.com)
            - [Bing Image Creator](https://www.bing.com/images/create)
            """)
        
        with col2:
            st.markdown("""
            **🎭 미드저니**
            - [Midjourney](https://www.midjourney.com)
            - 디스코드에서 사용
            """)
        
        with col3:
            st.markdown("""
            **🚀 기타 무료 사이트**
            - [Leonardo AI](https://leonardo.ai)
            - [PlaygroundAI](https://playgroundai.com)
            - [Ideogram](https://ideogram.ai)
            """)
        
        st.info("💡 **사용법**: 위 프롬프트를 복사해서 원하는 AI 이미지 생성 사이트에 붙여넣으면 4컷 만화가 한번에 생성됩니다!")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 워터마크와 푸터도 Streamlit 네이티브로 변경
# 예쁜 워터마크 추가
st.markdown('<div class="watermark">🎨 서울가동초 백인규</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("📋 4컷 만화 스토리보드 생성기 | 감정을 표현하고 창의성을 키워보세요!")
