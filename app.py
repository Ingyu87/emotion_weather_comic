/* 전역 텍스트 색상 강제 적용 */
.stApp * {
    color: #000000 !important;
}

.stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #000000 !important;
}

.stRadio label, .stTextArea label {
    color: #000000 !important;
}

/* 버튼 텍스트는 흰색 유지 */
.stButton > button {
    color: white !important;
}import streamlit as st
import requests
import json
import re
from datetime import datetime
import time

# API 키 설정
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY")
DALL_E_API_KEY = st.secrets.get("DALL_E_API_KEY") or st.secrets.get("OPENAI_API_KEY")
CITY = "Seoul"

# 페이지 설정
st.set_page_config(
    page_title="AI 4컷 만화 생성기", 
    page_icon="🎨", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS
st.markdown("""
<style>
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
        backdrop-filter: blur(10px);
        max-width: 900px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .main-title {
        text-align: center;
        color: #000000;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #000000;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 500;
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
        position: relative;
    }
    
    .step.active {
        background: #3498db;
        color: white;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
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
        border: 1px solid #e8ecef;
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
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
    }
    
    .stButton > button:hover {
        background: #2980b9;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(52, 152, 219, 0.4);
    }
    
    .emotion-btn {
        padding: 1rem;
        border-radius: 15px;
        border: 2px solid #e8ecef;
        background: white;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .emotion-btn:hover {
        border-color: #3498db;
        background: #f8f9ff;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #f39c12;
        color: #000000;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #27ae60;
        color: #000000;
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

# 세션 상태 초기화
def init_session_state():
    defaults = {
        "call_count": 0,
        "current_step": 1,
        "age_group": None,
        "situation": None,
        "emotion": None,
        "reason": None,
        "emotion_options": ([], []),
        "scenes": [],
        "generated_images": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# 입력 검증 함수들
def validate_text_input(text, min_length=5, max_length=200, field_name="입력"):
    if not text or not text.strip():
        return False, f"{field_name}을 입력해주세요."
    
    text = text.strip()
    if len(text) < min_length:
        return False, f"{field_name}은 최소 {min_length}자 이상 입력해주세요."
    
    if len(text) > max_length:
        return False, f"{field_name}은 최대 {max_length}자까지 입력 가능합니다."
    
    inappropriate_words = ["욕설", "비방", "혐오", "폭력"]
    for word in inappropriate_words:
        if word in text:
            return False, "부적절한 내용이 포함되어 있습니다. 다시 입력해주세요."
    
    return True, ""

def validate_age_group(age_group):
    valid_ages = ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"]
    return age_group in valid_ages

# API 함수들
def ask_gemini(prompt, model="models/gemini-1.5-pro-latest"):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
        
    except requests.exceptions.Timeout:
        return "[오류] 요청 시간이 초과되었습니다."
    except requests.exceptions.RequestException as e:
        return f"[오류] 네트워크 오류: {str(e)}"
    except KeyError:
        return "[오류] API 응답 형식이 올바르지 않습니다."
    except Exception as e:
        return f"[오류] 예상치 못한 오류: {str(e)}"

def generate_image(prompt):
    try:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {DALL_E_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        return response.json()["data"][0]["url"]
        
    except:
        return ""

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

# UI 컴포넌트들
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

# 메인 앱
init_session_state()

if st.session_state.call_count >= 20:
    st.error("🚫 오늘은 20회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
    st.stop()

st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎨 AI 4컷 만화 생성기</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">감정과 상황을 바탕으로 나만의 특별한 4컷 만화를 만들어보세요!</p>', unsafe_allow_html=True)

render_step_indicator(st.session_state.current_step)

progress = (st.session_state.current_step - 1) * 25
render_progress_bar(progress)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.metric(
        label="🎯 오늘의 생성 횟수", 
        value=f"{st.session_state.call_count} / 20",
        delta=f"{20 - st.session_state.call_count}회 남음"
    )

if st.session_state.current_step == 1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("👤 사용자 나이대를 선택하세요")
    st.markdown("만화 스타일과 내용을 맞춤화하기 위해 나이대를 선택해주세요.")
    
    age_options = ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"]
    selected_age = st.radio("나이대 선택", age_options, horizontal=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("다음 단계 ➡️"):
            if validate_age_group(selected_age):
                st.session_state.age_group = selected_age
                st.session_state.current_step = 2
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 어떤 상황인가요?")
    st.markdown("오늘 있었던 일이나 기억에 남는 상황을 자세히 적어주세요.")
    
    situation = st.text_area(
        "상황 설명",
        placeholder="예: 친구와 함께 놀이터에서 놀다가 넘어져서 무릎이 다쳤어요.",
        height=100
    )
    
    char_count = len(situation) if situation else 0
    st.caption(f"글자 수: {char_count}/200")
    
    if situation:
        is_valid, message = validate_text_input(situation, min_length=10, max_length=200, field_name="상황 설명")
        if not is_valid:
            st.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ 좋은 상황 설명이에요!</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        if st.button("다음 단계 ➡️"):
            is_valid, message = validate_text_input(situation, min_length=10, max_length=200, field_name="상황 설명")
            if is_valid:
                st.session_state.situation = situation.strip()
                st.session_state.emotion_options = fetch_emotions(st.session_state.situation)
                st.session_state.current_step = 3
                st.rerun()
            else:
                st.error(message)
    
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
        height=100
    )
    
    char_count = len(reason) if reason else 0
    st.caption(f"글자 수: {char_count}/150")
    
    if reason:
        is_valid, message = validate_text_input(reason, min_length=5, max_length=150, field_name="감정의 이유")
        if not is_valid:
            st.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ 감정을 잘 표현해주셨어요!</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.current_step = 3
            st.rerun()
    
    with col3:
        if st.button("🎨 만화 생성하기!"):
            is_valid, message = validate_text_input(reason, min_length=5, max_length=150, field_name="감정의 이유")
            if is_valid:
                st.session_state.reason = reason.strip()
                st.session_state.current_step = 5
                st.rerun()
            else:
                st.error(message)
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎬 당신만의 4컷 만화가 완성되었어요!")
    
    with st.expander("📋 입력 정보 확인", expanded=False):
        st.write(f"**👤 나이대:** {st.session_state.age_group}")
        st.write(f"**📝 상황:** {st.session_state.situation}")
        st.write(f"**😊 감정:** {st.session_state.emotion}")
        st.write(f"**💭 이유:** {st.session_state.reason}")
    
    weather = get_weather()
    st.info(f"🌤️ **오늘의 서울 날씨:** {weather}")
    
    if not st.session_state.scenes:
        with st.spinner("🎨 AI가 당신의 이야기를 4컷 만화로 만들고 있어요..."):
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
        
        for i, scene in enumerate(st.session_state.scenes):
            st.markdown(f"### 🎬 컷 {i+1}")
            st.write(f"**장면:** {scene}")
            
            if len(st.session_state.generated_images) <= i:
                with st.spinner(f"컷 {i+1} 이미지를 생성하는 중..."):
                    img_prompt = f"""
Create a colorful, child-friendly cartoon illustration showing:
- A {st.session_state.age_group} character 
- Scene: {scene}
- Emotion: {st.session_state.emotion}
- Setting related to: {st.session_state.situation}
- Art style: cute, colorful, manga/anime style, appropriate for children
- No text in the image
"""
                    
                    image_url = generate_image(img_prompt)
                    if image_url:
                        st.session_state.generated_images.append(image_url)
                    else:
                        st.session_state.generated_images.append("")
            
            if len(st.session_state.generated_images) > i:
                if st.session_state.generated_images[i]:
                    st.image(st.session_state.generated_images[i], caption=f"컷 {i+1}: {scene}", use_column_width=True)
                else:
                    st.warning(f"⚠️ 컷 {i+1} 이미지 생성에 실패했습니다.")
                    if st.button(f"🔄 컷 {i+1} 다시 생성", key=f"retry_{i}"):
                        with st.spinner(f"컷 {i+1} 이미지를 다시 생성하는 중..."):
                            img_prompt = f"Create a colorful, child-friendly cartoon illustration: Scene: {scene}, Character: {st.session_state.age_group}, Emotion: {st.session_state.emotion}, Style: cute anime/manga"
                            new_image_url = generate_image(img_prompt)
                            if new_image_url:
                                st.session_state.generated_images[i] = new_image_url
                                st.rerun()
            
            st.divider()
    else:
        st.error("❌ 장면 생성에 실패했습니다. '다시 만들기' 버튼을 눌러 다시 시도해주세요.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 다시 만들기"):
            keys_to_reset = ["age_group", "situation", "emotion", "reason", "scenes", "generated_images", "emotion_options", "counted"]
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
            st.success("🎉 멋진 4컷 만화가 완성되었어요! 스크린샷으로 저장해서 친구들과 공유해보세요!")
    
    if st.session_state.scenes and not hasattr(st.session_state, 'counted'):
        st.session_state.call_count += 1
        st.session_state.counted = True
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #000000; padding: 1rem;'>"
    "🎨 AI 4컷 만화 생성기 | 감정을 표현하고 창의성을 키워보세요!"
    "</div>", 
    unsafe_allow_html=True
)
