import streamlit as st
import os
import time
import uuid  # 新增：用于生成唯一文件名，防止冲突
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="VOID PROPHET | Cyber Oracle",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. 赛博风格 CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400&display=swap');
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        color: #e0e0e0;
        font-family: 'Roboto Mono', monospace;
    }
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ff41;
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.6);
    }
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1f2937;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(20, 20, 20, 0.8);
        color: #00ff41;
        border: 1px solid #333;
        border-radius: 4px;
        font-family: 'Roboto Mono', monospace;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #004d1a, #00802b);
        border: 1px solid #00ff41;
        color: white;
        padding: 10px 20px;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background: #00ff41;
        color: black;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.8);
        transform: scale(1.02);
    }
    /* 优化 SVG 显示容器 */
    .chart-container {
        display: flex;
        justify-content: center;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.1);
    }
    a { color: #ff00ff !important; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化 API ---
try:
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
except Exception:
    st.error("⚠️ SYSTEM ALERT: API Credentials Missing.")
    st.stop()

# --- 4. 核心功能：精准定位与排盘 ---

def get_geo_data(city_name):
    """获取城市的经纬度和时区"""
    # 1. 常用城市快速字典
    quick_lookup = {
        "beijing": (39.9042, 116.4074, "Asia/Shanghai"),
        "北京": (39.9042, 116.4074, "Asia/Shanghai"),
        "shanghai": (31.2304, 121.4737, "Asia/Shanghai"),
        "上海": (31.2304, 121.4737, "Asia/Shanghai"),
        "guangzhou": (23.1291, 113.2644, "Asia/Shanghai"),
        "shenzhen": (22.5431, 114.0579, "Asia/Shanghai"),
        "chengdu": (30.5728, 104.0668, "Asia/Shanghai"),
        "hong kong": (22.3193, 114.1694, "Asia/Hong_Kong"),
        "new york": (40.7128, -74.0060, "America/New_York"),
        "london": (51.5074, -0.1278, "Europe/London"),
        "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
    }
    
    city_lower = city_name.lower().strip()
    if city_lower in quick_lookup:
        return quick_lookup[city_lower]
    
    # 2. 在线查询
    try:
        geolocator = Nominatim(user_agent="cyber_oracle_app_v4")
        location = geolocator.geocode(city_name)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
    except Exception as e:
        print(f"Geo Error: {e}")
        return None

    return None

def generate_chart_svg(name, year, month, day, hour, minute, city):
    """V4.1 核心排盘逻辑：并发安全 + 自动清理"""
    
    # 1. 获取坐标
    geo_data = get_geo_data(city)
    if not geo_data:
        return None, None, f"LOCATION ERROR: Could not find '{city}'. Try a major city name."
    
    lat, lng, tz_str = geo_data
    
    try:
        year, month, day = int(year), int(month), int(day)
        hour, minute = int(hour), int(minute)
        
        # 2. 生成唯一的随机ID，防止文件冲突
        # 用户虽然输入 "Neo"，但系统内部生成文件叫 "Neo_a1b2c3..."
        unique_id = uuid.uuid4().hex[:8]
        safe_filename_base = f"{name}_{unique_id}".replace(" ", "_")

        # 3. 创建星盘对象
        subject = AstrologicalSubject(
            safe_filename_base, 
            year, month, day, hour, minute, 
            city=city, 
            lat=lat, lng=lng, tz_str=tz_str,
            online=False
        )
        
        # 4. 生成 SVG
        chart = KerykeionChartSVG(subject, theme="dark")
        chart.makeSVG()
        
        # 5. 读取内容并删除临时文件
        expected_filename = f"{safe_filename_base}_Chart.svg"
        
        if os.path.exists(expected_filename):
            with open(expected_filename, "r", encoding="utf-8") as f:
                svg_content = f.read()
            
            # 删除临时文件 (关键步骤！)
            os.remove(expected_filename)
            
            # 将对象的名字改回用户输入的名字，以便后续 AI 称呼用户
            subject.name = name
            
            return svg_content, subject, None
        else:
            return None, None, "RENDER ERROR: SVG generation failed."
            
    except Exception as e:
        return None, None, f"CALCULATION ERROR: {str(e)}"

def get_cyber_interpretation(subject_info, question):
    """赛博 AI 解读"""
    
    sun_sign = subject_info.sun['sign']
    moon_sign = subject_info.moon['sign']
    asc_sign = subject_info.first_house['sign']
    
    chart_data_str = f"""
    [Natal Data Verified]
    Sun: {sun_sign}
    Moon: {moon_sign}
    Ascendant: {asc_sign}
    Mercury: {subject_info.mercury['sign']}
    Venus: {subject_info.venus['sign']}
    Mars: {subject_info.mars['sign']}
    Jupiter: {subject_info.jupiter['sign']}
    Saturn: {subject_info.saturn['sign']}
    """

    system_prompt = """
    Role: You are "Void Prophet" (Cyber Oracle) from 2077.
    Task: Interpret the user's verified natal chart and question.
    
    IMPORTANT: You must base your analysis STRICTLY on the provided [Natal Data Verified]. 
    DO NOT hallucinate planetary positions.
    
    Style:
    - Tone: Cold, mysterious, tech-noir.
    - Metaphors: Astrology terms -> Cyberpunk concepts (e.g., Saturn = Firewall, Moon = Core Drive).
    
    Structure:
    1. [SIGNAL DETECTED]: Brief greeting.
    2. [CORE DUMP]: Analyze Sun, Moon, Ascendant using the verified signs.
    3. [PREDICTION ALGORITHM]: Answer the user's specific question.
    4. [ACTION PROTOCOL]: One specific, actionable advice.
    """
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{chart_data_str}\n\nUser Question: {question}"}
            ],
            stream=True
        )
        return stream
    except Exception as e:
        return f"Error: Uplink failed. {e}"

# --- 5. 界面布局 ---

with st.sidebar:
    st.title("💾 ACCESS_PORT")
    st.markdown("---")
    name = st.text_input("IDENTITY (Name)", "Neo")
    
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1: year = st.number_input("Year", 1950, 2030, 1989, step=1)
    with col2: month = st.number_input("Mon", 1, 12, 11, step=1)
    with col3: day = st.number_input("Day", 1, 31, 11, step=1)
    
    col4, col5 = st.columns(2)
    with col4: hour = st.number_input("Hour", 0, 23, 11, step=1)
    with col5: minute = st.number_input("Min", 0, 59, 57, step=1)
    
    city = st.text_input("CITY (Auto-Detect)", "Beijing")
    
    st.markdown("---")
    question = st.text_area("QUERY (Your Question)", "Will I achieve financial freedom?")
    
    st.markdown("### 🔋 ENERGY_CELL")
    st.markdown(
        """
        <button style="
            background: #ff00ff; border: none; color: white; width: 100%; padding: 10px; font-weight: bold; cursor: pointer;
        ">
        ⚡ INJECT CREDITS (DONATE)
        </button>
        """, 
        unsafe_allow_html=True
    )

st.title("🔮 VOID PROPHET")
st.caption("Quantum Astrology System v2077.4 (Precision Core) // Online")

if st.button(">> INITIALIZE SEQUENCE <<"):
    if not city:
        st.warning("⚠️ ALERT: Location data missing.")
    else:
        bar = st.progress(0)
        status = st.empty()
        
        # 1. 计算
        status.markdown("`Triangulating Coordinates...`")
        bar.progress(20)
        
        svg_content, subject_obj, error_msg = generate_chart_svg(name, year, month, day, hour, minute, city)
        
        if error_msg:
            bar.progress(0)
            status.error("❌ FATAL ERROR: " + error_msg)
            st.error("System halted. Please check city spelling.")
        else:
            # 2. 显示星盘
            bar.progress(50)
            status.markdown("`Rendering Natal Matrix...`")
            
            if svg_content:
                # 使用 HTML div 容器直接渲染 SVG，比 st.image 更清晰且支持透明背景
                st.markdown(f'<div class="chart-container">{svg_content}</div>', unsafe_allow_html=True)
            
            # 3. AI 解读
            bar.progress(75)
            status.markdown("`Establishing Quantum Link...`")
            
            st.markdown("---")
            st.subheader("📟 ORACLE TRANSMISSION")
            res_box = st.empty()
            full_text = ""
            
            ai_stream = get_cyber_interpretation(subject_obj, question)
            
            if isinstance(ai_stream, str):
                res_box.error(ai_stream)
            else:
                for chunk in ai_stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_text += content
                        res_box.markdown(full_text + " ▌")
                res_box.markdown(full_text)
                
            bar.progress(100)
            status.empty()
            st.success("✅ TRANSMISSION COMPLETE")
