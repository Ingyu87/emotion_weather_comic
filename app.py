import streamlit as st
import requests
import json

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY")
DALL_E_API_KEY = st.secrets.get("DALL_E_API_KEY") or st.secrets.get("OPENAI_API_KEY")
CITY = "Seoul"

if "call_count" not in st.session_state:
    st.session_state.call_count = 0

if st.session_state.call_count >= 20:
    st.error("오늘은 20회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
    st.stop()

def ask_gemini(prompt, model="models/gemini-1.5-pro-latest"):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    result = response.json()
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except:
        st.error(str(result)); return "[오류] Gemini API 응답을 확인할 수 없습니다."

def generate_image(prompt):
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
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["data"][0]["url"]
    else:
        st.warning(f"이미지 생성 오류: {response.status_code} - {response.text}")
        return ""

def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&lang=kr&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"{data['weather'][0]['description']}, {data['main']['temp']}°C"
    else:
        return "날씨 정보를 불러올 수 없습니다."

st.set_page_config(layout="wide")
st.sidebar.title("📊 사용량")
st.sidebar.metric(label="오늘의 생성 횟수", value=f"{st.session_state.call_count} / 20")
st.title("🌤️ 감정 + 날씨 기반 4컷 만화 생성기")

if "age_group" not in st.session_state:
    st.session_state.age_group = None
if "situation" not in st.session_state:
    st.session_state.situation = None
if "emotion" not in st.session_state:
    st.session_state.emotion = None
if "reason" not in st.session_state:
    st.session_state.reason = None

if not st.session_state.age_group:
    st.subheader("👤 사용자 나이대를 선택하세요")
    age = st.radio("나이대 선택", ["초등학교 1~2학년", "초등학교 3~4학년", "초등학교 5~6학년", "교사"], horizontal=True)
    if st.button("확인", key="age_btn"):
        st.session_state.age_group = age
        st.rerun()

elif not st.session_state.situation:
    st.subheader("📝 어떤 상황인가요?")
    situation = st.text_area("오늘 있었던 상황이나 기억에 남는 일을 짧게 적어주세요")
    col1, col2 = st.columns(2)
    if col1.button("이전", key="back_age"):
        st.session_state.age_group = None
        st.rerun()
    if col2.button("다음", key="situation_btn") and situation.strip():
        st.session_state.situation = situation.strip()
        st.rerun()

elif not st.session_state.emotion:
    st.subheader("😊 이 상황에서 느낀 감정을 골라보세요")
    prompt = (
        f"{st.session_state.age_group}이(가) 겪은 다음 상황에 대해 느낄 수 있는 긍정적 감정 5개와 부정적 감정 5개를 콤마로 구분해서 제시해줘. "
        f"감정 이름만 간단히 제시해. 상황: {st.session_state.situation}"
    )
    raw = ask_gemini(prompt)
    emotions = [e.strip() for e in raw.split(",") if e.strip()]
    cols = st.columns(5)
    for i, emo in enumerate(emotions):
        if cols[i % 5].button(emo):
            st.session_state.emotion = emo
            st.rerun()
    if st.button("이전", key="back_situation"):
        st.session_state.situation = None
        st.rerun()

elif not st.session_state.reason:
    st.subheader("🔍 그 감정을 느낀 이유를 작성해주세요")
    reason = st.text_area("그 감정을 느낀 이유는 무엇인가요?")
    col1, col2 = st.columns(2)
    if col1.button("이전", key="back_emotion"):
        st.session_state.emotion = None
        st.rerun()
    if col2.button("만화 생성하기") and reason.strip():
        st.session_state.reason = reason.strip()
        st.rerun()

else:
    st.subheader("🎬 생성된 4컷 만화")
    weather = get_weather()
    st.markdown(f"**📍 오늘의 날씨:** {weather}")

    summary_prompt = f"나이대: {st.session_state.age_group}\n상황: {st.session_state.situation}\n감정: {st.session_state.emotion}\n이유: {st.session_state.reason}\n날씨: {weather}\n\n이 정보를 바탕으로 4컷 만화의 장면 설명을 한 컷씩 나눠서 작성해줘. 각 장면은 한 문장으로 구성."
    result = ask_gemini(summary_prompt)
    scenes = [line.strip("- ") for line in result.split("\n") if line.strip()]
    for i, scene in enumerate(scenes):
        st.markdown(f"**컷 {i+1}**: {scene}")
        img_prompt = (
            f"Cartoon style illustration showing a {st.session_state.age_group} in a scene where they feel '{st.session_state.emotion}' "
            f"because '{st.session_state.reason}', in the context of '{st.session_state.situation}', with weather: {weather}. "
            f"Scene detail: {scene}"
        )
        url = generate_image(img_prompt)
        if "http" in url:
            st.image(url, caption=f"컷 {i+1}", use_column_width=True)
        else:
            st.warning(f"❌ 컷 {i+1} 이미지 생성에 실패했어요. 다시 시도해보거나 API 키를 확인해주세요.")

    st.session_state.call_count += 1


