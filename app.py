import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
import prompts
import re

# Load environment variables
load_dotenv()

# Configure Page
st.set_page_config(
    page_title="Turku Auto-Center Valuation",
    page_icon="🚗",
    layout="centered"
)

# Custom CSS for professional look
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #004e92;
        color: white;
        border-radius: 5px;
    }
    .header-text {
        color: #004e92;
        font-family: 'Helvetica Neue', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
col1, col2 = st.columns([1, 4])
with col1:
    st.write("🚗") # Placeholder for logo
with col2:
    st.markdown("<h1 class='header-text'>Turku Auto-Center</h1>", unsafe_allow_html=True)
    st.markdown("### Trade-in Valuation Tool")

# Sidebar for settings
# -----------------------------------------
# 1. SETUP SIDEBAR (Model Selection Always Visible)
# -----------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model Switcher (Keep this!)
    model_name = st.selectbox(
        "Model Engine", 
        [
            "gemini-1.5-flash",       # Fast, Reliable (Demo Safe)
            "gemini-2.0-flash-exp",   # Good Middle Ground
            "gemini-1.5-pro",         # Slower, Smarter
            "gemini-3-pro-preview"    # Bleeding Edge (High Risk of 429)
        ], 
        index=0
    )
    
    # Add a status indicator for the key
    # We'll define 'api_key_input' logic below, but we show status here
    if "GOOGLE_API_KEY" in st.secrets:
        st.caption("🟢 Cloud Key Active")
    elif os.getenv("GOOGLE_API_KEY"):
        st.caption("🟢 Local Key Active")
    else:
        st.warning("🔴 No Key Found")

# -----------------------------------------
# 2. AUTHENTICATION LOGIC (Hidden Process)
# -----------------------------------------
# Initialize variable
api_key_input = None

# Check 1: Streamlit Cloud Secrets (Production)
if "GOOGLE_API_KEY" in st.secrets:
    api_key_input = st.secrets["GOOGLE_API_KEY"]

# Check 2: Local .env file (Development)
elif os.getenv("GOOGLE_API_KEY"):
    api_key_input = os.getenv("GOOGLE_API_KEY")

# Check 3: Fallback - Manual Input (Only show this if 1 & 2 fail)
if not api_key_input:
    with st.sidebar:
        api_key_input = st.text_input("🔑 Enter API Key manually", type="password")

# Main Content
st.info("Take a photo of the car to get an instant valuation from our AI Senior Buyer.")

# Camera Input
img_file_buffer = st.camera_input("Take a picture")

if img_file_buffer is not None:
    if not api_key_input:
        st.error("⚠️ API Key is missing. Please check settings.")
    else:
        # 1. Show the captured image immediately
        image = Image.open(img_file_buffer)
        
        st.divider()
        
        # 2. INPUTS (The "Phase 1" Manual Data Layer)
        st.subheader("Vehicle Details")
        col1, col2 = st.columns(2)
        
        with col1:
            # Manual input for Mileage
            kms_input = st.number_input("Odometer Reading (km)", min_value=0, step=5000, value=150000)
        
        with col2:
            # Manual inputs for specs
            is_diesel = st.checkbox("Diesel Engine?", value=False)
            is_ev = st.checkbox("EV / Hybrid?", value=False)

        # 3. ACTION BUTTON (Triggers the AI)
        if st.button("🚀 Run Turku Valuation", type="primary"):
            
            # Configure API
            genai.configure(api_key=api_key_input)
            
            with st.spinner("Analyzing market data & vehicle condition..."):
                try:
                    # Initialize model
                    model = genai.GenerativeModel(model_name)
                    
                    # Build the Dynamic Prompt
                    fuel_type = "Diesel" if is_diesel else ("EV/Hybrid" if is_ev else "Petrol")
                    
                    # Inject the user's inputs into the prompt
                    final_prompt = f"""
                    {prompts.SYSTEM_INSTRUCTION}
                    
                    [USER INPUT DATA]
                    - Mileage: {kms_input} km
                    - Fuel: {fuel_type}
                    
                    [LOGIC ADJUSTMENTS]
                    - If Mileage > 250,000 km, value is LOW (High Risk).
                    - If Mileage < 100,000 km, value is PREMIUM.
                    - If Diesel, apply "Slow Sell" discount logic.
                    """
                    
                    # Call AI
                    response = model.generate_content([final_prompt, image])
                    
                    # 4. DISPLAY DASHBOARD
                    st.success("Valuation Complete")
                    
                    # Regex to find price range (e.g. €400 - €900)
                    match = re.search(r'€\s?([0-9,.]+)\s?-\s?€\s?([0-9,.]+)', response.text)
                    
                    if match:
                        low_bid = match.group(1)
                        high_bid = match.group(2)
                        
                        # Show the 3-column dashboard
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("📉 Conservative", f"€{low_bid}")
                        with m2:
                            st.metric("📈 Aggressive", f"€{high_bid}")
                        with m3:
                            # Quick 'Retail' math logic
                            try:
                                clean_high = float(high_bid.replace(',', '').replace('.', ''))
                                st.metric("🏷️ Est. Retail", f"~€{int(clean_high * 1.3)}")
                            except:
                                st.metric("🏷️ Est. Retail", "N/A")
                    
                    st.markdown("---")
                    st.markdown("### 📝 Manager's Report")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")