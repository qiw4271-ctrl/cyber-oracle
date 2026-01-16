import streamlit as st
import os
import time
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from openai import OpenAI
from streamlit_extras.stylable_container import stylable_container

# --- 1. 配置页面与赛博风格 CSS ---
st.set_page_config(
    page_title="VOID PROPHET | Cyber Oracle",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 注入自定义 CSS (霓虹赛博风)
st.markdown("""
<style>
    /* 全局背景变黑 */
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
        font-family: 'Courier New', Courier, monospace;
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #0b0d10;
        border-right: 1px solid #333;
    }
    /* 按钮样式：霓虹边框 */
    .stButton>button {
        color: #00ff41;
        background-color: transparent;
        border: 1px solid #00ff41;
        border-radius: 0px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00ff41;
        color: #000;
        box-shadow: 0 0 10px #00ff41;
    }
    /* 输入框样式 */
    .stTextInput>div>div>input {
        background-color: #1c1f26;
        color: #00ff41;
        border: 1px solid #333;
    }
    /* 标题特效 */
    h1 {
        text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41;
    }
    /* 链接颜色 */
    a { color: #ff00ff !important; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 API (从 Streamlit Secrets 获取) ---
# 无论你是用 OpenAI 还是公益 API，这里都兼容
try:
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
except Exception:
    st.error("⚠️ SYSTEM ERROR: API Key missing. Please configure secrets.")
    st.stop()

# --- 3. 核心功能函数 ---

def get_cyber_interpretation(user_data, question):
    """调用 AI 进行赛博风格解盘"""
    system_prompt = """
    You are the "Void Prophet" (Cyber Oracle) from the year 2077.
    Analyze the user's natal chart data and their question.
    
    Style Guidelines:
    1. Tone: Cold, philosophical, tech-noir, mysterious.
    2. Terminology: Translate astrological terms into cyberpunk metaphors (e.g., "Saturn" -> "System Firewall", "Retrograde" -> "Data Glitch", "Ascendant" -> "Interface Persona").
    3. Structure: 
       - [SIGNAL RECEIVED]: Acknowledge the user.
       - [CORE DUMP]: Analyze Sun/Moon/Rising briefly.
       - [PREDICTION ALGORITHM]: Answer the specific question.
       - [ACTION PROTOCOL]: One actionable advice.
    
    Output Language: English (for international users).
    Keep it concise but impactful.
    """
    
    user_prompt = f"""
    Target Subject Data: {user_data}
    Target Query: {question}
    """
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo", # 或者你的公益API支持的模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )
        return stream
    except Exception as e:
        return f"Error: Connection to the Void lost. {e}"

def generate_chart_svg(name, year, month, day, hour, minute, city, country="US"):
    """生成专业 SVG 星盘"""
    try:
        # Kerykeion 不需要联网查经纬度，自带数据库，速度极快
        subject = AstrologicalSubject(name, year, month, day, hour, minute, city=city, nation=country)
        chart = KerykeionChartSVG(subject, theme="dark") # 黑色主题
        # Kerykeion 生成的是 SVG 文件，我们读取它
        chart.makeSVG()
        # 读取生成的 SVG 内容
        # 注意：kerykeion 默认会在当前目录生成文件，我们读完需要清理或直接展示
        # 这里为了演示简单，直接返回对象里的 svg 字符串如果库支持，或者读取文件
        # 由于 kerykeion 的 makeSVG 会写文件，我们假设它写在临时目录
        svg_filename = f"{subject.name}_Chart.svg"
        if os.path.exists(svg_filename):
            with open(svg_filename, "r") as f:
                svg_content = f.read()
            # 稍微魔改一下 SVG 颜色以适应赛博风 (可选)
            return svg_content, subject
    except Exception as e:
        return None, f"Chart generation failed: {e}"

# --- 4. 界面布局 ---

# 侧边栏：输入区
with st.sidebar:
    st.title("💾 INPUT_DATA")
    st.markdown("---")
    name = st.text_input("CODENAME (Name)", "Traveler")
    
    col1, col2, col3 = st.columns(3)
    with col1: year = st.number_input("YYYY", 1950, 2030, 2000)
    with col2: month = st.number_input("MM", 1, 12, 1)
    with col3: day = st.number_input("DD", 1, 31, 1)
    
    col4, col5 = st.columns(2)
    with col4: hour = st.number_input("HR (0-23)", 0, 23, 12)
    with col5: minute = st.number_input("MIN", 0, 59, 0)
    
    city = st.text_input("LOCATION (City)", "London")
    country = st.text_input("REGION (Country Code)", "GB")
    
    st.markdown("---")
    question = st.text_area("QUERY DATABASE (Your Question)", "What is my purpose?")
    
    # 能量交换按钮 (Ko-fi)
    st.markdown("### 🔋 ENERGY_CELL")
    st.markdown(
        """
        <a href="https://ko-fi.com/你的用户名" target="_blank">
            <button style="
                width: 100%;
                background-color: #ff00ff;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
                cursor: pointer;
                text-transform: uppercase;
            ">
            ⚡ Inject Credits (Donate)
            </button>
        </a>
        """, 
        unsafe_allow_html=True
    )

# 主窗口：显示区
st.title("🔮 VOID PROPHET")
st.caption("Quantum Astrology System v2077.1 // Online")

if st.button(">> INITIALIZE SEQUENCE <<"):
    if not city or not question:
        st.warning("⚠️ DATA MISSING: Input required.")
    else:
        # 1. 进度条特效
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Parsing spacetime coordinates...")
        progress_bar.progress(25)
        time.sleep(0.5)
        
        # 2. 生成星盘
        status_text.text("Rendering Natal Matrix...")
        svg_content, subject_info = generate_chart_svg(name, year, month, day, hour, minute, city, country)
        progress_bar.progress(60)
        
        if svg_content:
            # 展示星盘 (SVG渲染)
            st.image(svg_content, caption=f"NATAL MATRIX: {name}", use_column_width=True)
            # 提取简要占星数据给 AI
            astrology_data = f"""
            Sun: {subject_info.sun['sign']}
            Moon: {subject_info.moon['sign']}
            Ascendant: {subject_info.first_house['sign']}
            """
        else:
            st.error("Chart rendering failed. Continuing with text analysis.")
            astrology_data = f"Date: {year}-{month}-{day}, City: {city}"
            
        # 3. AI 解读
        status_text.text("Establishing Quantum Link...")
        progress_bar.progress(90)
        
        st.markdown("---")
        st.subheader("📟 ORACLE TRANSMISSION")
        
        # 流式输出框
        response_container = st.empty()
        full_response = ""
        
        ai_stream = get_cyber_interpretation(astrology_data, question)
        
        # 模拟打字机效果
        for chunk in ai_stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                response_container.markdown(full_response + " ▌") # 光标特效
        
        response_container.markdown(full_response) # 结束时移除光标
        
        progress_bar.progress(100)
        status_text.text("COMPLETED.")
        
        # 4. 结尾再次暗示打赏
        st.info("💡 Insight received? Recharge the Void to keep the oracle online.")

else:
    # 待机画面
    st.markdown("""
    > "The stars are not silent; they are merely encrypted."
    
    Awaiting User Input on Sidebar...
    """)
