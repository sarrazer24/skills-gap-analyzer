"""Minimal Viable Product - Simple Skills Gap Analyzer (Single Page)"""
import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

# Load environment variables from .env file (force reload)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Force reload to get latest .env values
except ImportError:
    pass  # python-dotenv not installed, will use environment variables only

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.skill_extractor import SkillExtractor
from src.models.gap_analyzer import SkillGapAnalyzer
from src.data.loader import DataLoader

# Initialize session state
if 'user_skills' not in st.session_state:
    st.session_state.user_skills = []
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None

# Page config
st.set_page_config(
    page_title="Skills Gap Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar and header completely
st.markdown("""
<style>
    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    /* Hide sidebar toggle button */
    button[data-testid="baseButton-header"],
    button[kind="header"] {
        display: none !important;
    }
    
    /* Hide Streamlit header */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Adjust main content to use full width */
    .main .block-container {
        padding-top: 2rem;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)
    
# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Apply custom CSS for purple theme and dark mode
st.markdown("""
<style>
    /* Purple theme variables */
    :root {
        --purple-primary: #9333EA;
        --purple-secondary: #A855F7;
        --purple-light: #E9D5FF;
        --purple-dark: #6B21A8;
        --purple-darker: #581C87;
        --purple-gradient: linear-gradient(135deg, #9333EA 0%, #A855F7 100%);
        --card-shadow: 0 4px 6px -1px rgba(147, 51, 234, 0.1), 0 2px 4px -1px rgba(147, 51, 234, 0.06);
        --card-shadow-hover: 0 10px 15px -3px rgba(147, 51, 234, 0.2), 0 4px 6px -2px rgba(147, 51, 234, 0.1);
    }
    
    /* Card styling */
    .custom-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--card-shadow);
        border: 1px solid #E9D5FF;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        box-shadow: var(--card-shadow-hover);
        transform: translateY(-2px);
    }
    
    [data-theme="dark"] .custom-card,
    .dark-mode-active .custom-card {
        background: #1E1B2E;
        border-color: #6B21A8;
    }
    
    /* Skill badge styling */
    .skill-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: var(--purple-gradient);
        color: white;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
        box-shadow: 0 2px 4px rgba(147, 51, 234, 0.2);
        transition: all 0.2s ease;
    }
    
    .skill-badge:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(147, 51, 234, 0.3);
    }
    
    /* Section containers */
    .section-container {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid #E9D5FF;
        box-shadow: var(--card-shadow);
    }
    
    [data-theme="dark"] .section-container,
    .dark-mode-active .section-container {
        background: linear-gradient(135deg, #1E1B2E 0%, #0F0B1E 100%);
        border-color: #6B21A8;
    }
    
    /* Improved spacing */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Better header styling */
    h1 {
        background: var(--purple-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    
    h2 {
        color: var(--purple-primary);
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E9D5FF;
    }
    
    h3 {
        color: var(--purple-secondary);
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    /* Metric cards enhancement */
    [data-testid="stMetricContainer"] {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--card-shadow);
        border: 1px solid #E9D5FF;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetricContainer"]:hover {
        box-shadow: var(--card-shadow-hover);
        transform: translateY(-2px);
    }
    
    [data-theme="dark"] [data-testid="stMetricContainer"],
    .dark-mode-active [data-testid="stMetricContainer"] {
        background: #1E1B2E;
        border-color: #6B21A8;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #F9FAFB;
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    [data-theme="dark"] .stTabs [data-baseweb="tab-list"],
    .dark-mode-active .stTabs [data-baseweb="tab-list"] {
        background: #1E1B2E;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--purple-gradient);
        color: white;
        font-weight: 600;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 1rem;
        font-weight: 600;
        color: var(--purple-primary);
    }
    
    [data-theme="dark"] .streamlit-expanderHeader,
    .dark-mode-active .streamlit-expanderHeader {
        background: #1E1B2E;
        color: #A855F7;
    }
    
    /* Info boxes */
    .stInfo {
        background: linear-gradient(135deg, #E9D5FF 0%, #F3E8FF 100%);
        border-left: 4px solid var(--purple-primary);
        border-radius: 8px;
        padding: 1rem;
    }
    
    [data-theme="dark"] .stInfo,
    .dark-mode-active .stInfo {
        background: linear-gradient(135deg, #1E1B2E 0%, #2D1B3E 100%);
        border-left-color: #A855F7;
    }
    
    /* Success/Error styling */
    .stSuccess {
        background: linear-gradient(135deg, #D1FAE5 0%, #E6FFED 100%);
        border-left: 4px solid #10B981;
        border-radius: 8px;
    }
    
    .stError {
        background: linear-gradient(135deg, #FEE2E2 0%, #FEF2F2 100%);
        border-left: 4px solid #EF4444;
        border-radius: 8px;
    }
    
    /* Selectbox and input styling */
    .stSelectbox > div > div,
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E9D5FF;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus {
        border-color: var(--purple-primary);
        box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
    }
    
    /* Radio button styling */
    .stRadio > div {
        gap: 1rem;
    }
    
    .stRadio > div > label {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: 2px solid #E9D5FF;
        transition: all 0.3s ease;
        background: white;
    }
    
    .stRadio > div > label:hover {
        border-color: var(--purple-primary);
        background: #F9FAFB;
    }
    
    .stRadio > div > label[data-testid*="selected"] {
        background: var(--purple-gradient);
        color: white;
        border-color: var(--purple-primary);
        font-weight: 600;
    }
    
    /* Progress bar enhancement */
    .stProgress > div > div > div {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: var(--purple-gradient);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Smooth animations */
    * {
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    
    /* Better spacing for sections */
    .element-container {
        margin-bottom: 1.5rem;
    }
    
    /* Caption styling */
    .stCaption {
        color: #6B7280;
        font-size: 0.875rem;
    }
    
    [data-theme="dark"] .stCaption,
    .dark-mode-active .stCaption {
        color: #A855F7;
    }
    
    /* Dark mode styles - ultra comprehensive */
    [data-theme="dark"],
    .dark-mode-active,
    [data-theme="dark"] .stApp,
    .dark-mode-active .stApp,
    .stApp[data-theme="dark"],
    .stApp.dark-mode-active {
        background-color: #0F0B1E !important;
    }
    
    [data-theme="dark"] .main,
    [data-theme="dark"] .block-container,
    .dark-mode-active .main,
    .dark-mode-active .block-container,
    .stApp[data-theme="dark"] .main,
    .stApp[data-theme="dark"] .block-container,
    .stApp.dark-mode-active .main,
    .stApp.dark-mode-active .block-container {
        background-color: #0F0B1E !important;
        color: #F3E8FF !important;
    }
    
    [data-theme="dark"] .stMarkdown,
    [data-theme="dark"] .stMarkdown *,
    [data-theme="dark"] .stMarkdown p,
    [data-theme="dark"] .stMarkdown div,
    .dark-mode-active .stMarkdown,
    .dark-mode-active .stMarkdown *,
    .dark-mode-active .stMarkdown p,
    .dark-mode-active .stMarkdown div,
    .stApp[data-theme="dark"] .stMarkdown,
    .stApp[data-theme="dark"] .stMarkdown *,
    .stApp.dark-mode-active .stMarkdown,
    .stApp.dark-mode-active .stMarkdown * {
        color: #F3E8FF !important;
    }
    
    [data-theme="dark"] .element-container,
    .dark-mode-active .element-container,
    .stApp[data-theme="dark"] .element-container,
    .stApp.dark-mode-active .element-container {
        background-color: #0F0B1E !important;
        color: #F3E8FF !important;
    }
    
    /* Force dark mode on all elements */
    html[data-theme="dark"],
    html.dark-mode-active,
    body[data-theme="dark"],
    body.dark-mode-active {
        background-color: #0F0B1E !important;
    }
    
    /* All text in dark mode */
    [data-theme="dark"] *,
    .dark-mode-active * {
        color: #F3E8FF !important;
    }
    
    /* Exceptions for buttons and specific elements */
    [data-theme="dark"] button,
    .dark-mode-active button,
    [data-theme="dark"] .stButton button,
    .dark-mode-active .stButton button {
        color: white !important;
        background-color: #9333EA !important;
    }
    
    /* Headings in dark mode */
    [data-theme="dark"] h1,
    [data-theme="dark"] h2,
    [data-theme="dark"] h3,
    [data-theme="dark"] h4,
    .dark-mode-active h1,
    .dark-mode-active h2,
    .dark-mode-active h3,
    .dark-mode-active h4 {
        color: #A855F7 !important;
    }
    
    /* Purple accent colors */
    .stButton>button {
        background-color: var(--purple-primary);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: var(--purple-dark);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: var(--purple-primary);
        font-weight: 700;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--purple-primary), var(--purple-secondary));
    }
    
    /* Success/Error badges */
    .stSuccess {
        background-color: var(--purple-light);
        border-left: 4px solid var(--purple-primary);
    }
    
    /* Clean header */
    h1 {
        color: var(--purple-primary);
        font-weight: 700;
    }
    
    /* Dark mode text adjustments */
    [data-theme="dark"] h1,
    [data-theme="dark"] h2,
    [data-theme="dark"] h3,
    [data-theme="dark"] h4,
    .stApp[data-theme="dark"] h1,
    .stApp[data-theme="dark"] h2,
    .stApp[data-theme="dark"] h3,
    .stApp[data-theme="dark"] h4 {
        color: #A855F7 !important;
    }
    
    [data-theme="dark"] .stText,
    [data-theme="dark"] .stCaption,
    [data-theme="dark"] label,
    .stApp[data-theme="dark"] .stText,
    .stApp[data-theme="dark"] .stCaption,
    .stApp[data-theme="dark"] label {
        color: #F3E8FF !important;
    }
    
    [data-theme="dark"] .stSelectbox,
    [data-theme="dark"] .stTextInput,
    [data-theme="dark"] .stTextArea,
    .stApp[data-theme="dark"] .stSelectbox,
    .stApp[data-theme="dark"] .stTextInput,
    .stApp[data-theme="dark"] .stTextArea {
        background-color: #1E1B2E !important;
        color: #F3E8FF !important;
    }
</style>
""", unsafe_allow_html=True)

# Theme toggle in top right corner - using HTML/CSS for better control
theme_col1, theme_col2 = st.columns([1, 0.15])
with theme_col1:
    pass
with theme_col2:
    # Theme toggle button
    theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    theme_label = "Dark" if st.session_state.theme == 'light' else "Light"
    
    if st.button(theme_icon, help=f"Switch to {theme_label} mode", key="theme_toggle", use_container_width=True):
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        st.rerun()

# Apply theme with aggressive JavaScript using components API
import streamlit.components.v1 as components

is_dark = st.session_state.theme == 'dark'
theme_html = f"""
<script>
(function() {{
    const isDark = {str(is_dark).lower()};
    
    function forceApplyTheme() {{
        // Get all root elements
        const app = document.querySelector('.stApp');
        const html = document.documentElement;
        const body = document.body;
        const main = document.querySelector('.main');
        const blockContainer = document.querySelector('.block-container');
        const viewContainer = document.querySelector('[data-testid="stAppViewContainer"]');
        
        const rootElements = [app, html, body, main, blockContainer, viewContainer].filter(Boolean);
        
        if (isDark) {{
            // DARK MODE - Force apply with inline styles
            rootElements.forEach(el => {{
                el.setAttribute('data-theme', 'dark');
                el.classList.add('dark-mode-active');
                if (el === app || el === main || el === blockContainer || el === viewContainer) {{
                    el.style.setProperty('background-color', '#0F0B1E', 'important');
                    el.style.setProperty('color', '#F3E8FF', 'important');
                }}
                if (el === body || el === html) {{
                    el.style.setProperty('background-color', '#0F0B1E', 'important');
                }}
            }});
            
            // Force all text elements
            document.querySelectorAll('p, span, div, label, .stMarkdown, .stText, .element-container, .stCaption').forEach(el => {{
                if (el && !el.closest('button') && !el.closest('.stButton')) {{
                    el.style.setProperty('color', '#F3E8FF', 'important');
                }}
            }});
            
            // Headings
            document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(el => {{
                el.style.setProperty('color', '#A855F7', 'important');
            }});
        }} else {{
            // LIGHT MODE - Remove dark styles
            rootElements.forEach(el => {{
                el.setAttribute('data-theme', 'light');
                el.classList.remove('dark-mode-active');
                el.style.removeProperty('background-color');
                el.style.removeProperty('color');
            }});
        }}
    }}
    
    // Run immediately
    forceApplyTheme();
    
    // Run on multiple events
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', forceApplyTheme);
    }}
    window.addEventListener('load', forceApplyTheme);
    
    // Run with delays
    [10, 50, 100, 200, 500, 1000, 2000].forEach(delay => {{
        setTimeout(forceApplyTheme, delay);
    }});
    
    // Continuous monitoring every 1 second
    setInterval(forceApplyTheme, 1000);
    
    // MutationObserver for dynamic content
    if (window.MutationObserver) {{
        const obs = new MutationObserver(() => setTimeout(forceApplyTheme, 50));
        if (document.body) {{
            obs.observe(document.body, {{ childList: true, subtree: true, attributes: true }});
        }}
    }}
}})();
</script>
"""
components.html(theme_html, height=0, width=0)

# Header with gradient
st.markdown("""
<div style="text-align: center; padding: 3rem 0 2rem 0;">
    <h1 style="background: linear-gradient(135deg, #9333EA 0%, #A855F7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 3.5rem; margin-bottom: 0.5rem; font-weight: 800; letter-spacing: -0.02em;">🎯 Skills Gap Analyzer</h1>
    <p style="color: #6B7280; font-size: 1.2rem; font-weight: 500; margin-top: 0.5rem;">AI-Powered Career Skills Analysis</p>
    <div style="margin: 1.5rem auto; width: 100px; height: 4px; background: linear-gradient(90deg, #9333EA, #A855F7); border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load essential data and extract coherent skills from jobs"""
    loader = DataLoader()
    
    try:
        # Load ALL jobs for job selection (no sample limit)
        jobs_df = loader.load_jobs_data(sample_size=None)  # None = load all
        
        # Extract actual skills from job requirements
        all_job_skills = set()
        if not jobs_df.empty and 'skill_list' in jobs_df.columns:
            for skills in jobs_df['skill_list']:
                if isinstance(skills, list):
                    all_job_skills.update(s.lower().strip() for s in skills if s)
                elif isinstance(skills, str):
                    import ast
                    try:
                        skills_list = ast.literal_eval(skills)
                        if isinstance(skills_list, list):
                            all_job_skills.update(s.lower().strip() for s in skills_list if s)
                    except:
                        # Try comma separation
                        all_job_skills.update(s.lower().strip() for s in skills.split(',') if s.strip())
        
        # Load skills taxonomy for fallback and category info
        skills_df = loader.load_skills_taxonomy()
        
        # Merge: Use skills from jobs (primary) + taxonomy skills (for completeness)
        if not skills_df.empty:
            taxonomy_skills = set(skills_df['skill_group_name'].str.lower().unique())
            # Combine both sets, prioritizing job skills
            all_skills_combined = all_job_skills | taxonomy_skills
        else:
            all_skills_combined = all_job_skills
        
        # Clean and normalize job titles
        if not jobs_df.empty and 'job_title' in jobs_df.columns:
            # Clean job titles
            jobs_df = jobs_df.copy()
            jobs_df['job_title_clean'] = jobs_df['job_title'].str.strip().str.title()
            # Remove duplicates, normalize
            jobs_df['job_title_clean'] = jobs_df['job_title_clean'].str.replace(r'\s+', ' ', regex=True)
        
        return jobs_df, skills_df, sorted(list(all_skills_combined))
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), []

jobs_df, skills_df, available_skills = load_data()

# ====================
# SECTION 1: USER INPUT
# ====================
st.markdown("""
<div class="section-container">
    <h2 style="margin-top: 0; padding-top: 0;">1️⃣ Input Your Profile</h2>
""", unsafe_allow_html=True)

# Create columns for layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📝 Your Skills")
    
    # Method selector
    method = st.radio(
        "How to input skills:",
        ["Select from list", "Upload CV", "Write description"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    user_skills = []
    
    if method == "Select from list":
        if available_skills:
            # Use skills extracted from actual job requirements
            user_skills = st.multiselect(
                "Select your skills (skills shown are from actual job requirements):",
                available_skills,
                placeholder="Start typing to search...",
                label_visibility="visible"
            )
            
            # Show count
            if available_skills:
                st.caption(f"💡 {len(available_skills)} skills available (extracted from job listings)")
        else:
            st.warning("Skills data not loaded. Using sample skills.")
            sample_skills = ["python", "sql", "machine learning", "excel", "tableau", "aws", "docker"]
            user_skills = st.multiselect("Select your skills:", sample_skills)
    
    elif method == "Upload CV":
        # LLM extraction option
        use_llm = st.checkbox(
            "🤖 Use AI-powered extraction (requires OpenAI API key)",
            value=False,
            help="Enable LLM-based extraction for better accuracy. Falls back to pattern matching if API key is not set."
        )
        
        uploaded_file = st.file_uploader("Upload CV (PDF or DOCX)", type=['pdf', 'docx'])
        if uploaded_file:
            with st.spinner("🔍 Analyzing CV and extracting skills..."):
                try:
                    # Use skills from job requirements for better matching
                    if available_skills:
                        extractor_skills = available_skills
                    elif not skills_df.empty:
                        extractor_skills = skills_df['skill_group_name'].unique().tolist()
                    else:
                        extractor_skills = ["python", "sql", "machine learning", "excel", "tableau", "aws"]
                    
                    # Get API key from environment
                    api_key = None
                    if use_llm:
                        try:
                            from dotenv import load_dotenv
                            load_dotenv(override=True)
                        except:
                            pass
                        api_key = os.getenv('OPENAI_API_KEY', '').strip()
                        
                        if not api_key:
                            st.warning("⚠️ No API key found. Set OPENAI_API_KEY in .env file.")
                    
                    extractor = SkillExtractor(extractor_skills, use_llm=use_llm, api_key=api_key)
                    
                    # Extract skills with confidence scores
                    if uploaded_file.name.endswith('.pdf'):
                        text = extractor._read_pdf(uploaded_file)
                        user_skills_with_conf = extractor.extract_from_text(text, return_confidence=True)
                    else:
                        text = extractor._read_docx(uploaded_file)
                        user_skills_with_conf = extractor.extract_from_text(text, return_confidence=True)
                    
                    if user_skills_with_conf:
                        # Separate high and medium confidence skills
                        high_conf_skills = [skill for skill, conf in user_skills_with_conf if conf >= 0.7]
                        medium_conf_skills = [skill for skill, conf in user_skills_with_conf if 0.5 <= conf < 0.7]
                        
                        # Use high confidence skills as primary
                        user_skills = high_conf_skills
                        
                        if user_skills:
                            st.success(f"✅ Extracted {len(user_skills)} skills from your CV")
                            
                            # Show skills in a clean grid
                            cols = st.columns(4)
                            for idx, skill in enumerate(user_skills):
                                with cols[idx % 4]:
                                    st.markdown(f"<div class='skill-badge'>{skill.title()}</div>", unsafe_allow_html=True)
                            
                            if medium_conf_skills:
                                with st.expander(f"➕ {len(medium_conf_skills)} additional skills found"):
                                    cols2 = st.columns(4)
                                    for idx, skill in enumerate(medium_conf_skills[:12]):
                                        with cols2[idx % 4]:
                                            if st.button(f"Add {skill.title()}", key=f"add_{skill}"):
                                                user_skills.append(skill)
                                                st.rerun()
                        else:
                            st.info("💡 No skills found. Try the 'Write description' method.")
                    else:
                        st.info("💡 No skills found. Make sure your CV mentions technical skills explicitly.")
                except ImportError as e:
                    st.error(f"📦 Missing library: {e}")
                    st.info("Please install required libraries: `pip install PyPDF2 python-docx`")
                except Exception as e:
                    st.error(f"❌ Error extracting skills: {e}")
                    st.info("💡 Try the 'Write description' method as an alternative.")
    
    else:  # Write description
        # LLM extraction option
        use_llm = st.checkbox(
            "🤖 Use AI-powered extraction (requires OpenAI API key)",
            value=False,
            help="Enable LLM-based extraction for better accuracy. Falls back to pattern matching if API key is not set.",
            key="use_llm_text"
        )
        
        description = st.text_area(
            "Describe your skills and experience:",
            height=100,
            placeholder="Example: I have 3 years experience with Python and SQL. I've worked on data analysis projects using pandas and matplotlib. Familiar with machine learning concepts and AWS services..."
        )
        if description:
            with st.spinner("🔍 Extracting skills from description..."):
                try:
                    # Use skills from job requirements for better matching
                    if available_skills:
                        extractor_skills = available_skills
                    elif not skills_df.empty:
                        extractor_skills = skills_df['skill_group_name'].unique().tolist()
                    else:
                        extractor_skills = ["python", "sql", "machine learning", "excel", "tableau", "aws"]
                    
                    # Get API key from environment
                    api_key = None
                    if use_llm:
                        # Get from environment
                        try:
                            from dotenv import load_dotenv
                            load_dotenv(override=True)
                        except:
                            pass
                        api_key = os.getenv('OPENAI_API_KEY', '').strip()
                        
                        if not api_key:
                            st.warning("⚠️ No API key found. Set OPENAI_API_KEY environment variable or add it to .env file.")
                    
                    extractor = SkillExtractor(extractor_skills, use_llm=use_llm, api_key=api_key)
                    user_skills_with_conf = extractor.extract_from_text(description, return_confidence=True)
                    
                    if user_skills_with_conf:
                        # Use all skills found (description is usually more explicit)
                        user_skills = [skill for skill, conf in user_skills_with_conf if conf >= 0.4]
                        
                        if user_skills:
                            st.success(f"✅ Found {len(user_skills)} skills from your description")
                            
                            # Show extracted skills
                            with st.expander("📋 Extracted Skills", expanded=True):
                                cols = st.columns(4)
                                for idx, skill in enumerate(user_skills):
                                    conf = next((conf for s, conf in user_skills_with_conf if s == skill), 0)
                                    with cols[idx % 4]:
                                        if conf >= 0.7:
                                            st.success(f"✓ {skill.title()}")
                                        else:
                                            st.info(f"• {skill.title()}")
                        else:
                            st.warning("⚠️ Skills found but with low confidence. Try being more specific.")
                            st.info("💡 Tip: Mention specific technologies, tools, and frameworks explicitly.")
                    else:
                        st.info("💡 No skills detected. Try mentioning specific technologies like 'Python', 'SQL', 'AWS', etc.")
                except Exception as e:
                    st.error(f"❌ Error extracting skills: {e}")
    
    # Save to session state
    if user_skills:
        st.session_state.user_skills = [s.lower().strip() for s in user_skills]

with col2:
    st.markdown("### 🎯 Target Job")
    
    if not jobs_df.empty and 'job_title' in jobs_df.columns:
        # Get job titles, clean and organize them
        if 'job_title_clean' in jobs_df.columns:
            # Use cleaned titles
            job_titles_df = jobs_df[['job_title', 'job_title_clean']].copy()
        else:
            # Clean on the fly
            job_titles_df = jobs_df[['job_title']].copy()
            job_titles_df['job_title_clean'] = job_titles_df['job_title'].str.strip().str.title()
            job_titles_df['job_title_clean'] = job_titles_df['job_title_clean'].str.replace(r'\s+', ' ', regex=True)
        
        # Count frequency of each job title
        title_counts = job_titles_df['job_title_clean'].value_counts()
        
        # Get ALL unique job titles (not just top 150 - load all jobs)
        all_unique_titles = title_counts.index.tolist()
        
        # Sort alphabetically for easier browsing
        all_unique_titles_sorted = sorted(all_unique_titles)
        
        # Show count
        total_jobs = len(jobs_df)
        unique_titles_count = len(all_unique_titles_sorted)
        
        # Optional: Show clustering-based recommendations if user has skills
        recommended_jobs_info = None
        if st.session_state.user_skills:
            try:
                from src.models.cluster_analyzer import ClusterAnalyzer
                
                model_path = 'app/models/clustering_model.pkl'
                if os.path.exists(model_path):
                    cluster_model = ClusterAnalyzer.load(model_path)
                    user_cluster = cluster_model.predict_user_cluster(st.session_state.user_skills)
                    
                    if user_cluster is not None and 'cluster' in jobs_df.columns:
                        # Get jobs from user's cluster and calculate match scores
                        cluster_jobs = jobs_df[jobs_df['cluster'] == user_cluster].copy()
                        
                        if not cluster_jobs.empty:
                            # Calculate match percentage for each job
                            user_set = set(s.lower().strip() for s in st.session_state.user_skills)
                            
                            recommended_jobs_list = []
                            for idx, job_row in cluster_jobs.iterrows():
                                job_skills_raw = job_row.get('skill_list', [])
                                if isinstance(job_skills_raw, str):
                                    import ast
                                    try:
                                        job_skills = ast.literal_eval(job_skills_raw)
                                    except:
                                        job_skills = [s.strip() for s in job_skills_raw.split(',') if s.strip()]
                                else:
                                    job_skills = job_skills_raw if isinstance(job_skills_raw, list) else []
                                
                                job_set = set(s.lower().strip() for s in job_skills)
                                match_pct = (len(user_set & job_set) / len(job_set) * 100) if job_set else 0
                                
                                recommended_jobs_list.append({
                                    'job': job_row,
                                    'match': match_pct,
                                    'title': job_row.get('job_title', 'Unknown')
                                })
                            
                            # Sort by match percentage
                            recommended_jobs_list.sort(key=lambda x: x['match'], reverse=True)
                            recommended_jobs_info = recommended_jobs_list[:5]  # Top 5
            except Exception as e:
                pass  # Silently fail, use all jobs
        
        # Show recommended jobs if available
        if recommended_jobs_info:
            st.markdown(f"""
            <div class="custom-card" style="background: linear-gradient(135deg, #E9D5FF 0%, #F3E8FF 100%); border-left: 4px solid var(--purple-primary);">
                <p style="margin: 0; font-weight: 600; color: var(--purple-primary);">💡 <strong>{len(recommended_jobs_info)} recommended jobs</strong> found based on your skills (using clustering)</p>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View recommended jobs", expanded=False):
                for rec in recommended_jobs_info:
                    st.markdown(f"""
                    <div style="padding: 0.75rem; background: #F9FAFB; border-radius: 8px; margin: 0.5rem 0;">
                        <strong>{rec['title']}</strong> - <span style="color: var(--purple-primary); font-weight: 600;">{rec['match']:.1f}% match</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        selected_job_title = st.selectbox(
            f"Select a target job ({unique_titles_count:,} unique job titles from {total_jobs:,} total jobs):",
            ["-- Select a job --"] + all_unique_titles_sorted,
            help="All available jobs are listed alphabetically. Use search to find specific jobs."
        )
        
        if selected_job_title != "-- Select a job --":
            # Find the job (try cleaned title first, then original)
            job_rows = None
            if 'job_title_clean' in jobs_df.columns:
                job_rows = jobs_df[jobs_df['job_title_clean'] == selected_job_title]
            
            if job_rows is None or job_rows.empty:
                job_rows = jobs_df[jobs_df['job_title'].str.strip().str.title() == selected_job_title]
            
            if job_rows.empty:
                # Last resort: case-insensitive partial match
                job_rows = jobs_df[jobs_df['job_title'].str.strip().str.title().str.contains(selected_job_title, case=False, na=False)]
            
            if not job_rows.empty:
                # If we have recommendations, prefer jobs with higher match
                if recommended_jobs_info and st.session_state.user_skills:
                    # Find recommended job with this title
                    rec_job = next((r for r in recommended_jobs_info if r['title'] == selected_job_title), None)
                    if rec_job:
                        job_data = rec_job['job'].to_dict()
                    else:
                        job_data = job_rows.iloc[0].to_dict()
                else:
                    job_data = job_rows.iloc[0].to_dict()
                
                st.session_state.selected_job = job_data
                
                # Show job info in a card
                st.markdown(f"""
                <div class="custom-card" style="margin-top: 1rem;">
                    <p style="margin: 0.5rem 0;"><strong style="color: var(--purple-primary);">🏢 Company:</strong> {job_data.get('company', 'N/A')}</p>
                    <p style="margin: 0.5rem 0;"><strong style="color: var(--purple-primary);">📍 Location:</strong> {job_data.get('location', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show required skills preview
                job_skills_list = job_data.get('skill_list', [])
                
                # Parse job skills properly
                if isinstance(job_skills_list, list):
                    parsed_skills = [str(s).strip() for s in job_skills_list if s and str(s).strip()]
                elif isinstance(job_skills_list, str):
                    import ast
                    try:
                        parsed = ast.literal_eval(job_skills_list)
                        if isinstance(parsed, list):
                            parsed_skills = [str(s).strip() for s in parsed if s and str(s).strip()]
                        else:
                            parsed_skills = []
                    except:
                        # Try comma separation
                        parsed_skills = [s.strip() for s in job_skills_list.split(',') if s.strip()]
                else:
                    parsed_skills = []
                
                if parsed_skills:
                    st.write(f"**Required Skills:** {len(parsed_skills)} skills")
                    with st.expander("View required skills", expanded=True):
                        cols = st.columns(3)
                        for idx, skill in enumerate(parsed_skills[:12]):
                            with cols[idx % 3]:
                                st.caption(f"• {skill.title()}")
                        if len(parsed_skills) > 12:
                            st.caption(f"... and {len(parsed_skills) - 12} more skills")
    else:
        st.warning("Job data not loaded. Please check data files.")

# ====================
# SECTION 2: GAP ANALYSIS
# ====================
if st.session_state.user_skills and st.session_state.selected_job:
    st.markdown("</div>", unsafe_allow_html=True)  # Close section container
    st.markdown("""
    <div class="section-container">
        <h2 style="margin-top: 0; padding-top: 0;">2️⃣ Your Skill Gap Analysis</h2>
    """, unsafe_allow_html=True)
    
    # Get job skills
    job = st.session_state.selected_job
    job_skills_raw = job.get('skill_list', [])
    
    # Parse job skills
    if isinstance(job_skills_raw, str):
        import ast
        try:
            job_skills = ast.literal_eval(job_skills_raw)
        except:
            job_skills = [s.strip() for s in job_skills_raw.split(',') if s.strip()]
    else:
        job_skills = job_skills_raw if isinstance(job_skills_raw, list) else []
    
    # Normalize skills
    user_set = set(s.lower().strip() for s in st.session_state.user_skills)
    job_set = set(s.lower().strip() for s in job_skills)
    
    # Calculate gap
    matching = user_set & job_set
    missing = job_set - user_set
    extra = user_set - job_set
    
    match_percent = (len(matching) / len(job_set)) * 100 if job_set else 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Match Percentage", f"{match_percent:.1f}%")
    
    with col2:
        st.metric("✅ Matching Skills", f"{len(matching)}/{len(job_set)}")
    
    with col3:
        st.metric("❌ Missing Skills", len(missing))
    
    # Progress bar
    st.progress(match_percent / 100, text=f"Career Readiness: {match_percent:.1f}%")
    
    # Detailed breakdown
    tab1, tab2 = st.tabs(["✅ Your Matching Skills", "❌ Skills You Need"])
    
    with tab1:
        if matching:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(matching)):
                with cols[idx % 4]:
                    st.success(f"✓ {skill.title()}")
        else:
            st.info("No matching skills found.")
    
    with tab2:
        if missing:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(missing)):
                with cols[idx % 4]:
                    st.error(f"✗ {skill.title()}")
        else:
            st.success("🎉 You have all the required skills for this job!")
    
    # ====================
    # SECTION 3: RECOMMENDATIONS
    # ====================
    st.markdown("</div>", unsafe_allow_html=True)  # Close gap analysis container
    st.markdown("""
    <div class="section-container">
        <h2 style="margin-top: 0; padding-top: 0;">3️⃣ Learning Recommendations</h2>
    """, unsafe_allow_html=True)
    
    if missing:
        # Learning path using Association Rules for prioritization
        st.subheader("🎯 Recommended Learning Order (Based on Association Rules A2)")
        
        # Use Association Rules to determine priority and unlock potential
        try:
            from src.models.association_miner import AssociationMiner
            
            model_path = 'app/models/association_rules.pkl'
            skill_priorities = {}
            
            if os.path.exists(model_path):
                miner = AssociationMiner.load(model_path)
                
                # For each missing skill, find how many other skills it unlocks
                for missing_skill in missing:
                    # Get recommendations if user had this skill
                    test_skills = list(user_set) + [missing_skill]
                    recommendations = miner.get_recommendations(test_skills, top_n=20)
                    
                    # Count how many of the recommendations are also in missing skills
                    unlocks_count = 0
                    if not recommendations.empty:
                        recommended_skills = set(r['skill'].lower().strip() for _, r in recommendations.iterrows())
                        unlocks_count = len(recommended_skills & missing)
                    
                    # Calculate priority based on unlocks and confidence
                    if not recommendations.empty:
                        # Get average confidence for this skill
                        skill_recs = recommendations[recommendations['skill'].str.lower().str.strip() == missing_skill.lower().strip()]
                        avg_confidence = skill_recs['confidence'].mean() if not skill_recs.empty else 0.5
                    else:
                        avg_confidence = 0.5
                    
                    # Priority = unlocks * 0.3 + confidence * 0.7
                    priority = (unlocks_count / max(len(missing), 1)) * 0.3 + avg_confidence * 0.7
                    skill_priorities[missing_skill] = {
                        'priority': priority,
                        'unlocks': unlocks_count,
                        'confidence': avg_confidence
                    }
            else:
                # Fallback: use simple priority
                for skill in missing:
                    skill_priorities[skill] = {'priority': 0.5, 'unlocks': 0, 'confidence': 0.5}
        except Exception as e:
            # Fallback: use simple priority
            for skill in missing:
                skill_priorities[skill] = {'priority': 0.5, 'unlocks': 0, 'confidence': 0.5}
        
        # Sort skills by priority
        sorted_skills = sorted(missing, key=lambda s: skill_priorities.get(s, {}).get('priority', 0.5), reverse=True)
        
        # Show learning steps
        for i, skill in enumerate(sorted_skills[:5], 1):
            skill_info = skill_priorities.get(skill, {'priority': 0.5, 'unlocks': 0, 'confidence': 0.5})
            priority = skill_info['priority']
            unlocks = skill_info['unlocks']
            confidence = skill_info['confidence']
            
            priority_label = "High" if priority >= 0.7 else "Medium" if priority >= 0.4 else "Low"
            
            with st.expander(f"{i}. **{skill.title()}** (Priority: {priority_label})", expanded=i==1):
                if unlocks > 0:
                    st.markdown(f"📌 Unlocks **{unlocks}** other related skills")
                else:
                    st.markdown(f"📌 Foundation skill for this role")
                
                st.markdown(f"💡 Association confidence: {confidence*100:.0f}%")
                
                st.write("**Learning Resources:**")
                st.write("- Online courses (Coursera, Udemy, edX)")
                st.write("- Official documentation and tutorials")
                st.write("- Practice projects and exercises")
        
        # Related skills from Association Rules A2
        st.markdown("### 📚 Related Skills (Based on Association Rules A2)")
        
        try:
            from src.models.association_miner import AssociationMiner
            
            model_path = 'app/models/association_rules.pkl'
            if os.path.exists(model_path):
                miner = AssociationMiner.load(model_path)
                recommendations = miner.get_recommendations(st.session_state.user_skills, top_n=5)
                
                if not recommendations.empty:
                    for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
                        skill_name = row['skill'].title()
                        confidence_pct = row.get('confidence', 0) * 100
                        based_on = row.get('based_on', 'your skills')
                        
                        # Format based_on for display
                        if isinstance(based_on, str) and based_on:
                            based_on_skills = [s.strip().title() for s in based_on.split(',')]
                            based_on_display = ' + '.join(based_on_skills[:2])  # Show max 2 skills
                        else:
                            based_on_display = 'your current skills'
                        
                        st.markdown(f"""
                        **{idx}. {skill_name}**
                        
                        💡 {confidence_pct:.0f}% of jobs with {based_on_display} also need {skill_name}
                        
                        *(From Association Rules A2)*
                        """)
                else:
                    if st.session_state.user_skills:
                        st.info("💡 No specific skill recommendations found for your skill combination yet. Try learning complementary skills from the job descriptions below.")
                    else:
                        st.info("💡 Enter your skills above to get personalized skill recommendations based on job market patterns.")
            else:
                st.info("💡 Association rules model not found. Run `python scripts/download_models.py`")
        except Exception as e:
            st.warning(f"Skill recommendations temporarily unavailable: {str(e)}")
        
        # Similar jobs from Clustering (all from same cluster)
        st.markdown("### 💼 Similar Jobs You Might Like (All from same cluster as your selected job)")
        
        try:
            from src.models.cluster_analyzer import ClusterAnalyzer
            
            model_path = 'app/models/clustering_model.pkl'
            if os.path.exists(model_path):
                cluster_model = ClusterAnalyzer.load(model_path)
                
                # Find user's cluster
                user_cluster = cluster_model.predict_user_cluster(st.session_state.user_skills)
                
                if user_cluster is not None:
                    # Get jobs from same cluster (excluding current job)
                    if 'cluster' in jobs_df.columns:
                        cluster_jobs = jobs_df[jobs_df['cluster'] == user_cluster].copy()
                        
                        # Exclude current job
                        current_job_title = job.get('job_title', '')
                        if current_job_title:
                            cluster_jobs = cluster_jobs[cluster_jobs['job_title'] != current_job_title]
                        
                        if not cluster_jobs.empty:
                            # Calculate match for each job and sort
                            similar_jobs_with_match = []
                            for _, job_row in cluster_jobs.iterrows():
                                similar_job_skills = job_row.get('skill_list', [])
                                if isinstance(similar_job_skills, str):
                                    import ast
                                    try:
                                        similar_job_skills = ast.literal_eval(similar_job_skills)
                                    except:
                                        similar_job_skills = [s.strip() for s in similar_job_skills.split(',') if s.strip()]
                                else:
                                    similar_job_skills = similar_job_skills if isinstance(similar_job_skills, list) else []
                                
                                similar_job_set = set(s.lower().strip() for s in similar_job_skills)
                                similar_match = len(user_set & similar_job_set) / len(similar_job_set) * 100 if similar_job_set else 0
                                
                                similar_jobs_with_match.append({
                                    'job': job_row,
                                    'match': similar_match
                                })
                            
                            # Sort by match and take top 3
                            similar_jobs_with_match.sort(key=lambda x: x['match'], reverse=True)
                            
                            for idx, item in enumerate(similar_jobs_with_match[:3], 1):
                                job_row = item['job']
                                match_pct = item['match']
                                
                                company = job_row.get('company', 'N/A')
                                location = job_row.get('location', 'N/A')
                                job_title = job_row.get('job_title', 'Unknown Job')
                                
                                st.markdown(f"""
                                **{idx}. {job_title} - {company}** ({match_pct:.0f}% match)
                                
                                📍 {location}
                                """)
                        else:
                            st.info("No similar jobs found in your cluster.")
                    else:
                        st.info("Job clustering not available in loaded data.")
                else:
                    if st.session_state.user_skills:
                        st.info("💡 Job cluster prediction not available for your skill combination. Upgrade your skills to unlock job recommendations.")
                    else:
                        st.info("💡 Enter your skills above to get personalized job recommendations.")
            else:
                st.info("💡 Clustering model not found. Run `python scripts/download_models.py`")
        except Exception as e:
            st.info(f"Job recommendations unavailable: {str(e)}")
    
    else:
        st.markdown("""
        <div class="custom-card" style="text-align: center; padding: 2rem;">
            <h3 style="color: #10B981; margin: 0;">🎉 Congratulations!</h3>
            <p style="font-size: 1.1rem; margin-top: 0.5rem;">You have all the required skills for this job!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close recommendations container

else:
    st.markdown("""
    <div class="custom-card" style="text-align: center; padding: 2rem;">
        <p style="font-size: 1.1rem; color: #6B7280;">👆 Please input your skills and select a target job to see the analysis.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Built with Machine Learning: Association Rules & Clustering | Skills Gap Analyzer MVP")
