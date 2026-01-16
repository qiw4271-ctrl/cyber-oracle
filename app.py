import streamlit as st
import os
import uuid
import base64
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. 基础页面配置 (无花哨样式) ---
st.set_page_config(
    page_title="星盘解读系统 V5.0",
    page_icon="🌟",
    layout="wide"  # 使用宽屏模式，看图更清楚
)

# --- 2. 初始化 API ---
try:
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
except Exception:
    st.error("⚠️ 错误: 也就是 API Key 没配置好。请检查 .streamlit/secrets.toml 文件。")
    st.stop()

# --- 3. 核心功能函数 ---

def get_geo_data(city_name):
    """获取城市的经纬度和时区"""
    # 常用城市快速查找（为了速度）
    quick_lookup = {
        "beijing": (39.9042, 116.4074, "Asia/Shanghai"),
        "北京": (39.9042, 116.4074, "Asia/Shanghai"),
        "shanghai": (31.2304, 121.4737, "Asia/Shanghai"),
        "上海": (31.2304, 121.4737, "Asia/Shanghai"),
        "guangzhou": (23.1291, 113.2644, "Asia/Shanghai"),
        "广州": (23.1291, 113.2644, "Asia/Shanghai"),
        "shenzhen": (22.5431, 114.0579, "Asia/Shanghai"),
        "深圳": (22.5431, 114.0579, "Asia/Shanghai"),
    }
    
    city_clean = city_name.lower().strip()
    if city_clean in quick_lookup:
        return quick_lookup[city_clean]
    
    # 在线查询
    try:
        geolocator = Nominatim(user_agent="astrology_app_v5")
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
    """
    生成星盘 SVG 并转换为 Base64 编码供 HTML 显示。
    这是目前最稳定、绝对不会显示乱码的方法。
    """
    
    geo_data = get_geo_data(city)
    if not geo_data:
        return None, None, f"找不到城市 '{city}'，请尝试用拼音 (如 Beijing)。"
    
    lat, lng, tz_str = geo_data
    
    try:
        # 生成唯一ID防止文件冲突
        unique_id = uuid.uuid4().hex[:8]
        clean_name = f"User_{unique_id}"
        
        subject = AstrologicalSubject(
            clean_name, 
            int(year), int(month), int(day), int(hour), int(minute), 
            city=city, 
            lat=lat, lng=lng, tz_str=tz_str,
            online=False
        )
        
        # 这里的参数 new_output_directory="." 是必须的
        chart = KerykeionChartSVG(subject, theme="dark", new_output_directory=".")
        chart.makeSVG()
        
        # 寻找生成的文件
        target_file = None
        for f in os.listdir("."):
            if f.endswith(".svg") and unique_id in f:
                target_file = f
                break
        
        if target_file:
            # 读取文件内容
            with open(target_file, "rb") as f:
                svg_bytes = f.read()
            
            # 转换为 Base64 字符串
            b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
            
            # 删除临时文件保持清洁
            try:
                os.remove(target_file)
            except:
                pass
                
            return b64_svg, subject, None
        else:
            return None, None, "SVG文件生成失败，未找到文件。"
            
    except Exception as e:
        return None, None, f"排盘计算错误: {str(e)}"

def get_ai_interpretation(subject_info, question, gender):
    """GPT 解读"""
    
    chart_data = f"""
    【星盘数据】
    太阳: {subject_info.sun['sign']}
    月亮: {subject_info.moon['sign']}
    上升: {subject_info.first_house['sign']}
    水星: {subject_info.mercury['sign']}
    金星: {subject_info.venus['sign']}
    火星: {subject_info.mars['sign']}
    木星: {subject_info.jupiter['sign']}
    土星: {subject_info.saturn['sign']}
    """

    system_prompt = f"""
    你是一位专业的现代占星师。用户是{gender}性。
    请根据用户的星盘数据，用通俗易懂、温暖但专业的口吻回答用户的问题。
    不要使用过于晦涩的术语，解释清楚这些配置对用户生活的影响。
    重点分析：太阳、月亮、上升星座，以及与问题相关的行星。
    """
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{chart_data}\n\n用户问题: {question}"}
            ],
            stream=True
        )
        return stream
    except Exception as e:
        return f"AI 连接错误: {e}"

# --- 4. 界面布局 ---

# 侧边栏：输入区域
with st.sidebar:
    st.header("1. 输入资料")
    
    name = st.text_input("昵称", "访客")
    gender = st.selectbox("性别", ["男", "女", "其他/保密"])
    
    st.subheader("出生日期")
    col1, col2, col3 = st.columns(3)
    with col1: year = st.number_input("年", 1950, 2030, 1990)
    with col2: month = st.number_input("月", 1, 12, 1)
    with col3: day = st.number_input("日", 1, 31, 1)
    
    st.subheader("出生时间")
    col4, col5 = st.columns(2)
    with col4: hour = st.number_input("时 (0-23)", 0, 23, 12)
    with col5: minute = st.number_input("分 (0-59)", 0, 59, 0)
    
    city = st.text_input("出生城市 (建议拼音，如 Beijing)", "Beijing")
    
    st.markdown("---")
    st.header("2. 你想问什么？")
    question = st.text_area("问题描述", "我的事业运势如何？")
    
    start_btn = st.button("✨ 开始排盘解读", type="primary", use_container_width=True)
    
    st.markdown("---")
    # 真正的链接按钮
    st.link_button("☕ 请我喝咖啡 (Buy me a coffee)", "https://www.buymeacoffee.com/") 

# 主界面：显示区域
st.title("🌟 AI 智能星盘解读")

if start_btn:
    if not city:
        st.warning("⚠️ 请输入出生城市")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        # 1. 计算星盘
        status_text.text("正在计算星体坐标...")
        progress_bar.progress(30)
        
        b64_svg, subject_obj, error_msg = generate_chart_svg(name, year, month, day, hour, minute, city)
        
        if error_msg:
            status_text.text("出错了")
            progress_bar.empty()
            st.error(error_msg)
        else:
            # 2. 显示图片
            status_text.text("正在绘制星盘...")
            progress_bar.progress(60)
            
            # 使用 HTML <img> 标签直接嵌入 Base64 图片，这是最稳的方法
            # 居中显示，宽度限制为 600px 防止太大
            html_code = f"""
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/svg+xml;base64,{b64_svg}" style="max-width: 600px; width: 100%; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            </div>
            """
            st.markdown(html_code, unsafe_allow_html=True)
            
            # 3. AI 解读
            status_text.text("AI 正在思考你的问题...")
            progress_bar.progress(80)
            
            st.subheader(f"🔮 {name} 的解读报告")
            response_container = st.container(border=True) # 给文字加个框，好看点
            
            with response_container:
                stream_res = get_ai_interpretation(subject_obj, question, gender)
                
                if isinstance(stream_res, str):
                    st.error(stream_res)
                else:
                    st.write_stream(stream_res)
            
            progress_bar.progress(100)
            status_text.empty() # 清空状态文字
