import streamlit as st
import requests
import json
import re
from datetime import datetime
import time

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY")
CITY = "Seoul"

st.set_page_config(
    page_title="4컷 만화 스토리보드 생성기", 
    page_icon="📋", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* 일반 텍스트는 검은색 */
    .stApp, .stApp *, .stMarkdown, .stMarkdown * {
        color: #000000 !important;
    }
    
    /* 입력 필드들은 검은 배경에 흰색 텍스트 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea,
    .stTextInput input,
    .stTextArea textarea {
        color: #ffffff !important;
        background-color: #2c3e50 !important;
    }
    
    /* 코드 블록은 흰색 텍스트 + 어두운 배경 */
    .stCode, .stCode *, code, pre {
        color: #ffffff !important;
        background: #2c3e50 !important;
    }
    
    /* 버튼은 흰색 텍스트 */
    .stButton > button, .stButton > button * {
        color: white !important;
        background: #3498db !important;
    }
    
    /* 워터마크 - 왼쪽 하단으로 */
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 12px;
        color: #666666;
        background: rgba(255, 255, 255, 0.8);
        padding: 5px 10px;
        border-radius: 5px;
        z-index: 99999;
        pointer-events: none;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
        max-width: 900px;
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
    .warning-box {
        background: #fff3cd;
        border: 1px solid #f39c12;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #27ae60;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .progress-container {
        width: 100%;
        height: 6px;
        background: #ecf0f1;
        border-radius: 3px;
        margin: 1rem 0;
    }
    .progress-bar {
        height: 100%;
        background: #3498db;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    # 현재 날짜 확인
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 날짜가 바뀌었으면 카운트 리셋
    if "last_date" not in st.session_state or st.session_state.last_date != today:
        st.session_state.call_count = 0
        st.session_state.last_date = today
    
    defaults = {
        "call_count": 0,
        "current_step": 1,
        "age_group": None,
        "gender": None,
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

def ask_gemini(prompt, model="models/gemini-1.5-pro-latest"):
    """Gemini API 호출 (개선된 오류 처리 + 안전 필터링)"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        
        result = response.json()
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # 생성된 결과에서도 부적절한 내용 필터링
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

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&lang=kr&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return f"{data['weather'][0]['description']}, {data['main']['temp']}°C"
    except:
        return "맑음, 20°C"

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
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress}%"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

init_session_state()

if st.session_state.call_count >= 20:
    st.error("🚫 오늘은 20회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
    st.stop()

st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📋 4컷 만화 스토리보드 생성기</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">감정과 상황을 바탕으로 4컷 만화 스토리보드와 최적화된 이미지 프롬프트를 만들어보세요!</p>', unsafe_allow_html=True)

render_step_indicator(st.session_state.current_step)

progress = (st.session_state.current_step - 1) * 25
render_progress_bar(progress)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # 현재 날짜 표시
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    st.metric(
        label=f"🎯 오늘의 생성 횟수 ({current_date})", 
        value=f"{st.session_state.call_count} / 20",
        delta=f"{20 - st.session_state.call_count}회 남음"
    )

if st.session_state.current_step == 1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # 안전 사용 안내
    st.markdown("""
    <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem;">
        <h4 style="color: #856404; margin-bottom: 1rem;">🛡️ 안전한 사용을 위한 안내</h4>
        <div style="color: #856404; font-size: 1rem; line-height: 1.6;">
            <strong>📚 이 도구는 초등학생의 건전한 감정 표현 학습을 위해 만들어졌습니다.</strong><br><br>
            
            <strong>🚫 다음과 같은 내용은 자동으로 차단됩니다:</strong><br>
            • 욕설, 폭언, 혐오 표현<br>
            • 폭력적이거나 위험한 내용<br>
            • 부적절한 성적 표현<br>
            • 정치적 인물이나 논란적 내용<br>
            • 의미 없는 글자 나열<br><br>
            
            <strong>✅ 이런 건전한 내용을 사용해주세요:</strong><br>
            • 친구와의 우정 이야기<br>
            • 학교에서의 즐거운 경험<br>
            • 가족과의 따뜻한 시간<br>
            • 새로운 것을 배우는 기쁨<br>
            • 도움을 주고받는 경험
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 시작 안내 메시지
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); border-radius: 15px; margin-bottom: 2rem;">
        <h3 style="color: #1976d2; margin-bottom: 1rem;">🎨 감정 표현 4컷 만화 만들기</h3>
        <p style="color: #424242; font-size: 1.1rem; margin-bottom: 0;">
            📚 교육 목표: 자신의 감정을 인식하고 표현하는 능력 향상<br>
            🎯 결과물: 4컷 만화 스토리보드 + AI 이미지 생성용 프롬프트
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("👤 사용자 나이대를 선택하세요")
    st.markdown("만화 스타일과 내용을 맞춤화하기 위해 나이대를 선택해주세요.")
    
    age_options = ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"]
    selected_age = st.radio("나이대 선택", age_options, horizontal=True)
    
    # 나이대별 특징 안내
    age_descriptions = {
        "초등학교 1~2학년": "🌟 간단하고 귀여운 스타일의 만화를 만들어요!",
        "초등학교 3~4학년": "🎨 조금 더 자세하고 재미있는 스토리를 만들어요!",
        "초등학교 5~6학년": "📖 감정 표현이 풍부하고 깊이 있는 만화를 만들어요!",
        "교사": "🎓 교육용으로 활용할 수 있는 전문적인 스토리보드를 만들어요!"
    }
    
    if selected_age:
        st.info(f"✨ {age_descriptions[selected_age]}")
    
    # 성별 선택 추가
    st.markdown("### 👦👧 주인공 성별을 선택하세요")
    gender = st.radio("성별 선택", ["남자", "여자"], horizontal=True)
    
    if gender:
        gender_emoji = "👦" if gender == "남자" else "👧"
        st.info(f"{gender_emoji} {gender} 주인공으로 만화를 만들어요!")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("다음 단계 ➡️"):
            if validate_age_group(selected_age) and gender:
                st.session_state.age_group = selected_age
                st.session_state.gender = gender
                st.session_state.current_step = 2
                st.rerun()
            else:
                if not gender:
                    st.error("성별을 선택해주세요!")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 어떤 상황인가요?")
    
    # 선택된 나이대에 맞는 예시 상황들 제공
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
    
    # 실시간 입력 검증
    if situation and len(situation.strip()) >= 5:
        # AI 기반 실시간 문맥 검증
        context_check_prompt = f"""
다음 텍스트가 초등학생에게 적합한지 문맥을 고려하여 판단해주세요:

텍스트: "{situation}"

판단 기준:
- 폭력적이거나 위험한 내용인가?
- 욕설이나 혐오 표현이 있는가?
- 성적이거나 부적절한 내용인가?
- 정치적 인물이나 논란적 내용인가?
- 의미있는 문장인가?
- 초등학생 교육환경에 적합한가?

예시:
- "친구와 죽 먹기" → 적합 (음식 이야기)
- "괴물을 죽이기" → 부적절 (폭력적 내용)
- "김정은 만나기" → 부적절 (정치적 인물)

"적합" 또는 "부적절" 중 하나로만 답변하세요:
"""
        
        try:
            ai_response = ask_gemini(context_check_prompt)
            
            if ai_response and "부적절" in ai_response:
                st.markdown(f'''
                <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    🚨 <strong>이 내용은 초등학생에게 적합하지 않아요!</strong><br><br>
                    📚 <strong>디지털 시민 교육:</strong> 학교에서는 모든 친구들이 안전하고 편안하게 느낄 수 있는 내용을 사용해야 해요.<br><br>
                    ✨ <strong>건전한 내용으로 바꿔주세요:</strong><br>
                    • 친구와 사이좋게 놀이터에서 놀았을 때<br>
                    • 선생님께 칭찬을 받아서 기뻤을 때<br>
                    • 새로운 것을 배워서 뿌듯했을 때
                </div>
                ''', unsafe_allow_html=True)
                situation_valid = False
            elif ai_response and "적합" in ai_response:
                st.markdown('<div style="background: #d4edda; border: 1px solid #27ae60; padding: 1rem; border-radius: 10px; margin: 1rem 0;">✅ 좋은 상황 설명이에요!</div>', unsafe_allow_html=True)
                situation_valid = True
            else:
                # AI 응답이 애매하면 기본 키워드 체크
                quick_check_words = ["시발", "병신", "김정은", "트럼프", "윤석열"]
                has_inappropriate = any(word in situation.lower() for word in quick_check_words)
                
                if has_inappropriate:
                    st.markdown('''
                    <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        🚨 <strong>부적절한 표현이 포함되어 있어요!</strong>
                    </div>
                    ''', unsafe_allow_html=True)
                    situation_valid = False
                else:
                    st.markdown('<div style="background: #d4edda; border: 1px solid #27ae60; padding: 1rem; border-radius: 10px; margin: 1rem 0;">✅ 좋은 상황 설명이에요!</div>', unsafe_allow_html=True)
                    situation_valid = True
        except:
            # AI 검증 실패 시 기본 키워드 체크
            quick_check_words = ["시발", "병신", "김정은", "트럼프", "윤석열"]
            has_inappropriate = any(word in situation.lower() for word in quick_check_words)
            
            if has_inappropriate:
                st.markdown('''
                <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    🚨 <strong>부적절한 표현이 포함되어 있어요!</strong>
                </div>
                ''', unsafe_allow_html=True)
                situation_valid = False
            else:
                situation_valid = len(situation.strip()) >= 10
    else:
        situation_valid = len(situation.strip()) >= 10 if situation else False
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        if st.button("다음 단계 ➡️", disabled=not situation_valid):
            if situation_valid:
                # 최종 AI 검증 (더 정확한 검사)
                is_valid, message = validate_text_input(situation, min_length=10, max_length=200, field_name="상황 설명")
                if is_valid:
                    st.session_state.situation = situation.strip()
                    st.session_state.emotion_options = fetch_emotions(st.session_state.situation)
                    st.session_state.current_step = 3
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("적절한 상황을 입력해주세요!")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("😊 이 상황에서 느낀 감정을 선택하세요")
    st.markdown("가장 강하게 느꼈던 감정 하나를 골라주세요.")
    
    st.markdown("### 🌟 긍정적인 감정")
    pos_cols = st.columns(5)
    for i, emotion in enumerate(st.session_state.emotion_options[0]):
        with pos_cols[i % 5]:
            if st.button(f"😊 {emotion}", key=f"pos_{emotion}"):
                st.session_state.emotion = emotion
                st.session_state.current_step = 4
                st.rerun()
    
    st.markdown("### 😔 부정적인 감정")
    neg_cols = st.columns(5)
    for i, emotion in enumerate(st.session_state.emotion_options[1]):
        with neg_cols[i % 5]:
            if st.button(f"😔 {emotion}", key=f"neg_{emotion}"):
                st.session_state.emotion = emotion
                st.session_state.current_step = 4
                st.rerun()
    
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
    
    # 실시간 입력 검증 (이유 입력)
    if reason and len(reason.strip()) >= 3:
        # AI 기반 문맥 검증
        reason_check_prompt = f"""
다음 텍스트가 초등학생에게 적합한지 문맥을 고려하여 판단해주세요:

텍스트: "{reason}"

판단 기준:
- 폭력적이거나 위험한 내용인가?
- 욕설이나 혐오 표현이 있는가?
- 성적이거나 부적절한 내용인가?
- 정치적 인물이나 논란적 내용인가?
- 의미있는 문장인가?
- 초등학생 교육환경에 적합한가?

"적합" 또는 "부적절" 중 하나로만 답변하세요:
"""
        
        try:
            ai_response = ask_gemini(reason_check_prompt)
            
            if ai_response and "부적절" in ai_response:
                st.markdown(f'''
                <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    🚨 <strong>이 내용은 초등학생에게 적합하지 않아요!</strong><br><br>
                    ✨ 감정의 이유를 건전하고 교육적으로 표현해주세요.
                </div>
                ''', unsafe_allow_html=True)
                reason_valid = False
            elif ai_response and "적합" in ai_response:
                st.markdown('<div style="background: #d4edda; border: 1px solid #27ae60; padding: 1rem; border-radius: 10px; margin: 1rem 0;">✅ 감정을 잘 표현해주셨어요!</div>', unsafe_allow_html=True)
                reason_valid = True
            else:
                # AI 응답이 애매하면 기본 체크
                quick_check_words = ["시발", "병신", "김정은", "트럼프"]
                has_inappropriate = any(word in reason.lower() for word in quick_check_words)
                
                if has_inappropriate:
                    st.markdown('''
                    <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        🚨 <strong>부적절한 표현이 포함되어 있어요!</strong>
                    </div>
                    ''', unsafe_allow_html=True)
                    reason_valid = False
                else:
                    st.markdown('<div style="background: #d4edda; border: 1px solid #27ae60; padding: 1rem; border-radius: 10px; margin: 1rem 0;">✅ 감정을 잘 표현해주셨어요!</div>', unsafe_allow_html=True)
                    reason_valid = True
        except:
            # AI 검증 실패 시 기본 키워드 체크
            quick_check_words = ["시발", "병신", "김정은", "트럼프"]
            has_inappropriate = any(word in reason.lower() for word in quick_check_words)
            
            if has_inappropriate:
                st.markdown('''
                <div style="background: #ffebee; border: 1px solid #f44336; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    🚨 <strong>부적절한 표현이 포함되어 있어요!</strong>
                </div>
                ''', unsafe_allow_html=True)
                reason_valid = False
            else:
                reason_valid = len(reason.strip()) >= 5
    else:
        reason_valid = len(reason.strip()) >= 5 if reason else False
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 3
            st.rerun()
    
    with col3:
        if st.button("🎨 스토리보드 생성하기!", disabled=not reason_valid):
            if reason_valid:
                is_valid, message = validate_text_input(reason, min_length=5, max_length=150, field_name="감정의 이유")
                if is_valid:
                    st.session_state.reason = reason.strip()
                    st.session_state.current_step = 5
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("적절한 이유를 입력해주세요!")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 당신만의 4컷 만화 스토리보드가 완성되었어요!")
    
    with st.expander("📋 입력 정보 확인", expanded=False):
        st.write(f"**👤 나이대:** {st.session_state.age_group}")
        st.write(f"**👦👧 성별:** {st.session_state.gender}")
        st.write(f"**📝 상황:** {st.session_state.situation}")
        st.write(f"**😊 감정:** {st.session_state.emotion}")
        st.write(f"**💭 이유:** {st.session_state.reason}")
    
    weather = get_weather()
    st.info(f"🌤️ **오늘의 서울 날씨:** {weather}")
    
    if not st.session_state.scenes:
        with st.spinner("📋 AI가 당신의 이야기를 4컷 만화 스토리보드로 만들고 있어요..."):
            summary_prompt = f"""
나이대: {st.session_state.age_group}
상황: {st.session_state.situation}
감정: {st.session_state.emotion}
이유: {st.session_state.reason}
날씨: {weather}

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
        
        # 프롬프트가 아직 생성되지 않았다면 생성
        if not st.session_state.scene_prompts:
            with st.spinner("🎨 각 장면별 최적화된 이미지 프롬프트를 생성하고 있어요..."):
                
                # 일관된 캐릭터 스타일 정의
                character_desc = f"{'Korean elementary school boy' if st.session_state.gender == '남자' else 'Korean elementary school girl'}"
                age_desc = st.session_state.age_group
                
                # 각 장면별로 개별 프롬프트 생성
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
                        # 일관성을 위한 기본 설정 추가
                        clean_prompt = ai_prompt.strip()
                        if ":" in clean_prompt:
                            clean_prompt = clean_prompt.split(":")[-1].strip()
                        
                        # 캐릭터 일관성 + 안전성 보장
                        safe_prompt = f"Safe for children, educational content. Cute anime/manga style illustration of a {character_desc} ({age_desc}) showing {st.session_state.emotion} emotion. {clean_prompt}. Wholesome, school-appropriate, consistent character design, colorful, child-friendly art style."
                        st.session_state.scene_prompts.append(safe_prompt)
                    else:
                        # 안전한 기본 프롬프트
                        default_prompt = f"Safe for children, educational content. Cute anime/manga style illustration of a {character_desc} ({age_desc}) showing {st.session_state.emotion} emotion in this scene: {scene}. Wholesome, school-appropriate, consistent character design, colorful, child-friendly art style."
                        st.session_state.scene_prompts.append(default_prompt)
        
        # 생성된 장면과 프롬프트 표시
        for i, scene in enumerate(st.session_state.scenes):
            st.markdown(f"### 🎬 컷 {i+1}")
            st.write(f"**장면 설명:** {scene}")
            
            st.divider()
    else:
        st.error("❌ 장면 생성에 실패했습니다. '다시 만들기' 버튼을 눌러 다시 시도해주세요.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 다시 만들기"):
            keys_to_reset = ["age_group", "gender", "situation", "emotion", "reason", "scenes", "scene_prompts", "emotion_options", "counted"]
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
        
    # 4컷 만화 통합 프롬프트만 제공
    if st.session_state.scenes and st.session_state.scene_prompts:
        st.markdown("---")
        st.markdown("### 🎬 4컷 만화 생성 프롬프트")
        
        # 4컷 만화 생성용 통합 프롬프트
        character_desc = f"{'Korean elementary school boy' if st.session_state.gender == '남자' else 'Korean elementary school girl'}"
        
        four_panel_prompt = f"""Create a 4-panel comic strip (네컷 만화) with consistent character design throughout all panels:

Character: {character_desc} ({st.session_state.age_group})
Story theme: {st.session_state.situation}
Main emotion: {st.session_state.emotion}
Reason for emotion: {st.session_state.reason}

Panel 1: {st.session_state.scenes[0] if len(st.session_state.scenes) > 0 else ""}
Panel 2: {st.session_state.scenes[1] if len(st.session_state.scenes) > 1 else ""}
Panel 3: {st.session_state.scenes[2] if len(st.session_state.scenes) > 2 else ""}
Panel 4: {st.session_state.scenes[3] if len(st.session_state.scenes) > 3 else ""}

Art style: Cute anime/manga style, safe for children, educational content, wholesome, school-appropriate, consistent character design across all panels, colorful, child-friendly."""
        
        st.markdown("**🎨 아래 프롬프트를 복사해서 AI 이미지 생성 사이트에 붙여넣으세요:**")
        st.text_area("4컷 만화 생성 프롬프트", four_panel_prompt, height=250, key="four_panel_final")
        
        # 추천 이미지 생성 사이트들
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

# 워터마크 추가
st.markdown('<div class="watermark">서울가동초 백인규</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #000000; padding: 1rem;'>"
    "📋 4컷 만화 스토리보드 생성기 | 감정을 표현하고 창의성을 키워보세요!"
    "</div>", 
    unsafe_allow_html=True
)
