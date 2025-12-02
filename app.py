
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
    page_title="Auton Arviointi / Car Evaluation App",
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

# ---------------------------------------------------------
# TRANSLATION DICTIONARY
# ---------------------------------------------------------
translations = {
    'Suomi': {
        'title': 'Auton Arviointi',
        'subtitle': 'Vaihtoauton Arviointityökalu',
        'settings': '⚙️ Asetukset',
        'api_status_ok': '🟢 API-avain: Yhdistetty',
        'api_status_error': '🔴 Yhteys puuttuu',
        'enter_api_key': 'Syötä Google API-avain',
        'ai_engine': 'Tekoälymalli',
        'info_text': 'Ota kuva autosta saadaksesi välittömän hinta-arvion tekoälyltä.',
        'camera_label': 'Ota kuva',
        'api_missing_error': '⚠️ API-avain puuttuu. Tarkista asetukset.',
        'vehicle_details': 'Ajoneuvon Tiedot',
        'odometer': 'Mittarilukema (km)',
        'diesel': 'Diesel-moottori?',
        'ev': 'Sähkö / Hybridi?',
        'run_button': '🚀 Suorita Arviointi',
        'analyzing': 'Analysoidaan markkinatietoja ja ajoneuvon kuntoa...',
        'valuation_complete': 'Arviointi Valmis',
        'conservative': '📉 Varovainen',
        'aggressive': '📈 Aggressiivinen',
        'retail': '🏷️ Arvioitu Myyntihinta',
        'managers_report': '📝 Arvioijan Raportti',
        'ai_error': 'Tekoälyvirhe: {}',
        'prompt_instruction': 'Vastaa suomeksi. Käytä ammattimaista autokaupan sanastoa (esim. Hyvityshinta, Jälleenmyyntiarvo, Katsastus).',
        'analysis_mode_label': 'Analyysitila',
        'mode_quick': '⚡ Nopea Arvio',
        'mode_deep': '🧐 Syvällinen Asiantuntija-analyysi',
        'spinner_quick': 'Skannataan visuaalista dataa...',
        'spinner_deep': 'Konsultoidaan asiantuntijaa & analysoidaan markkinatilannetta...',
    },
    'English': {
        'title': 'Car Evaluation App',
        'subtitle': 'Trade-in Valuation Tool',
        'settings': '⚙️ Settings',
        'api_status_ok': '🟢 API Key System: Online',
        'api_status_error': '🔴 Connection Missing',
        'enter_api_key': 'Enter Google API Key',
        'ai_engine': 'AI Engine',
        'info_text': 'Take a photo of the car to get an instant valuation from our AI Senior Buyer.',
        'camera_label': 'Take a picture',
        'api_missing_error': '⚠️ API Key is missing. Please check settings.',
        'vehicle_details': 'Vehicle Details',
        'odometer': 'Odometer Reading (km)',
        'diesel': 'Diesel Engine?',
        'ev': 'EV / Hybrid?',
        'run_button': '🚀 Run Valuation',
        'analyzing': 'Analyzing market data & vehicle condition...',
        'valuation_complete': 'Valuation Complete',
        'conservative': '📉 Conservative',
        'aggressive': '📈 Aggressive',
        'retail': '🏷️ Est. Retail',
        'managers_report': '📝 Manager\'s Report',
        'ai_error': 'AI Error: {}',
        'prompt_instruction': 'Answer in English. Use professional automotive terminology.',
        'analysis_mode_label': 'Analysis Mode',
        'mode_quick': '⚡ Quick Estimate',
        'mode_deep': '🧐 Deep Expert Analysis',
        'spinner_quick': 'Scanning visual data...',
        'spinner_deep': 'Consulting Senior Specialist & Analyzing market nuances...',
    }
}

# ---------------------------------------------------------
# SIDEBAR & LANGUAGE SELECTION
# ---------------------------------------------------------
with st.sidebar:
    # Language Selector (Default: Suomi)
    language = st.radio("Kieli / Language", ['Suomi', 'English'], index=0)
    t = translations[language]

    st.header(t['settings'])
    
    # 1. AUTHENTICATION
    api_key_input = None
    if os.getenv("GOOGLE_API_KEY"):
        api_key_input = os.getenv("GOOGLE_API_KEY")
    if not api_key_input:
        try:
            if "GOOGLE_API_KEY" in st.secrets:
                api_key_input = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass

    # VISUAL STATUS
    if api_key_input:
        st.caption(t['api_status_ok'])
    else:
        st.warning(t['api_status_error'])
        api_key_input = st.text_input(t['enter_api_key'], type="password")
    
    st.divider()
    
    # MODEL SELECTOR (Segmented Control)
    st.caption(t['analysis_mode_label'])
    mode_options = [t['mode_quick'], t['mode_deep']]
    selected_mode = st.segmented_control(
        t['analysis_mode_label'],
        mode_options,
        default=mode_options[0],
        label_visibility="collapsed"
    )
    
    # Fallback to default if None (though default is set)
    if not selected_mode:
        selected_mode = mode_options[0]

    # Map Selection to Backend Logic
    if selected_mode == t['mode_quick']:
        model_name = "gemini-2.0-flash-exp"
        spinner_text = t['spinner_quick']
    else:
        model_name = "gemini-3-pro-preview"
        spinner_text = t['spinner_deep']

# ---------------------------------------------------------
# MAIN UI
# ---------------------------------------------------------

# Header
col1, col2 = st.columns([1, 4])
with col1:
    st.write("🚗") # Placeholder for logo
with col2:
    st.markdown(f"<h1 class='header-text'>{t['title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"### {t['subtitle']}")

# Main Content
st.info(t['info_text'])

# Camera Input
img_file_buffer = st.camera_input(t['camera_label'])

if img_file_buffer is not None:
    if not api_key_input:
        st.error(t['api_missing_error'])
    else:
        # 1. Show the captured image immediately
        image = Image.open(img_file_buffer)
        
        st.divider()
        
        # 2. INPUTS
        st.subheader(t['vehicle_details'])
        col1, col2 = st.columns(2)
        
        with col1:
            # Manual input for Mileage
            kms_input = st.number_input(t['odometer'], min_value=0, step=5000, value=150000)
        
        with col2:
            # Manual inputs for specs
            is_diesel = st.checkbox(t['diesel'], value=False)
            is_ev = st.checkbox(t['ev'], value=False)

        # 3. ACTION BUTTON (Triggers the AI)
        if st.button(t['run_button'], type="primary"):
            
            # Configure API
            genai.configure(api_key=api_key_input)
            
            with st.spinner(spinner_text):
                try:
                    # Initialize model
                    model = genai.GenerativeModel(model_name)
                    
                    # Build the Dynamic Prompt
                    fuel_type = "Diesel" if is_diesel else ("EV/Hybrid" if is_ev else "Petrol")
                    
                    # Inject the user's inputs into the prompt
                    final_prompt = f"""
                    {prompts.SYSTEM_INSTRUCTION}
                    
                    [LANGUAGE INSTRUCTION]
                    {t['prompt_instruction']}

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
                    st.success(t['valuation_complete'])
                    
                    # Regex to find price range (e.g. €400 - €900)
                    match = re.search(r'€\s?([0-9,.]+)\s?-\s?€\s?([0-9,.]+)', response.text)
                    
                    if match:
                        low_bid = match.group(1)
                        high_bid = match.group(2)
                        
                        # Show the 3-column dashboard
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric(t['conservative'], f"€{low_bid}")
                        with m2:
                            st.metric(t['aggressive'], f"€{high_bid}")
                        with m3:
                            # Quick 'Retail' math logic
                            try:
                                clean_high = float(high_bid.replace(',', '').replace('.', ''))
                                st.metric(t['retail'], f"~€{int(clean_high * 1.3)}")
                            except:
                                st.metric(t['retail'], "N/A")
                    
                    st.markdown("---")
                    st.markdown(f"### {t['managers_report']}")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(t['ai_error'].format(e))
