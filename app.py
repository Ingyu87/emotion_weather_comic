# 개선된 사용량 제한 옵션들

# 옵션 1: 쿠키 기반 (브라우저 닫아도 유지)
import streamlit as st
from datetime import datetime
import json

def init_usage_tracking_cookie():
    """쿠키 기반 사용량 추적 (더 지속적)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # JavaScript로 쿠키 읽기/쓰기
    cookie_script = f"""
    <script>
    function getCookie(name) {{
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {{
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {{
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }}
            }}
        }}
        return cookieValue;
    }}
    
    function setCookie(name, value, days) {{
        let expires = "";
        if (days) {{
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }}
        document.cookie = name + "=" + (value || "") + expires + "; path=/";
    }}
    
    // 현재 사용량 확인
    const today = "{today}";
    const usageData = getCookie('comic_usage');
    let currentUsage = {{ date: today, count: 0 }};
    
    if (usageData) {{
        try {{
            const parsed = JSON.parse(usageData);
            if (parsed.date === today) {{
                currentUsage = parsed;
            }}
        }} catch (e) {{
            console.log('Cookie parsing error:', e);
        }}
    }}
    
    // Streamlit에 데이터 전달
    window.parent.postMessage({{
        type: 'usage_data',
        data: currentUsage
    }}, '*');
    </script>
    """
    
    st.markdown(cookie_script, unsafe_allow_html=True)

# 옵션 2: localStorage 기반 (더 간단)
def init_usage_tracking_local():
    """localStorage 기반 사용량 추적"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    local_storage_script = f"""
    <script>
    const today = "{today}";
    const storageKey = 'comic_usage_data';
    
    // 기존 데이터 확인
    let usageData = localStorage.getItem(storageKey);
    let currentUsage = {{ date: today, count: 0 }};
    
    if (usageData) {{
        try {{
            const parsed = JSON.parse(usageData);
            if (parsed.date === today) {{
                currentUsage = parsed;
            }} else {{
                // 날짜가 다르면 리셋
                currentUsage = {{ date: today, count: 0 }};
                localStorage.setItem(storageKey, JSON.stringify(currentUsage));
            }}
        }} catch (e) {{
            console.log('LocalStorage parsing error:', e);
            localStorage.removeItem(storageKey);
        }}
    }}
    
    // 사용량 증가 함수
    window.incrementUsage = function() {{
        currentUsage.count += 1;
        localStorage.setItem(storageKey, JSON.stringify(currentUsage));
        return currentUsage.count;
    }};
    
    // 현재 사용량 반환 함수
    window.getCurrentUsage = function() {{
        return currentUsage.count;
    }};
    
    console.log('Current usage:', currentUsage.count);
    </script>
    """
    
    st.markdown(local_storage_script, unsafe_allow_html=True)

# 옵션 3: 서버 기반 (가장 확실하지만 복잡)
import hashlib
import pickle
import os

def get_user_id():
    """사용자 고유 ID 생성 (IP 기반)"""
    # 실제로는 더 정교한 방법 필요
    user_agent = st.context.headers.get("user-agent", "")
    remote_ip = st.context.headers.get("x-forwarded-for", "unknown")
    unique_string = f"{remote_ip}_{user_agent}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def init_usage_tracking_server():
    """서버 파일 기반 사용량 추적 (가장 확실)"""
    today = datetime.now().strftime("%Y-%m-%d")
    user_id = get_user_id()
    
    usage_dir = "usage_data"
    if not os.path.exists(usage_dir):
        os.makedirs(usage_dir)
    
    usage_file = os.path.join(usage_dir, f"{user_id}_{today}.pkl")
    
    try:
        if os.path.exists(usage_file):
            with open(usage_file, 'rb') as f:
                usage_count = pickle.load(f)
        else:
            usage_count = 0
    except:
        usage_count = 0
    
    return usage_count, usage_file

def increment_usage_server(usage_file, current_count):
    """서버 사용량 증가"""
    new_count = current_count + 1
    try:
        with open(usage_file, 'wb') as f:
            pickle.dump(new_count, f)
    except:
        pass
    return new_count

# 옵션 4: Streamlit secrets 기반 (간단한 서버 방식)
def init_usage_tracking_simple():
    """간단한 파일 기반 추적"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 간단한 텍스트 파일로 관리
    usage_file = f"daily_usage_{today}.txt"
    
    try:
        if os.path.exists(usage_file):
            with open(usage_file, 'r') as f:
                count = int(f.read().strip())
        else:
            count = 0
    except:
        count = 0
    
    return count

def increment_simple_usage():
    """간단한 사용량 증가"""
    today = datetime.now().strftime("%Y-%m-%d")
    usage_file = f"daily_usage_{today}.txt"
    
    current_count = init_usage_tracking_simple()
    new_count = current_count + 1
    
    try:
        with open(usage_file, 'w') as f:
            f.write(str(new_count))
    except:
        pass
    
    return new_count

# 사용 예시
def check_usage_limit():
    """사용량 제한 확인"""
    # 현재 방식 (세션 기반)
    if "call_count" not in st.session_state:
        st.session_state.call_count = 0
    
    # 추가로 더 지속적인 방식도 병행
    persistent_count = init_usage_tracking_simple()
    
    # 둘 중 높은 값 사용
    actual_count = max(st.session_state.call_count, persistent_count)
    
    if actual_count >= 100:
        st.error("🚫 오늘은 100회까지만 생성할 수 있습니다. 내일 다시 이용해 주세요.")
        st.info(f"현재 사용량: {actual_count}/100")
        return False
    
    return True

def increment_all_usage():
    """모든 방식의 사용량 증가"""
    # 세션 증가
    st.session_state.call_count = st.session_state.get('call_count', 0) + 1
    
    # 파일 증가
    increment_simple_usage()
    
    # 사용량 표시
    current = st.session_state.call_count
    st.info(f"오늘 사용량: {current}/100")
