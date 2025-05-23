import streamlit as st
import requests
import json
import base64
import os
import tempfile
import urllib.request
from dotenv import load_dotenv
from fpdf import FPDF

# -------------------------------
# 환경변수 로드
# -------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DALL_E_API_KEY = os.getenv("DALL_E_API_KEY")
CITY = "Seoul"

# -------------------------------
# 호출 제한 초기화 (하루 최대 20회만 허용)
# -------------------------------
if "call_count" not in st.session_state:
    st.session_state.call_count = 0

if st.session_state.call_count >= 20:
    st.error("오늘은 20회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
    st.stop()

# -------------------------------
# Gemini API 요청 함수
# -------------------------------
def ask_gemini(prompt, model="models/gemini-1.5-pro-latest"):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    result = response.json()
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except:
        st.error(str(result)); return "[오류] Gemini API 응답을 확인할 수 없습니다."

# -------------------------------
# 이미지 생성 (DALL·E)
# -------------------------------
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
        "size": "512x512"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["data"][0]["url"]
    else:
        return f"[오류] 이미지 생성 실패: {response.text}"

# -------------------------------
# 날씨 API
# -------------------------------
def get_weather():
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&lang=kr&units=metric"
    response = requests.get(weather_url)
    if response.status_code == 200:
        data = response.json()
        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return f"{description}, {temperature}°C"
    else:
        return "날씨 정보를 불러올 수 없습니다."

# -------------------------------
# Streamlit UI
# -------------------------------
st.sidebar.title("📊 사용량")
st.sidebar.metric(label="오늘의 생성 횟수", value=f"{st.session_state.call_count} / 20")

st.title("🌤️ 감정 + 날씨 기반 4컷 만화 생성기")

if "emotion" not in st.session_state:
    st.session_state.emotion = None
if "reason" not in st.session_state:
    st.session_state.reason = None

# Step 1: 감정 선택
if not st.session_state.emotion:
    st.subheader("1️⃣ 오늘 당신의 감정을 선택하세요")
    raw_emotions = ask_gemini("오늘의 감정을 나타내는 단어 5개만 제시해줘.")
    emotions = [e.strip("- ") for e in raw_emotions.split("\n") if e.strip()]
    selected_emotion = st.radio("감정을 선택하세요:", emotions)
    if st.button("확정하기", key="select_emotion"):
        st.session_state.emotion = selected_emotion
        st.rerun()

# Step 2: 이유 선택
elif not st.session_state.reason:
    st.subheader(f"2️⃣ '{st.session_state.emotion}' 감정의 이유를 선택하세요")
    prompt = f"'{st.session_state.emotion}'이라는 감정을 느끼는 이유 5개만 제시해줘."
    raw_reasons = ask_gemini(prompt)
    reasons = [r.strip("- ") for r in raw_reasons.split("\n") if r.strip()]
    selected_reason = st.radio("이유를 선택하세요:", reasons)
    if st.button("확정하기", key="select_reason"):
        st.session_state.reason = selected_reason
        st.rerun()

# Step 3: 만화 생성
elif st.session_state.reason:
    st.subheader("3️⃣ 만화 생성 결과")
    weather = get_weather()
    summary_prompt = f"감정: {st.session_state.emotion}\n이유: {st.session_state.reason}\n날씨: {weather}\n\n이 정보를 바탕으로 4컷 만화의 장면 설명을 각 컷마다 한 문장씩 해줘."
    summary = ask_gemini(summary_prompt)
    st.markdown(f"**날씨:** {weather}")
    st.text_area("🖼️ 4컷 만화 설명 (텍스트)", summary, height=250)

    st.subheader("🎨 생성된 컷 이미지")
    scenes = [line.strip("- ") for line in summary.split("\n") if line.strip()]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="감정 만화 생성 결과", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"감정: {st.session_state.emotion}\n이유: {st.session_state.reason}\n날씨: {weather}")

    for i, scene in enumerate(scenes):
        st.markdown(f"**컷 {i+1}**: {scene}")
        img_prompt = f"A colorful cartoon style illustration: {scene}"
        img_url = generate_image(img_prompt)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"컷 {i+1}: {scene}")
        if "http" in img_url:
            st.image(img_url, caption=f"컷 {i+1}", use_column_width=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                urllib.request.urlretrieve(img_url, tmp_img.name)
                pdf.image(tmp_img.name, w=100)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        with open(tmp_pdf.name, "rb") as f:
            st.download_button("📄 생성 결과 PDF 다운로드", f.read(), file_name="emotion_comic.pdf", mime="application/pdf")

    st.session_state.call_count += 1

