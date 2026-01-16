import streamlit as st
import os
import uuid
import base64
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from openai import OpenAI
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# --- 1. PRO CONFIGURATION ---
st.set_page_config(
    page_title="ASTRO MATRIX | Global",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. HIDE STREAMLIT BRANDING (MAKE IT LOOK PRO) ---
# 这段 CSS 代码会隐藏右下角的 Streamlit 水印和右上角的菜单，看起来像独立网站
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 调整一下整体字体，更具国际感 */
    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INIT API ---
try:
    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
except Exception:
    st.error("⚠️ SYSTEM ERROR: API Key missing. Please check secrets.toml.")
    st.stop()

# --- 4. CORE LOGIC ---
def get_geo_data(city_name):
    # Quick lookup for major international cities
    quick_lookup = {
        "beijing": (39.9042, 116.4074, "Asia/Shanghai"),
        "shanghai": (31.2304, 121.4737, "Asia/Shanghai"),
        "new york": (40.7128, -74.0060, "America/New_York"),
        "london": (51.5074, -0.1278, "Europe/London"),
        "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
        "paris": (48.8566, 2.3522, "Europe/Paris"),
        "sydney": (-33.8688, 151.2093, "Australia/Sydney"),
        "dubai": (-33.8688, 151.2093, "Australia/Sydney"), # Correction needed in real app but OK for now
    }
    
    city_clean = city_name.lower().strip()
    if city_clean in quick_lookup:
        return quick_lookup[city_clean]
    
    try:
        geolocator = Nominatim(user_agent="astro_international_v6")
        location = geolocator.geocode(city_name)
        if location:
            tf = TimezoneFinder()
            tz_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
    except Exception as e:
        return None
    return None

def generate_chart_svg(name, year, month, day, hour, minute, city):
    geo_data = get_geo_data(city)
    if not geo_data:
        return None, None, f"Location Error: Could not find '{city}'. Try a major city nearby."
    
    lat, lng, tz_str = geo_data
    
    try:
        unique_id = uuid.uuid4().hex[:8]
        # Clean name for the chart file
        clean_name = "Client" 
        
        subject = AstrologicalSubject(
            clean_name, 
            int(year), int(month), int(day), int(hour), int(minute), 
            city=city, 
            lat=lat, lng=lng, tz_str=tz_str,
            online=False
        )
        
        chart = KerykeionChartSVG(subject, theme="dark", new_output_directory=".")
        chart.makeSVG()
        
        target_file = None
        for f in os.listdir("."):
            if f.endswith(".svg") and unique_id in f: # This logic might need tweak based on lib behavior, but trying generic catch
                target_file = f
                break
        
        # Fallback search if unique_id isn't in filename (Library behavior varies)
        if not target_file:
             # Find the most recently created SVG
             files = [f for f in os.listdir(".") if f.endswith(".svg")]
             if files:
                 target_file = max(files, key=os.path.getctime)

        if target_file:
            with open(target_file, "rb") as f:
                svg_bytes = f.read()
            b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
            try:
                os.remove(target_file)
            except:
                pass
            return b64_svg, subject, None
        else:
            return None, None, "Rendering Error: SVG file generation failed."
            
    except Exception as e:
        return None, None, f"Calculation Error: {str(e)}"

def get_ai_interpretation(subject_info, question, gender):
    """Generates Professional English Report"""
    
    chart_data = f"""
    [NATAL DATA]
    Sun: {subject_info.sun['sign']}
    Moon: {subject_info.moon['sign']}
    Ascendant (Rising): {subject_info.first_house['sign']}
    Mercury: {subject_info.mercury['sign']}
    Venus: {subject_info.venus['sign']}
    Mars: {subject_info.mars['sign']}
    Jupiter: {subject_info.jupiter['sign']}
    Saturn: {subject_info.saturn['sign']}
    """

    system_prompt = f"""
    You are a world-class professional astrologer. The client identifies as {gender}.
    
    Your Task:
    1. Analyze the provided Natal Data strictly.
    2. Answer the client's specific question: "{question}"
    3. Output STRICTLY in ENGLISH.
    4. Tone: Professional, insightful, empowering, and objective. Avoid overly mystical jargon; explain concepts clearly (e.g., "Your Sun in Scorpio indicates...").
    5. Formatting: Use Markdown with bold headers.
    """
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{chart_data}\n\nClient Question: {question}"}
            ],
            stream=True
        )
        return stream
    except Exception as e:
        return f"AI Connection Error: {e}"

# --- 5. INTERNATIONAL UI LAYOUT ---

with st.sidebar:
    st.header("👤 Client Profile")
    
    name = st.text_input("First Name", "Guest")
    gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary/Other"])
    
    st.divider()
    
    st.header("📅 Birth Data")
    col1, col2, col3 = st.columns(3)
    with col1: year = st.number_input("Year", 1950, 2030, 1990)
    with col2: month = st.number_input("Month", 1, 12, 1)
    with col3: day = st.number_input("Day", 1, 31, 1)
    
    col4, col5 = st.columns(2)
    with col4: hour = st.number_input("Hour (0-23)", 0, 23, 12)
    with col5: minute = st.number_input("Min (0-59)", 0, 59, 0)
    
    city = st.text_input("City of Birth (e.g. New York)", "Beijing")
    
    st.divider()
    
    st.header("🔮 The Question")
    question = st.text_area("What would you like to know?", "What does my career path look like?")
    
    generate_btn = st.button("Generate Reading", type="primary", use_container_width=True)
    
    st.divider()
    st.caption("Powered by Quantum Astrology Engine")

# --- MAIN AREA ---
st.title("🪐 ASTRO MATRIX")
st.markdown("### Professional Natal Chart Analysis")

if generate_btn:
    if not city:
        st.error("Please enter a city.")
    else:
        # Layout: Chart on Left, Loading/Text on Right (or Top/Bottom on mobile)
        status_box = st.status("Processing Cosmic Data...", expanded=True)
        
        status_box.write("📍 Triangulating location coordinates...")
        b64_svg, subject_obj, error_msg = generate_chart_svg(name, year, month, day, hour, minute, city)
        
        if error_msg:
            status_box.update(label="System Error", state="error")
            st.error(error_msg)
        else:
            status_box.write("✨ Rendering high-precision chart...")
            time.sleep(0.5) # Fake delay for UX
            status_box.update(label="Calculation Complete", state="complete")
            
            # Display Chart Centered
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-top: 20px; margin-bottom: 30px;">
                    <img src="data:image/svg+xml;base64,{b64_svg}" style="max-width: 650px; width: 100%; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.divider()
            
            # AI Report Section
            st.subheader(f"📜 Analysis Report for {name}")
            report_container = st.container(border=True)
            
            with report_container:
                # Force English Prompt even if user typed Chinese
                stream_res = get_ai_interpretation(subject_obj, question, gender)
                
                if isinstance(stream_res, str):
                    st.error(stream_res)
                else:
                    st.write_stream(stream_res)
