import streamlit as st
import os
import time
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from openai import OpenAI
from streamlit_extras.stylable_container import stylable_container

# --- 1. 页面配置与专业级赛博 CSS ---
st.set_page_config(
    page_title="VOID PROPHET | Cyber Oracle",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 注入 CSS：高科技黑客风 (High-Tech Noir)
st.markdown("""
<style>
    /* 引入谷歌字体：Orbitron (科幻标题) 和 Roboto Mono (代码正文) */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400&display=swap');

    /* 全局背景：深邃的矩阵黑 */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        color: #e0e0e0;
        font-family: 'Roboto Mono', monospace;
    }

    /* 标题特效 */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ff41; /* 矩阵绿 */
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.6);
    }
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1f2937;
    }
    
    /* 输入框：半透明磨砂玻璃感 */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(20, 20, 20, 0.8);
        color: #00ff41;
        border: 1px solid #333;
        border-radius: 4px;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* 按钮：实心发光按钮 */
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
    
    /* 进度条 */
    .stProgress > div > div > div > div {
        background-color: #00ff41;
        box-shadow: 0 0 10px #00ff41;
    }
    
    /* 链接样式 */
    a { color: #ff00ff !important; text-decoration: none; transition: 0.3s; }
    a:hover { text-shadow: 0 0 8px #ff00ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 API ---
try:
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
except Exception:
    st.error("⚠️ SYSTEM ALERT: API Credentials Missing. Check Streamlit Secrets.")
    st.stop()

# --- 3. 核心功能 (已修复 Bug) ---

def get_cyber_interpretation(user_data, question):
    """赛博风格 AI 解读"""
    system_prompt = """
    Role: You are "Void Prophet" (Cyber Oracle) from 2077.
    Task: Interpret the user's natal chart and question.
    Style:
    - Tone: Cold, mysterious, tech-savvy (Cyberpunk).
    - Metaphors: Use tech terms for astrology (e.g., Saturn -> Firewall, Retrograde -> Glitch).
    - Structure:
      [SIGNAL DETECTED]: Brief greeting.
      [SYSTEM SCAN]: Analysis of Sun/Moon/Rising.
      [CALCULATION]: Answer the question.
      [PROTOCOL]: One actionable advice.
    Language: English. Keep it concise (under 200 words).
    """
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo", # 可根据你的API支持情况修改，如 gpt-4o-mini
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Data: {user_data}\nQuestion: {question}"}
            ],
            stream=True
        )
        return stream
    except Exception as e:
        return f"Error: Uplink failed. {e}"

def generate_chart_svg(name, year, month, day, hour, minute, city, country):
    """生成 SVG 星盘 (带防崩溃机制)"""
    try:
        # 1. 强制转为整数，防止手机端输入产生小数导致报错
        year, month, day = int(year), int(month), int(day)
        hour, minute = int(hour), int(minute)
        
        # 2. 使用临时文件名，避免因用户名字含特殊字符导致文件名乱码找不到
        temp_name = "Subject_01"
        
        # 3. 生成星盘对象
        # 注意：Kerykeion 需要正确的国家代码 (如 CN, US, GB) 才能更准地找到城市
        subject = AstrologicalSubject(temp_name, year, month, day, hour, minute, city=city, nation=country)
        chart = KerykeionChartSVG(subject, theme="dark")
        chart.makeSVG()
        
        # 4. 读取生成的文件
        svg_file = f"{temp_name}_Chart.svg"
        
        if os.path.exists(svg_file):
            with open(svg_file, "r", encoding="utf-8") as f:
                svg_content = f.read()
            # 成功！返回内容
            return svg_content, subject
        else:
            # 失败：文件未生成 (可能是城市经纬度没查到)
            return None, "Chart generation skipped (Location data not found)."
            
    except Exception as e:
        # 捕获所有错误，返回 None 和错误信息，防止程序崩溃
        return None, f"Chart Error: {str(e)}"

# --- 4. 界面布局 ---

# 侧边栏
with st.sidebar:
    st.title("💾 ACCESS_PORT")
    st.markdown("---")
    
    # 名字
    name = st.text_input("IDENTITY (Name)", "Neo")
    
    # 日期时间
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1: year = st.number_input("Year", 1950, 2030, 1995, step=1)
    with col2: month = st.number_input("Mon", 1, 12, 1, step=1)
    with col3: day = st.number_input("Day", 1, 31, 1, step=1)
    
    col4, col5 = st.columns(2)
    with col4: hour = st.number_input("Hour", 0, 23, 12, step=1)
    with col5: minute = st.number_input("Min", 0, 59, 0, step=1)
    
    # 地点
    city = st.text_input("CITY (e.g. Beijing, New York)", "Beijing")
    country = st.text_input("COUNTRY CODE (e.g. CN, US, GB)", "CN")
    
    st.markdown("---")
    question = st.text_area("QUERY (Your Question)", "Will I achieve financial freedom?")
    
    # 打赏按钮
    st.markdown("### 🔋 ENERGY_CELL")
    st.markdown(
        """
        <a href="https://ko-fi.com/你的用户名" target="_blank">
            <button style="
                background: #ff00ff; border: none; color: white; width: 100%; padding: 10px; font-weight: bold; cursor: pointer;
            ">
            ⚡ INJECT CREDITS (DONATE)
            </button>
        </a>
        """, 
        unsafe_allow_html=True
    )

# 主界面
st.title("🔮 VOID PROPHET")
st.caption("Quantum Astrology System v2077.2 // Online")

# 启动按钮
if st.button(">> INITIALIZE SEQUENCE <<"):
    if not city:
        st.warning("⚠️ ALERT: Location data missing.")
    else:
        # 进度条
        bar = st.progress(0)
        status = st.empty()
        
        # 第一步：计算星盘
        status.markdown("`Connecting to Satellite...`")
        bar.progress(30)
        time.sleep(0.5)
        
        status.markdown("`Rendering Natal Matrix...`")
        # 调用修复后的函数
        svg_content, result_info = generate_chart_svg(name, year, month, day, hour, minute, city, country)
        
        bar.progress(60)
        
        # 显示星盘或错误信息
        chart_data_for_ai = ""
        if svg_content:
            st.image(svg_content, caption=f"NATAL MATRIX: {name.upper()}", use_column_width=True)
            # 提取简单信息给 AI
            chart_data_for_ai = f"Sun: {result_info.sun['sign']}, Moon: {result_info.moon['sign']}, Asc: {result_info.first_house['sign']}"
        else:
            # 如果出错了 (result_info 是错误信息字符串)
            st.warning(f"⚠️ GRAPHIC RENDER FAIL: {result_info}")
            st.caption("Switching to text-only mode...")
            chart_data_for_ai = f"Birth: {year}-{month}-{day}, {city}"
            
        # 第二步：AI 解读
        status.markdown("`Downloading Prophecy...`")
        bar.progress(80)
        
        st.markdown("---")
        st.subheader("📟 ORACLE TRANSMISSION")
        
        # 结果容器
        res_box = st.empty()
        full_text = ""
        
        # 获取流式回复
        ai_response = get_cyber_interpretation(chart_data_for_ai, question)
        
        # 如果 AI 报错
        if isinstance(ai_response, str): 
            res_box.error(ai_response)
        else:
            # 正常打字机效果
            for chunk in ai_response:
                content = chunk.choices[0].delta.content
                if content:
                    full_text += content
                    res_box.markdown(full_text + " ▌")
            res_box.markdown(full_text)
            
        bar.progress(100)
        status.empty() # 清除状态文字
        
        st.success("✅ TRANSMISSION COMPLETE")
