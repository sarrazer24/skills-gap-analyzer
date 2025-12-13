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

# DEBUG: Check which API key is loaded
_api_key_env = os.getenv("OPEN_API_KEY") or os.getenv("OPENAI_API_KEY")
if _api_key_env:
    print(f"[DEBUG] API Key loaded: ...{_api_key_env[-20:]}")
else:
    print("[DEBUG] WARNING: No API key found in environment!")

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.skill_extractor import SkillExtractor
from src.models.gap_analyzer import SkillGapAnalyzer
from src.data.loader import DataLoader
from src.utils.cluster_analyzer import ClusterAnalyzer
from src.utils.secrets import get_openai_api_key


def locate_model_file(candidates):
    """Return the first existing path from candidates or None.

    Candidates may be relative paths; we try them as given and relative to
    the project root (parent of this file).
    """
    project_root = Path(__file__).parent.parent
    for p in candidates:
        try:
            ppath = Path(p)
            if ppath.exists():
                return str(ppath)
            alt = project_root.joinpath(p)
            if alt.exists():
                return str(alt)
        except Exception:
            continue
    return None


# Helper: map known course/platform names to useful URLs (best-effort)
import urllib.parse

COURSE_LINK_MAP = {
    'coursera': 'https://www.coursera.org/search?query=',
    'udemy': 'https://www.udemy.com/courses/search/?q=',
    'codecademy': 'https://www.codecademy.com/search?query=',
    'khan academy': 'https://www.khanacademy.org/search?page_search_query=',
    'w3schools': 'https://www.w3schools.com/',
    'kaggle': 'https://www.kaggle.com/learn/search?q=',
    'real python': 'https://realpython.com/search?q=',
    'pluralsight': 'https://www.pluralsight.com/search?q=',
    'fast.ai': 'https://www.fast.ai/search?q=',
    'a cloud guru': 'https://acloudguru.com/search?q=',
    'aws training': 'https://www.aws.training/Search?searchTerm=',
    'docker': 'https://www.docker.com/search?q=',
}


def make_course_link(name: str) -> str:
    """Return HTML anchor for a course name. Falls back to a Google search link."""
    if not name or not isinstance(name, str):
        return ''
    lower = name.lower()
    # If user provided explicit URL in parentheses, return it
    # e.g., 'Coursera: Python (https://...)' -> extract URL
    if '(' in name and ')' in name and name.strip().endswith(')'):
        try:
            url = name[name.rfind('(') + 1: -1]
            if url.startswith('http'):
                return f'<a href="{url}" target="_blank" rel="noopener">{name}</a>'
        except Exception:
            pass

    for key, base in COURSE_LINK_MAP.items():
        if key in lower:
            query = urllib.parse.quote_plus(name)
            return f'<a href="{base}{query}" target="_blank" rel="noopener">{name}</a>'

    # Generic fallback: Google search
    q = urllib.parse.quote_plus(name)
    return f'<a href="https://www.google.com/search?q={q}" target="_blank" rel="noopener">{name}</a>'

# Initialize session state variables
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

if 'user_skills' not in st.session_state:
    st.session_state.user_skills = []

if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None

if 'selected_job_title' not in st.session_state:
    st.session_state.selected_job_title = None

# Define color scheme based on current theme
def get_colors():
    """Return color dictionary based on current theme"""
    if st.session_state.theme == 'dark':
        return {
            'bg_primary': '#0F172A',
            'bg_secondary': '#1E293B',
            'bg_tertiary': '#334155',
            'text_primary': '#F1F5F9',
            'text_secondary': '#CBD5E1',
            'text_muted': '#94A3B8',
            'border': '#475569',
            'accent_primary': '#818CF8',
            'accent_secondary': '#A78BFA',
            'accent_tertiary': '#F472B6',
            'success': '#10B981',
            'warning': '#FBBF24',
            'error': '#F87171',
            'card_gradient': 'linear-gradient(135deg, #1E293B 0%, #0F172A 100%)',
        }
    else:
        return {
            'bg_primary': '#FFFFFF',
            'bg_secondary': '#F9FAFB',
            'bg_tertiary': '#F3F4F6',
            'text_primary': '#1F2937',
            'text_secondary': '#6B7280',
            'text_muted': '#9CA3AF',
            'border': '#E5E7EB',
            'accent_primary': '#6366F1',
            'accent_secondary': '#8B5CF6',
            'accent_tertiary': '#EC4899',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'card_gradient': 'linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 100%)',
        }

colors = get_colors()

# Apply theme to entire app using aggressive CSS
st.markdown(f"""
<style>
  html, body, .stApp, .main {{
    background-color: {colors['bg_primary']} !important;
    color: {colors['text_primary']} !important;
  }}
  
  [data-testid="stAppViewContainer"] {{
    background-color: {colors['bg_primary']} !important;
    color: {colors['text_primary']} !important;
  }}

  header[data-testid="stHeader"], footer {{ visibility: hidden; height: 0; }}
  section[data-testid="stSidebar"] {{ display: none !important; }}

  /* Text elements */
  p, span, label, div, a {{
    color: {colors['text_primary']} !important;
  }}

  /* Headings */
  h1, h2, h3, h4, h5, h6 {{
    color: {colors['text_primary']} !important;
  }}

  /* Divider */
  hr {{
    border-color: {colors['border']} !important;
  }}

  /* Select/Dropdown elements - always dark background */
  select, .stSelectbox {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
  }}
  
  select option {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
  }}
  
  /* Streamlit-specific selectbox styling */
  div[data-baseweb="select"] {{
    background-color: {colors['bg_secondary']} !important;
  }}
  
  div[data-baseweb="select"] input {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
  }}
  
  div[data-baseweb="select"] > div {{
    background-color: {colors['bg_secondary']} !important;
  }}
  
  /* Popover/dropdown menu items */
  [role="listbox"], [role="option"] {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
  }}
  
  [role="option"][aria-selected="true"] {{
    background-color: {colors['accent_primary']} !important;
    color: white !important;
  }}
  
  /* Input fields styling */
  input[type="text"], input[type="password"], input[type="email"], textarea {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
    border: 1px solid {colors['border']} !important;
  }}
  
  input[type="text"]::placeholder, textarea::placeholder {{
    color: {colors['text_secondary']} !important;
  }}
  
  /* BaseWeb components - general */
  .stSelectbox > div {{
    background-color: {colors['bg_secondary']} !important;
  }}
  
  /* Any div with role=button that's part of select */
  [role="button"][aria-haspopup="listbox"] {{
    background-color: {colors['bg_secondary']} !important;
    color: {colors['text_primary']} !important;
    border: 1px solid {colors['border']} !important;
  }}

  /* Custom classes */
  .custom-card {{
    background: {colors['card_gradient']} !important;
    border-color: {colors['border']} !important;
    color: {colors['text_primary']} !important;
  }}

  .skill-badge {{
    background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_secondary']} 100%) !important;
    color: white !important;
    border-color: {colors['accent_primary']} !important;
  }}

  .stage-card {{
    background: {colors['card_gradient']} !important;
    border-left-color: {colors['accent_primary']} !important;
    color: {colors['text_primary']} !important;
  }}

  .stage-title {{
    color: {colors['text_primary']} !important;
  }}

    /* File uploader and uploaded file list - ensure visible in dark theme */
    .stFileUploader, div[data-testid="stFileUploader"] {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }}

    /* The internal file input/button inside uploader */
    .stFileUploader button, .stFileUploader input[type="file"], div[data-testid="stFileUploader"] button {{
        background-color: transparent !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
    }}

    /* Buttons and clickable tags (Add/skill badges) */
    button, .stButton>button {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        box-shadow: none !important;
        border-radius: 8px !important;
    }}

    /* Expander content and panels */
    div[role="region"], .stExpander, .stExpander div[role="button"] + div {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}

    /* Uploaded file name list - make text visible */
    .uploadedFileList, .stUploadedFileList, .stUploadedFileList > div {{
        background-color: transparent !important;
        color: {colors['text_primary']} !important;
    }}

    /* Ensure skill cards (small white boxes) use dark background and visible text */
    .skill-card, .small-skill, .skill-badge, .skill-pill {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        box-shadow: none !important;
    }}

    /* Stronger overrides for file input controls (browser-native parts) */
    /* Target Streamlit uploader container and all descendants */
    [data-testid="stFileUploader"], .stFileUploader, [data-testid="stFileUploader"] * {{
        color: {colors['text_primary']} !important;
        background-color: transparent !important;
    }}

    /* Style the native file input and its button across browsers */
    input[type="file"] {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        padding: 6px 8px !important;
        border-radius: 6px !important;
    }}

    /* Chrome / Edge / Safari upload button */
    input[type="file"]::-webkit-file-upload-button {{
        background-color: {colors['bg_tertiary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        padding: 6px 10px !important;
        border-radius: 6px !important;
    }}

    /* IE/Edge legacy */
    input[type="file"]::-ms-browse {{
        background-color: {colors['bg_tertiary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
    }}

    /* Make uploader's internal buttons highly visible */
    [data-testid="stFileUploader"] button, .stFileUploader button, .stFileUploader .stButton > button {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
    }}

    /* Ensure the 'No file chosen' / filename text is readable */
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] div {{
        color: {colors['text_primary']} !important;
    }}

    /* Expander header and summary (the "➕ X additional skills found" control) */
    .stExpander > div[role="button"], .stExpander div[role="button"], .stExpanderHeader, .streamlit-expanderHeader, .stExpanderSummary, details summary {{
        background-color: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        box-shadow: none !important;
    }}

    /* When expander is open, ensure inner header stays consistent */
    .stExpander[open] > div[role="button"], details[open] summary {{
        background-color: {colors['bg_tertiary']} !important;
        color: {colors['text_primary']} !important;
    }}

    /* Skill card inline styles used in gap UI: ensure readable text on light card backgrounds */
    div[style*="#fee2e2"] {{
        color: #7f1d1d !important;
    }}
    div[style*="#fef3c7"] {{
        color: #78350f !important;
    }}
    div[style*="#dcfce7"] {{
        color: #15803d !important;
    }}
    /* Extra skills card background */
    div[style*="#e0e7ff"] {{
        color: #1e293b !important;
    }}
    /* Force descendants (titles, small text, spans, paragraphs) inside the inline-styled cards to use readable colors */
    div[style*="#fee2e2"] *, div[style*="#fee2e2"] > * {{
        color: #7f1d1d !important;
    }}
    div[style*="#fef3c7"] *, div[style*="#fef3c7"] > * {{
        color: #78350f !important;
    }}
    div[style*="#dcfce7"] *, div[style*="#dcfce7"] > * {{
        color: #15803d !important;
    }}
    div[style*="#e0e7ff"] *, div[style*="#e0e7ff"] > * {{
        color: #1e293b !important;
    }}
    /* Also cover RGB-formatted inline styles (some browsers/Renderers use rgb(...) instead of hex) */
    div[style*="rgb(254, 226, 226)"], div[style*="rgb(254,226,226)"], div[style*="rgb(254, 226,226)"], div[style*="rgb(254,226, 226)"] {{
        color: #7f1d1d !important;
    }}
    div[style*="rgb(254, 226, 226)"] *, div[style*="rgb(254,226,226)"] * {{
        color: #7f1d1d !important;
    }}

    div[style*="rgb(254, 243, 199)"], div[style*="rgb(254,243,199)"], div[style*="rgb(254, 243,199)"], div[style*="rgb(254,243, 199)"] {{
        color: #78350f !important;
    }}
    div[style*="rgb(254, 243, 199)"] *, div[style*="rgb(254,243,199)"] * {{
        color: #78350f !important;
    }}

    div[style*="rgb(220, 252, 231)"], div[style*="rgb(220,252,231)"], div[style*="rgb(220, 252,231)"], div[style*="rgb(220,252, 231)"] {{
        color: #15803d !important;
    }}
    div[style*="rgb(220, 252, 231)"] *, div[style*="rgb(220,252,231)"] * {{
        color: #15803d !important;
    }}

    div[style*="rgb(224, 231, 255)"], div[style*="rgb(224,231,255)"], div[style*="rgb(224, 231,255)"], div[style*="rgb(224,231, 255)"] {{
        color: #1e293b !important;
    }}
    div[style*="rgb(224, 231, 255)"] *, div[style*="rgb(224,231,255)"] * {{
        color: #1e293b !important;
    }}

    /* --- Custom app layout overrides --- */
    /* Widen the main content area while keeping reasonable side padding */
    .main > div {{
        max-width: 1200px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}

    @media (max-width: 900px) {{
        .main > div {{
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
    }}

    /* Animated accent line used under hero subtitle */
    .accent-line {{
        margin: 1rem auto;
        height: 4px;
        width: 200px;
        border-radius: 999px;
        background: linear-gradient(90deg, {colors['accent_tertiary']}, {colors['accent_primary']}, {colors['accent_secondary']});
        background-size: 200% 100%;
        animation: accentPulse 3s ease-in-out infinite;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }}

    @keyframes accentPulse {{
        0%   {{ background-position: 0% 50%;   opacity: 0.65; }}
        50%  {{ background-position: 100% 50%; opacity: 1.0; }}
        100% {{ background-position: 0% 50%;   opacity: 0.65; }}
    }}

</style>
""", unsafe_allow_html=True)

# Section title styling for consistent typography and subtle underline

# Header with modern gradient and professional branding
col1, col2, col3 = st.columns([1, 0.05, 0.15])

with col1:
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0 3rem 0;">
        <h1 style="
            color: {colors['accent_primary']};
            font-size: 4rem;
            margin-bottom: 0.5rem;
            font-weight: 900;
            letter-spacing: -0.03em;
        ">🎯 Skills Gap Analyzer</h1>
        <p style="
            color: {colors['text_secondary']};
            font-size: 1.25rem;
            font-weight: 500;
            margin-top: 0.75rem;
            letter-spacing: 0.02em;
        ">AI-Powered Career Development Platform</p>
        <div class="accent-line"></div>
        <p style="
            color: {colors['text_secondary']};
            font-size: 0.95rem;
            margin-top: 1rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        ">Identify your skill gaps and get personalized learning recommendations using Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Theme toggle button in top right
    if st.button(
        st.session_state.theme == "light" and "🌙" or "☀️",
        key="theme_toggle",
        help=f"Switch to {'dark' if st.session_state.theme == 'light' else 'light'} mode"
    ):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

# Load data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load essential data efficiently - optimized for performance"""
    loader = DataLoader()
    
    try:
        # Load jobs efficiently (5000 sample is optimal balance)
        jobs_df = loader.load_jobs_data(sample_size=5000)
        
        # Extract actual skills from job requirements (fast set operations)
        all_job_skills = loader.get_all_skills_fast()
        
        # Load skills taxonomy and merge
        skills_df = loader.load_skills_taxonomy()
        
        # Build efficient mappings for fast lookups
        if not skills_df.empty:
            taxonomy_skills = set(skills_df['skill_group_name'].str.lower().str.strip().unique())
            # Combine both sets
            all_skills_combined = all_job_skills | taxonomy_skills
        else:
            all_skills_combined = all_job_skills
        
        # Clean and normalize job titles
        if not jobs_df.empty and 'job_title' in jobs_df.columns:
            jobs_df = jobs_df.copy()
            jobs_df['job_title_clean'] = jobs_df['job_title'].str.strip().str.title()
            # Remove duplicates
            jobs_df['job_title_clean'] = jobs_df['job_title_clean'].str.replace(r'\s+', ' ', regex=True)

        # Ensure any list-valued entries in DataFrame columns are converted to hashable types
        # Streamlit's caching/hashing will fail on unhashable types (like list), so convert
        # common list-like columns (e.g., 'skill_list') to tuples for safe hashing.
        try:
            # operate on a copy to avoid accidental side-effects
            for col in jobs_df.columns:
                try:
                    if jobs_df[col].apply(lambda x: isinstance(x, list)).any():
                        jobs_df[col] = jobs_df[col].apply(lambda x: tuple(x) if isinstance(x, list) else x)
                except Exception:
                    # If a per-column conversion fails, skip it and continue
                    continue
        except Exception:
            # If any unexpected error occurs, allow Streamlit to fallback to pickling
            pass

        return jobs_df, skills_df, sorted(list(all_skills_combined))
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), []

jobs_df, skills_df, available_skills = load_data()

# Detect optional model modules/artifacts to simplify UI
import importlib
recommender_available = True
try:
    importlib.import_module('src.models.recommender')
except Exception:
    recommender_available = False

cluster_available = False
try:
    importlib.import_module('src.models.cluster_analyzer')
    cluster_available = True
except Exception:
    # also check for a saved clustering model artifact
    cluster_available = os.path.exists(os.path.join('app', 'models', 'clustering_model.pkl'))

# Helper function to get unique job titles from data
@st.cache_data
def get_unique_job_titles(df):
    """Extract unique job titles from jobs dataframe"""
    if df.empty or 'job_title' not in df.columns:
        return ["Data Scientist", "Senior Engineer", "ML Engineer", "Product Manager"]
    
    unique_titles = df['job_title'].str.strip().str.title().unique()
    # Limit to top 30 by frequency
    title_counts = df['job_title'].value_counts()
    top_titles = title_counts.head(30).index.tolist()
    clean_titles = [t.strip().title() for t in top_titles]
    return sorted(list(set(clean_titles)))

unique_job_titles = get_unique_job_titles(jobs_df)

# ====================
# SECTION 1: BUILD YOUR PROFILE
# ====================
st.markdown("<h2 class='section-title'>1️⃣ Build your profile</h2>", unsafe_allow_html=True)

# Two-column layout: Skills on left, Job on right
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Your Skills")
    
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
            # Clean, deduplicate, and sort all skills
            # Remove empty strings, normalize case, and deduplicate
            cleaned_skills = set()
            for skill in available_skills:
                if skill and isinstance(skill, str):
                    normalized = skill.strip().lower()
                    if normalized and len(normalized) > 1:  # Filter out single chars
                        cleaned_skills.add(normalized)
            
            sorted_skills = sorted(list(cleaned_skills))
            
            st.caption(f"💡 {len(sorted_skills)} unique skills available (from job listings and taxonomy)")
            
            # Use skills extracted from actual job requirements
            user_skills = st.multiselect(
                "Select your skills (search or scroll to find skills):",
                sorted_skills,
                placeholder="Start typing to search skills...",
                label_visibility="visible"
            )
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
                    
                    # Get API key securely (Streamlit secrets preferred, then env var)
                    api_key = None
                    if use_llm:
                        try:
                            api_key = get_openai_api_key()
                        except Exception:
                            st.warning("⚠️ OpenAI API key not configured. Set it in Streamlit secrets or environment.")
                            # disable LLM mode if no key available
                            use_llm = False
                            api_key = None
                    
                    extractor = SkillExtractor(extractor_skills, use_llm=use_llm, api_key=api_key)
                    
                    # Extract skills with confidence scores
                    if uploaded_file.name.endswith('.pdf'):
                        text = extractor._read_pdf(uploaded_file)
                        user_skills_with_conf = extractor.extract_from_text(text, return_confidence=True)
                    else:
                        text = extractor._read_docx(uploaded_file)
                        user_skills_with_conf = extractor.extract_from_text(text, return_confidence=True)
                    
                    # Show extraction method used
                    if use_llm and api_key:
                        st.caption("🤖 Using AI-powered (OpenAI) extraction")
                    
                    if user_skills_with_conf:
                        # Separate high and medium confidence skills
                        high_conf_skills = [skill for skill, conf in user_skills_with_conf if conf >= 0.7]
                        medium_conf_skills = [skill for skill, conf in user_skills_with_conf if 0.5 <= conf < 0.7]
                        
                        # Use high confidence skills as primary
                        user_skills = high_conf_skills
                        # Persist to session state so other sections can access immediately
                        try:
                            st.session_state.user_skills = user_skills
                        except Exception:
                            pass
                        
                        if user_skills:
                            st.success(f"✅ Extracted {len(user_skills)} skills from your CV")
                            
                            # Show skills in a clean grid
                            cols = st.columns(4)
                            for idx, skill in enumerate(user_skills):
                                with cols[idx % 4]:
                                    st.markdown(f"<div class='skill-badge'>{skill.title()}</div>", unsafe_allow_html=True)
                            
                            if medium_conf_skills:
                                with st.expander(f"➕ {len(medium_conf_skills)} additional skills found"):
                                    # Button to add all additional skills at once
                                    if st.button(f"Add all {len(medium_conf_skills)} additional skills", key="add_all_additional"):
                                        added = 0
                                        for skill in medium_conf_skills:
                                            if skill not in user_skills:
                                                user_skills.append(skill)
                                                added += 1
                                        # persist and remember recent additions for undo
                                        st.session_state.user_skills = user_skills
                                        st.session_state._recently_added_skills = medium_conf_skills
                                        st.success(f"Added {added} skills")
                                        st.rerun()

                                    cols2 = st.columns(4)
                                    for idx, skill in enumerate(medium_conf_skills[:12]):
                                        with cols2[idx % 4]:
                                            if st.button(f"Add {skill.title()}", key=f"add_{skill}"):
                                                if skill not in user_skills:
                                                    user_skills.append(skill)
                                                    st.session_state.user_skills = user_skills
                                                    st.session_state._recently_added_skills = [skill]
                                                st.rerun()
                                # Provide undo option for recent additions
                                if st.session_state.get('_recently_added_skills'):
                                    if st.button("Undo last added skills", key="undo_recent_cv"):
                                        recent = st.session_state.pop('_recently_added_skills', [])
                                        current = st.session_state.get('user_skills', [])
                                        for s in recent:
                                            if s in current:
                                                current.remove(s)
                                        st.session_state.user_skills = current
                                        st.success(f"Removed {len(recent)} recently added skills")
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
                    
                    # Get API key securely (Streamlit secrets preferred, then env var)
                    api_key = None
                    if use_llm:
                        try:
                            api_key = get_openai_api_key()
                        except Exception:
                            st.warning("⚠️ OpenAI API key not configured. Set it in Streamlit secrets or environment.")
                            use_llm = False
                            api_key = None
                    
                    extractor = SkillExtractor(extractor_skills, use_llm=use_llm, api_key=api_key)
                    user_skills_with_conf = extractor.extract_from_text(description, return_confidence=True)
                    
                    # Show extraction method used
                    if use_llm and api_key:
                        st.caption("🤖 Using AI-powered (OpenAI) extraction")
                    
                    if user_skills_with_conf:
                        # Split into high and medium confidence for interactive adds
                        high_conf_skills = [skill for skill, conf in user_skills_with_conf if conf >= 0.7]
                        medium_conf_skills = [skill for skill, conf in user_skills_with_conf if 0.4 <= conf < 0.7]

                        # Use high confidence skills as primary
                        user_skills = high_conf_skills
                        try:
                            st.session_state.user_skills = user_skills
                        except Exception:
                            pass

                        if user_skills:
                            st.success(f"✅ Found {len(user_skills)} high-confidence skills from your description")

                            # Show extracted skills with medium-confidence expander
                            with st.expander("📋 Extracted Skills", expanded=True):
                                cols = st.columns(4)
                                for idx, skill in enumerate(user_skills):
                                    conf = next((conf for s, conf in user_skills_with_conf if s == skill), 0)
                                    with cols[idx % 4]:
                                        if conf >= 0.7:
                                            st.success(f"✓ {skill.title()}")
                                        else:
                                            st.info(f"• {skill.title()}")

                                if medium_conf_skills:
                                    # Add all medium-confidence skills
                                    if st.button(f"Add all {len(medium_conf_skills)} additional skills", key="add_all_desc"):
                                        added = 0
                                        for skill in medium_conf_skills:
                                            if skill not in user_skills:
                                                user_skills.append(skill)
                                                added += 1
                                        st.session_state.user_skills = user_skills
                                        st.session_state._recently_added_skills = medium_conf_skills
                                        st.success(f"Added {added} skills")
                                        st.rerun()

                                    cols2 = st.columns(4)
                                    for idx, skill in enumerate(medium_conf_skills[:12]):
                                        with cols2[idx % 4]:
                                            if st.button(f"Add {skill.title()}", key=f"add_desc_{skill}"):
                                                if skill not in user_skills:
                                                    user_skills.append(skill)
                                                    st.session_state.user_skills = user_skills
                                                    st.session_state._recently_added_skills = [skill]
                                                st.rerun()

                                    # Undo option for recent additions
                                    if st.session_state.get('_recently_added_skills'):
                                        if st.button("Undo last added skills", key="undo_recent_desc"):
                                            recent = st.session_state.pop('_recently_added_skills', [])
                                            current = st.session_state.get('user_skills', [])
                                            for s in recent:
                                                if s in current:
                                                    current.remove(s)
                                            st.session_state.user_skills = current
                                            st.success(f"Removed {len(recent)} recently added skills")
                                            st.rerun()
                        else:
                            st.warning("⚠️ No high-confidence skills found. Try being more specific.")
                            st.info("💡 Tip: Mention specific technologies, tools, and frameworks explicitly.")
                    else:
                        st.info("💡 No skills detected. Try mentioning specific technologies like 'Python', 'SQL', 'AWS', etc.")
                except Exception as e:
                    st.error(f"❌ Error extracting skills: {e}")
    
    # Save to session state
    if user_skills:
        st.session_state.user_skills = [s.lower().strip() for s in user_skills]

with col2:
    st.subheader("🎯 Target Job Role")
    
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
        
        # Optional: Show job recommendations based on user skills
        recommended_jobs_info = None
        if 'user_skills' not in st.session_state:
            st.session_state.user_skills = []

        if st.session_state.user_skills:
            try:
                # Calculate match percentage for each job based on skill overlap
                user_set = set(s.lower().strip() for s in st.session_state.user_skills)
                
                recommended_jobs_list = []
                for idx, job_row in jobs_df.iterrows():
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
                <div style="
                    background: {colors['bg_secondary']};
                    border-radius: 12px;
                    padding: 16px;
                    margin: 1rem 0;
                    border-left: 4px solid {colors['accent_primary']};
                ">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                        <div>
                            <p style="margin: 0 0 0.5rem 0; color: {colors['text_secondary']}; font-weight: 500;">Company</p>
                            <p style="margin: 0; color: {colors['text_primary']}; font-weight: 600; font-size: 1.1rem;">{job_data.get('company', 'N/A')}</p>
                        </div>
                        <div>
                            <p style="margin: 0 0 0.5rem 0; color: {colors['text_secondary']}; font-weight: 500;">Location</p>
                            <p style="margin: 0; color: {colors['text_primary']}; font-weight: 600; font-size: 1.1rem;">📍 {job_data.get('location', 'N/A')}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show required skills preview
                job_skills_list = job_data.get('skill_list', [])
                
                # Parse job skills properly
                parsed_skills = []
                
                if isinstance(job_skills_list, (list, tuple)):
                    # Handle list or tuple directly
                    parsed_skills = [str(s).strip() for s in job_skills_list if s and str(s).strip()]
                elif isinstance(job_skills_list, str):
                    # String representation - try to parse
                    import ast
                    try:
                        parsed = ast.literal_eval(job_skills_list)
                        if isinstance(parsed, (list, tuple)):
                            parsed_skills = [str(s).strip() for s in parsed if s and str(s).strip()]
                        else:
                            parsed_skills = []
                    except (ValueError, SyntaxError):
                        # If parsing fails, try comma separation
                        try:
                            parsed_skills = [s.strip() for s in job_skills_list.split(',') if s.strip()]
                        except:
                            parsed_skills = []
                else:
                    parsed_skills = []
                
                # Always display skills section with header
                st.markdown(f"""
                <div style="
                    margin: 1.5rem 0 1rem 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid {colors['accent_primary']};
                ">
                    <h3 style="margin: 0; color: {colors['text_primary']}; display: flex; align-items: center; gap: 0.5rem;">
                        📚 Required Skills for This Role
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                if parsed_skills:
                    st.markdown(f"**Total:** `{len(parsed_skills)} skills`")
                    with st.expander("✏️ View all required skills", expanded=True):
                        cols = st.columns(3)
                        for idx, skill in enumerate(parsed_skills):
                            with cols[idx % 3]:
                                st.caption(f"• {skill.title()}")
                else:
                    st.info("📋 No specific skills data available for this job posting.")
            else:
                st.warning("⚠️ Unable to find the selected job. Please try another job title.")
    else:
        st.warning("Job data not loaded. Please check data files.")

# ====================
# SECTION 2: SKILL GAP ANALYSIS
# ====================
if st.session_state.user_skills and st.session_state.selected_job:
    st.divider()
    st.markdown("<h2 class='section-title'>2️⃣ Skill gap analysis</h2>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Compare your skills to the role and prioritize the most important gaps.</div>", unsafe_allow_html=True)
    
    # Get job skills
    job = st.session_state.selected_job
    job_skills_raw = job.get('skill_list', [])
    
    # Parse job skills - handle multiple formats
    job_skills = []
    if isinstance(job_skills_raw, str):
        import ast
        try:
            parsed = ast.literal_eval(job_skills_raw)
            if isinstance(parsed, (list, tuple)):
                job_skills = [str(s).strip().lower() for s in parsed if s]
            else:
                job_skills = []
        except:
            # Try comma-separated format
            job_skills = [s.strip().lower() for s in job_skills_raw.split(',') if s.strip()]
    elif isinstance(job_skills_raw, (list, tuple)):
        job_skills = [str(s).strip().lower() for s in job_skills_raw if s]
    else:
        job_skills = []
    
    # Normalize user skills to lowercase
    user_skills_normalized = [s.lower().strip() for s in st.session_state.user_skills if s]
    
    # Convert to sets for fast comparison
    user_set = set(user_skills_normalized)
    job_set = set(job_skills)
    
    # Remove empty strings
    user_set.discard('')
    job_set.discard('')
    
    # Calculate gap
    matching = user_set & job_set
    missing = job_set - user_set
    extra = user_set - job_set
    
    match_percent = (len(matching) / len(job_set) * 100) if job_set else 0
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid {colors['accent_primary']};
        margin: 1.5rem 0;
    ">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Required for role:</p>
                <p style="color: {colors['text_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">{len(job_set)} skills</p>
            </div>
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Your matching:</p>
                <p style="color: {colors['success']}; font-size: 1.5rem; font-weight: 700; margin: 0;">{len(matching)} skills</p>
            </div>
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Your match rate:</p>
                <p style="color: {colors['accent_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">{match_percent:.1f}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    st.progress(match_percent / 100, text=f"Career Readiness: {match_percent:.1f}%")
    st.write("")
    
    # Set up color scheme
    if st.session_state.get('theme', 'dark') == 'dark':
        match_bg = '#dcfce7'
        match_border = '#22c55e'
        match_title = '#0a4e1a'
        missing_bg = '#fee2e2'
        missing_border = '#dc2626'
        missing_title = '#4b0000'
        extra_bg = '#e0e7ff'
        extra_title = '#1e1b4b'
    else:
        match_bg = '#dcfce7'
        match_border = '#22c55e'
        match_title = '#15803d'
        missing_bg = '#fee2e2'
        missing_border = '#dc2626'
        missing_title = '#7f1d1d'
        extra_bg = '#e0e7ff'
        extra_title = '#312e81'
    
    # EXPANDER 1: Matching Skills
    with st.expander("✅ Your Matching Skills", expanded=False):
        if matching:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(matching)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: {match_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid {match_border};">
                        <div style="font-weight: 600; color: {match_title} !important;">✓ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No matching skills found yet.")
    
    # EXPANDER 2: Missing Skills
    with st.expander("❌ Skills You Need", expanded=True):
        if missing:
            # Define fallback colors for the exception handler
            missing_bg = '#f3f4f6'
            missing_border = '#6b7280'
            missing_title = '#374151'
            
            # Use SkillMatcher for optimized gap analysis
            from src.models.skill_matcher import SkillMatcher
            from src.data.loader import DataLoader
            import pandas as pd
            import ast
            import re
            from difflib import get_close_matches

            try:
                from rapidfuzz import process as rf_process, fuzz as rf_fuzz
                _have_rapidfuzz = True
            except Exception:
                _have_rapidfuzz = False

            # Small alias map - extend over time via UI inspector
            ALIAS_MAP = {
                'k8s': 'kubernetes',
                'aws': 'amazon web services',
                'gcp': 'google cloud platform',
                'ci/cd': 'ci cd',
                'ci-cd': 'ci cd',
                'ci_cd': 'ci cd',
                'devops': 'devops',
                'monitoring and logging tools': 'monitoring and logging tools',
            }

            RULE_CONF_THRESHOLD = 0.30  # ignore rules with confidence below this when counting unlocks

            def normalize_skill(s: str) -> str:
                if not s or not isinstance(s, str):
                    return ""
                s2 = s.strip().lower()
                s2 = re.sub(r"[\(\)\[\]\"']", "", s2)
                s2 = re.sub(r"[_\-\/]", " ", s2)
                s2 = re.sub(r"\s+", " ", s2).strip()
                return ALIAS_MAP.get(s2, s2)

            def fuzzy_in_set(target: str, candidates_set: set, score_threshold: int = 85) -> bool:
                t = target.lower().strip()
                if t in candidates_set:
                    return True
                t_norm = normalize_skill(t)
                if t_norm in candidates_set:
                    return True
                if _have_rapidfuzz and candidates_set:
                    best = rf_process.extractOne(t_norm, list(candidates_set), scorer=rf_fuzz.token_sort_ratio)
                    if best and best[1] >= score_threshold:
                        return True
                else:
                    tries = get_close_matches(t_norm, list(candidates_set), n=1, cutoff=score_threshold / 100.0)
                    if tries:
                        return True
                return False
            
            try:
                # Build skill-to-category mapping
                loader = DataLoader()
                skill_to_cat_map = loader.get_skill_to_category_map()
                matcher = SkillMatcher(skill_to_cat_map)
                
                # Load association rules for better prioritization
                rules_df = None
                rules_combined_df = None
                rules_cat_df = None
                try:
                    rules_path = os.path.join('data', 'processed', 'association_rules_skills.csv')
                    if os.path.exists(rules_path):
                        rules_df = pd.read_csv(rules_path)
                        st.session_state.rules_loaded = True
                    # combined rules (A3)
                    combined_path = os.path.join('data', 'processed', 'association_rules_combined.csv')
                    if os.path.exists(combined_path):
                        rules_combined_df = pd.read_csv(combined_path)
                        st.session_state.rules_combined_loaded = True
                    # category-level rules (A2)
                    cat_path = os.path.join('data', 'processed', 'association_rules_categories.csv')
                    if os.path.exists(cat_path):
                        rules_cat_df = pd.read_csv(cat_path)
                        st.session_state.rules_cat_loaded = True
                except Exception:
                    st.session_state.rules_loaded = False
                
                # Get prioritized missing skills (with association rules)
                gap_analysis = matcher.analyze_gap(
                    list(user_set),
                    list(job_set),
                    rules_df=rules_df  # Pass association rules for better prioritization
                )
                
                # Show learning time estimate
                learning_estimate = matcher.estimate_learning_time(gap_analysis['missing'])
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#ef4444;'>{len(missing)}</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Skills to Learn</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#3b82f6;'>{learning_estimate['total_hours']:.0f}h</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Hours</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#f59e0b;'>{learning_estimate['total_weeks']:.1f}w</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Weeks</div></div>", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#10b981;'>{learning_estimate['total_months']:.1f}m</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Months</div></div>", unsafe_allow_html=True)
                
                # Use prioritized missing skills returned by SkillMatcher
                missing_sorted = gap_analysis.get('missing', sorted(missing))

                # If rules_df was loaded, compute unlocks/confidence for display
                skill_rule_meta = {}
                if 'rules_df' in locals() and rules_df is not None and not rules_df.empty:
                    try:
                        # normalize job skills for matching
                        job_skills_norm = {s.lower().strip() for s in job_set}
                        for skill in missing_sorted:
                            try:
                                unlocks_job = 0
                                total_consequents = 0
                                confs = []
                                consequents_accum = []

                                # find rows where skill appears in antecedents (safe comparison)
                                # antecedents are stored as stringified frozenset; parse with ast.literal_eval
                                mask = rules_df['antecedents'].astype(str).apply(lambda x: skill.lower().strip() in x.lower())
                                subset = rules_df[mask]

                                for _, row in subset.iterrows():
                                    try:
                                        # skip weak rules by confidence
                                        conf_val = row.get('confidence', None)
                                        if pd.notna(conf_val):
                                            try:
                                                if float(conf_val) < RULE_CONF_THRESHOLD:
                                                    continue
                                            except Exception:
                                                pass

                                        ants = ast.literal_eval(row.get('antecedents', 'set()')) if isinstance(row.get('antecedents'), str) else set()
                                        cons = ast.literal_eval(row.get('consequents', 'set()')) if isinstance(row.get('consequents'), str) else set()
                                        # normalize consequents
                                        cons_norm = {normalize_skill(c) for c in cons if isinstance(c, str)}
                                        consequents_accum.extend(list(cons_norm))
                                        total_consequents += len(cons_norm)
                                        # count how many consequents match the job's required skills using fuzzy matching
                                        for c_norm in cons_norm:
                                            if fuzzy_in_set(c_norm, job_skills_norm, score_threshold=82):
                                                unlocks_job += 1
                                        # collect confidence
                                        if pd.notna(conf_val):
                                            try:
                                                confs.append(float(conf_val))
                                            except Exception:
                                                pass
                                    except Exception:
                                        continue

                                avg_conf = float(sum(confs) / len(confs)) if confs else None
                                skill_rule_meta[skill] = {
                                    'unlocks_job': int(unlocks_job),
                                    'total_consequents': int(len(set(consequents_accum))) if consequents_accum else 0,
                                    'avg_confidence': avg_conf,
                                    'consequents_list': sorted(list(set(consequents_accum))) if consequents_accum else []
                                }
                            except Exception:
                                skill_rule_meta[skill] = {'unlocks_job': 0, 'total_consequents': 0, 'avg_confidence': None, 'consequents_list': []}
                    except Exception:
                        skill_rule_meta = {}

                # Split into priority tiers (preserve ordering from matcher)
                third = max(1, len(missing_sorted) // 3)
                high_priority = missing_sorted[:third] if missing_sorted else []
                med_priority = missing_sorted[third:third*2] if len(missing_sorted) > third else []
                low_priority = missing_sorted[third*2:] if len(missing_sorted) > third*2 else []
                
                # Define priority colors
                critical_bg = '#fee2e2'
                critical_border = '#dc2626'
                critical_title = '#7f1d1d' if st.session_state.get('theme', 'dark') != 'dark' else '#4b0000'
                critical_sub = '#991b1b' if st.session_state.get('theme', 'dark') != 'dark' else '#6b0000'
                
                med_bg = '#fef3c7'
                med_border = '#f59e0b'
                med_title = '#78350f' if st.session_state.get('theme', 'dark') != 'dark' else '#5a3c0a'
                med_sub = '#92400e' if st.session_state.get('theme', 'dark') != 'dark' else '#6b4608'
                
                low_bg = '#dcfce7'
                low_border = '#22c55e'
                low_title = '#15803d' if st.session_state.get('theme', 'dark') != 'dark' else '#0a4e1a'
                low_sub = '#166534' if st.session_state.get('theme', 'dark') != 'dark' else '#0a4e1a'
                
                # Add CSS for card grid
                st.markdown("""
                <style>
                .card-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 16px;
                    margin-top: 12px;
                    margin-bottom: 24px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                if high_priority:
                    st.markdown("##### 🔴 Critical — Learn first")
                    cards_html = '<div class="card-grid">'
                    for skill in high_priority:
                        cards_html += f'<div class="card"><div style="background: {critical_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {critical_border}; height: 100%;"><div style="font-weight: 600; color: {critical_title} !important;">{skill.title()}</div></div></div>'
                    cards_html += '</div>'
                    st.markdown(cards_html, unsafe_allow_html=True)
                
                if med_priority:
                    st.markdown("##### 🟡 Important — Learn after critical")
                    cards_html = '<div class="card-grid">'
                    for skill in med_priority:
                        cards_html += f'<div class="card"><div style="background: {med_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {med_border}; height: 100%;"><div style="font-weight: 600; color: {med_title} !important;">{skill.title()}</div></div></div>'
                    cards_html += '</div>'
                    st.markdown(cards_html, unsafe_allow_html=True)
                
                if low_priority:
                    st.markdown("##### 🟢 Nice to have — Learn if time permits")
                    cards_html = '<div class="card-grid">'
                    for skill in low_priority:
                        cards_html += f'<div class="card"><div style="background: {low_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {low_border}; height: 100%;"><div style="font-weight: 600; color: {low_title} !important;">{skill.title()}</div></div></div>'
                    cards_html += '</div>'
                    st.markdown(cards_html, unsafe_allow_html=True)

            except Exception as e:
                # Fallback: simple list display
                st.markdown(f"**Missing Skills ({len(missing)}):**")
                cols = st.columns(3)
                for idx, skill in enumerate(sorted(missing)):
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div style="background: {missing_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid {missing_border};">
                            <div style="font-weight: 600; color: {missing_title};">✗ {skill.title()}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.success("✅ You have all the required skills!")

    # EXPANDER 3: Extra Skills
    with st.expander("📊 Additional Skills You Have", expanded=False):
        if extra:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(extra)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: {extra_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid #6366f1;">
                        <div style="font-weight: 600; color: {extra_title};">+ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No additional skills beyond what's required.")
    
    # ====================
    # SECTION 2B: ASSOCIATION RULES RECOMMENDATIONS (NEW)
    # ====================
    # Display association rule-based recommendations prominently
    if missing and user_skills_normalized:
        st.markdown(f"""
        <hr style="margin: 2rem 0; border: none; border-top: 2px solid {colors['border']};">
        <h2 style="
            color: {colors['text_primary']};
            font-size: 1.5rem;
            margin: 1.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border-bottom: 2px solid {colors['accent_tertiary']};
            padding-bottom: 12px;
        "><span style="font-size: 1.75rem;">🤖</span> AI-Powered Skill Recommendations (Association Rules)</h2>
        """, unsafe_allow_html=True)
        
        with st.expander("ℹ️ How this works", expanded=False):
            st.markdown("""
            Our unsupervised association rules mining learned patterns from 200,000+ job profiles.
            Based on your current skills, these skills are frequently learned together by professionals advancing their careers.
            """)
        
        # Load and display association rules recommendations
        try:
            from src.models.association_miner import get_skill_recommendations_with_explanations
            # Always pass both user_skills and target_job_skills for job-aware recommendations
            rec_result = get_skill_recommendations_with_explanations(
                user_skills=user_skills_normalized,
                target_job_skills=job_skills,
                data_dir='data/processed',
                top_n=8,
                min_score=0.0
            )
            
            if rec_result.get('success'):
                recs = rec_result.get('recommendations', [])
                num_rules = rec_result.get('num_rules_loaded', 0)
                
                # Filter out 'Other' recommendation (noisy, not meaningful)
                recs = [r for r in recs if r.get('skill', '').strip().lower() != 'other']
                
                if recs:
                    st.caption(f"📊 Generated from {num_rules:,} association rules ({len(recs)} recommendations found)")
                    # Display recommendations in a nice grid
                    rec_cols = st.columns(2)
                    for idx, rec in enumerate(recs):
                        with rec_cols[idx % 2]:
                            skill_name = rec.get('skill', '').title()
                            score = rec.get('score', 0)
                            explanation = rec.get('explanation', 'No explanation available')
                            
                            # Score visualization (0-1 scale)
                            bar_width = int(score * 20)  # 20 chars max
                            bar = "█" * bar_width + "░" * (20 - bar_width)
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
                                border-radius: 12px;
                                padding: 14px;
                                border-left: 4px solid {colors['accent_tertiary']};
                                margin-bottom: 12px;
                            ">
                                <div style="font-weight: 700; color: {colors['accent_tertiary']}; font-size: 1.1rem; margin-bottom: 6px;">
                                    📚 {skill_name}
                                </div>
                                <div style="font-size: 0.75rem; color: {colors['text_secondary']}; margin-bottom: 8px;">
                                    {explanation}
                                </div>
                                <div style="font-size: 0.7rem; color: {colors['text_muted']}; margin-top: 6px;">
                                    Recommendation Score: <span style="font-weight: 600; color: {colors['accent_tertiary']};">{score:.1%}</span>
                                </div>
                                <div style="font-size: 0.65rem; color: {colors['text_muted']}; margin-top: 2px;">
                                    {bar}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("💡 No additional recommendations found. You might already have broad skill coverage for this role!")
            else:
                error_msg = rec_result.get('error_message', 'Unknown error')
                st.warning(f"⚠️ Could not load association rules: {error_msg}")
        
        except ImportError:
            st.warning("⚠️ Association rules module not available. Please run 02_association_rules.ipynb first.")
        except Exception as e:
            st.warning(f"⚠️ Error loading association rules: {str(e)}")
    
    # ====================
    # SECTION 3: PERSONALIZED LEARNING PATH
    # ====================
    st.markdown("<h2 class='section-title'>3️⃣ Personalized learning path</h2>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Skills are ranked using job demand and ML patterns for this role.</div>", unsafe_allow_html=True)
    
    # ===== NEW: Model-Driven Learning Path (powered by Association Rules) =====
    if missing:
        with st.spinner("⏳ Generating personalized learning path..."):
            # Load ensemble if available (non-fatal)
            try:
                from src.models.association_miner import AssociationEnsemble, get_association_rules_from_csv
            except Exception:
                AssociationEnsemble = None
                get_association_rules_from_csv = None

            from src.models.learning_path_generator import build_personalized_learning_path

            # Try to load ensemble (best-effort)
            ensemble = None
            try:
                if get_association_rules_from_csv is not None:
                    ensemble = get_association_rules_from_csv('data/processed')
                    # Verify ensemble has models loaded
                    if ensemble is None or not getattr(ensemble, 'models', []):
                        ensemble = None
            except Exception:
                ensemble = None

            # Call builder defensively
            try:
                path = build_personalized_learning_path(
                    user_skills=user_skills,
                    job_skills=job_skills,
                    ensemble=ensemble,
                    max_phases=4
                )
            except Exception as e:
                path = None
                error_msg = str(e)

            # Safe-check result and render
            sorted_missing = sorted(missing)
            if not path or not isinstance(path, dict) or 'phases' not in path or not path.get('phases'):
                # Fallback behavior (model unavailable or no phases)
                if 'error_msg' in locals():
                    st.info("Showing missing skills by requirement frequency instead (model-based path unavailable).")
                else:
                    st.info("No model-powered learning path available for this profile yet. Showing missing skills by requirement frequency instead.")

                for i, skill in enumerate(sorted_missing[:10], start=1):
                    st.write(f"{i}. **{skill.title()}**")
            else:
                # Safe rendering of phases
                phases = path.get('phases', [])
                total_weeks = float(path.get('total_weeks', 0.0) or 0.0)
                missing_count = int(path.get('missing_count', len(missing)))

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #10b981 0%, rgba(16, 185, 129, 0.1) 100%);
                    border-radius: 8px;
                    padding: 12px 16px;
                    border-left: 3px solid #10b981;
                    margin: 0.5rem 0 1rem 0;
                ">
                    <p style="margin: 0; color: {colors['text_primary']}; font-weight: 600; font-size: 0.95rem;">
                    ✅ Model-Powered Learning Path
                    </p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.3rem;'>{missing_count}</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Missing Skills</div></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.3rem;'>{len(phases)}</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Phases</div></div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.3rem;'>{total_weeks:.1f}w</div><div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Duration</div></div>", unsafe_allow_html=True)

                for phase in phases:
                    if not isinstance(phase, dict):
                        continue
                    phase_num = phase.get('phase_number', '?')
                    phase_title = phase.get('title', 'Phase')
                    phase_difficulty = phase.get('difficulty', 'Medium')
                    phase_weeks = phase.get('duration_weeks', 0)
                    phase_skills = phase.get('skills', []) or []

                    exp_label = f"Phase {phase_num}: {phase_title} ({phase_difficulty}) — {phase_weeks}w"
                    with st.expander(exp_label, expanded=(phase_num == 1)):
                        # Render skills safely
                        if phase_skills:
                            for s in phase_skills:
                                if isinstance(s, dict):
                                    name = s.get('name', '').title() or 'Unknown'
                                    score = s.get('final_score', 0)
                                    st.write(f"- {name} (score: {score:.2f})")
                                else:
                                    st.write(f"- {str(s)}")
    
    else:
        st.info("Add skills and select a job to see personalized learning path recommendations.")
        
        # Use AssociationEnsemble to determine priority and unlock potential across pickles and CSV fallbacks
        try:
            from src.models.association_miner import AssociationEnsemble

            # Candidate artifacts (pickles and CSV fallbacks)
            candidates = [
                os.path.join('app', 'models', 'association_rules_a2.pkl'),
                os.path.join('app', 'models', 'association_rules_a1.pkl'),
                os.path.join('app', 'models', 'association_rules_a3.pkl'),
                os.path.join('app', 'models', 'association_rules.pkl'),
                os.path.join('data', 'processed', 'association_rules_a2.pkl'),
                os.path.join('data', 'processed', 'association_rules_a1.pkl'),
                os.path.join('data', 'processed', 'association_rules_a3.pkl'),
                os.path.join('data', 'processed', 'association_rules_skills.csv'),
                os.path.join('data', 'processed', 'association_rules_categories.csv'),
                os.path.join('data', 'processed', 'association_rules_combined.csv'),
            ]

            found_paths = []
            for c in candidates:
                p = locate_model_file([c])
                if p and os.path.exists(p):
                    found_paths.append(p)

            skill_priorities = {}

            if found_paths:
                ensemble = AssociationEnsemble()
                ensemble.load_paths(found_paths)

                # Load skill -> category mapping to convert skills to categories (A2 expects categories)
                try:
                    dl = DataLoader()
                    skills_tax = dl.load_skills_taxonomy()
                    # Build mapping: skill_name -> category
                    skill_to_cat = {}
                    if isinstance(skills_tax, pd.DataFrame) and 'skill_group_name' in skills_tax.columns and 'skill_group_category' in skills_tax.columns:
                        for _, r in skills_tax.iterrows():
                            name = str(r['skill_group_name']).lower().strip()
                            cat = str(r['skill_group_category']).lower().strip()
                            if name:
                                skill_to_cat[name] = cat
                except Exception:
                    skill_to_cat = {}

                # For each missing skill, find how many other skills it unlocks
                for missing_skill in missing:
                    # Map user's skills and the missing skill to categories when possible
                    try:
                        user_cats = set()
                        for s in user_set:
                            sc = skill_to_cat.get(s.lower().strip())
                            if sc:
                                user_cats.add(sc)

                        missing_cat = skill_to_cat.get(missing_skill.lower().strip())

                        if missing_cat:
                            test_items = list(user_cats) + [missing_cat]
                        else:
                            test_items = list(user_set) + [missing_skill]
                    except Exception:
                        test_items = list(user_set) + [missing_skill]

                    recommendations = ensemble.get_recommendations(test_items, top_n=20)

                    # Count how many of the recommendations are also in missing skills (map back if needed)
                    unlocks_count = 0
                    if recommendations is not None and not recommendations.empty:
                        recommended_skills = set(r['skill'].lower().strip() for _, r in recommendations.iterrows())
                        if skill_to_cat:
                            missing_cats = set(skill_to_cat.get(s.lower().strip()) for s in missing if skill_to_cat.get(s.lower().strip()))
                            unlocks_count = len(recommended_skills & missing_cats)
                        else:
                            unlocks_count = len(recommended_skills & set(s.lower().strip() for s in missing))

                    # Calculate priority based on unlocks and ensemble score
                    if recommendations is not None and not recommendations.empty:
                        skill_recs = recommendations[recommendations['skill'].str.lower().str.strip() == missing_skill.lower().strip()]
                        if skill_recs.empty and skill_to_cat:
                            miss_cat = skill_to_cat.get(missing_skill.lower().strip())
                            if miss_cat:
                                skill_recs = recommendations[recommendations['skill'].str.lower().str.strip() == miss_cat]

                        # ensemble returns 'score' as combined measure
                        avg_confidence = float(skill_recs['score'].mean()) if not skill_recs.empty else 0.5
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
        # Build SkillGapAnalyzer with taxonomy mapping to generate per-skill roadmaps
        try:
            skill_to_cat_map = {}
            if isinstance(skills_df, pd.DataFrame) and 'skill_group_name' in skills_df.columns and 'skill_group_category' in skills_df.columns:
                for _, r in skills_df.iterrows():
                    name = str(r['skill_group_name']).lower().strip()
                    cat = str(r['skill_group_category']).lower().strip()
                    if name:
                        skill_to_cat_map[name] = cat
        except Exception:
            skill_to_cat_map = {}

        sga = SkillGapAnalyzer(skill_to_cat_map)

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

                # Render structured learning plan (stages, courses, projects) with compact cards
                try:
                    learning_plan = sga._get_learning_resources(skill)
                except Exception:
                    learning_plan = None

                if isinstance(learning_plan, dict):
                    prereqs = learning_plan.get('prerequisites', [])
                    if prereqs:
                        st.markdown("**Prerequisites:** " + ", ".join(p.title() for p in prereqs))

                    # Roadmap: render each stage as a compact card
                    stages = learning_plan.get('roadmap', [])
                    if stages:
                        cols_per_row = 2
                        for idx in range(0, len(stages), cols_per_row):
                            row = stages[idx: idx + cols_per_row]
                            cols = st.columns(len(row))
                            for ccol, stage in zip(cols, row):
                                title = stage.get('stage', 'Stage')
                                duration = stage.get('duration_weeks', '?')
                                goals = stage.get('goals', [])
                                courses = stage.get('courses', [])
                                projects = stage.get('projects', [])

                                # Build HTML for the card
                                goals_html = ''
                                if goals:
                                    goals_html = '<ul>' + ''.join(f'<li>{g}</li>' for g in goals[:6]) + '</ul>'

                                courses_html = ''
                                if courses:
                                    courses_html = '<ul>' + ''.join(f'<li>{make_course_link(c)}</li>' for c in courses[:6]) + '</ul>'

                                projects_html = ''
                                if projects:
                                    projects_html = '<ul>' + ''.join(f'<li>{p}</li>' for p in projects[:6]) + '</ul>'

                                card_html = f'''
                                <div class="stage-card" style="background: linear-gradient(135deg, #ffffff, #f8fafc);">
                                  <div class="stage-title">{title} — <small style="color: #6B7280;">{duration} wk(s)</small></div>
                                  <div style="font-size: 0.92rem;">{goals_html}
                                  {courses_html}
                                  {projects_html}</div>
                                </div>
                                '''
                                ccol.markdown(card_html, unsafe_allow_html=True)

                    # Suggested courses and estimated time
                    suggested = learning_plan.get('suggested_courses', [])
                    if suggested:
                        suggested_links = [make_course_link(s) for s in suggested]
                        st.markdown("**Suggested Courses:** " + ', '.join(suggested_links), unsafe_allow_html=True)

                    est = learning_plan.get('estimated_time_weeks')
                    if extra:
                        st.markdown(f"**You have {len(extra)} extra skills:**")
                        cols = st.columns(4)
                        for idx, skill in enumerate(sorted(extra)):
                            with cols[idx % 4]:
                                st.markdown(f"""
                                <div style="background: {extra_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid #6366f1;">
                                    <div style="font-weight: 600; color: {extra_title} !important;">+ {skill.title()}</div>
                                </div>
                                """, unsafe_allow_html=True)

# ====================
# SECTION 4: SIMILAR OPPORTUNITIES
# ====================
st.markdown("<h2 class='section-title'>4️⃣ Similar opportunities</h2>", unsafe_allow_html=True)
st.markdown("<div class='section-sub'>Jobs that share a similar skill profile with your selected role.</div>", unsafe_allow_html=True)

# Path to the minimal mapping file created by the offline script. Prefer the minimal gzip file for the app.
CLUSTER_MAPPING_PATH = "data/processed/job_clusters_minimal.pkl.gz"

@st.cache_resource
def load_cluster_analyzer(path: str = CLUSTER_MAPPING_PATH):
    try:
        return ClusterAnalyzer(path)
    except Exception as e:
        # If loading fails, return None and the UI will show an informational message
        st.session_state._cluster_load_error = str(e)
        return None

analyzer = load_cluster_analyzer()

selected_similar_displayed = False
selected_job = st.session_state.get('selected_job')
if analyzer is None:
    st.caption("Similar opportunities are available but the cluster mapping could not be loaded.")
    err = st.session_state.get('_cluster_load_error')
    if err:
        st.text(f"Cluster load error: {err}")
    st.info("You can still view job details above. To enable similar job recommendations, provide a compact `job_clusters_minimal.pkl.gz` mapping in `data/processed`.")
else:
    if selected_job:
        # Determine a job id/key for lookup - common columns are 'job_key' or 'job_id'
        job_key = None
        for candidate in ('job_key', 'job_id', 'jobKey', 'id'):
            if isinstance(selected_job, dict) and candidate in selected_job:
                job_key = selected_job.get(candidate)
                break

        if job_key is None:
            st.info("Selected job does not contain an identifier ('job_key' or 'job_id') required for similar-job lookup.")
        else:
            similar = analyzer.get_similar_jobs(job_key, top_n=8)
            if similar.empty:
                st.info("No similar jobs found in the cluster mapping.")
            else:
                # Try to enrich with the in-memory `jobs_df` sample if available
                display_df = similar.copy()
                try:
                    if 'job_key' in globals().get('jobs_df', pd.DataFrame()).columns:
                        meta = jobs_df[['job_key', 'job_title', 'company', 'location']].copy()
                        meta['job_key'] = meta['job_key'].astype(str)
                        display_df = display_df.merge(meta, left_on='job_id', right_on='job_key', how='left')
                        display_df = display_df[['job_id', 'job_title', 'company', 'location', 'cluster_id']]
                    elif 'job_id' in globals().get('jobs_df', pd.DataFrame()).columns:
                        meta = jobs_df[['job_id', 'job_title', 'company', 'location']].copy()
                        meta['job_id'] = meta['job_id'].astype(str)
                        display_df = display_df.merge(meta, on='job_id', how='left')
                    else:
                        # No metadata available in the sampled jobs_df; keep minimal
                        pass
                except Exception:
                    # If enriching fails, fall back to minimal display
                    pass

                # Render as styled cards in a responsive grid rather than a raw dataframe
                try:
                    disp = display_df.reset_index(drop=True)
                    num = len(disp)
                    if num == 0:
                        st.info("No similar jobs found in the mapping.")
                    else:
                        # Show first 4 by default
                        show_more = st.session_state.get('show_more_similar', False)
                        limit = 8 if show_more else 4
                        disp_subset = disp.head(limit)
                        
                        cols_count = min(4, num)
                        cols = st.columns(cols_count)
                        for i, row in disp_subset.iterrows():
                            col = cols[i % cols_count]
                            title = row.get('job_title') if pd.notna(row.get('job_title')) else 'Untitled'
                            company = row.get('company') if pd.notna(row.get('company')) else 'N/A'
                            location = row.get('location') if pd.notna(row.get('location')) else 'N/A'
                            cluster_badge = row.get('cluster_id')
                            col.markdown(f"""
                                <div style="background: {colors['bg_secondary']}; border-radius: 10px; padding: 12px; margin: 6px; border-left: 4px solid {colors['accent_primary']};">
                                    <div style="font-weight: 700; color: {colors['text_primary']}; margin-bottom: 8px;">{title}</div>
                                    <div style="color: {colors['text_secondary']}; font-size:0.9rem; margin-bottom: 8px;">{company} • {location}</div>
                                    <div style="background: {colors['accent_secondary']}; color: white; padding: 3px 8px; border-radius: 12px; font-size:0.8rem; display:inline-block;">Cluster {cluster_badge}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Show more button if there are additional jobs
                        if num > 4 and not show_more:
                            if st.button("Show more similar jobs", key="show_more_btn"):
                                st.session_state.show_more_similar = True
                                st.rerun()
                        elif show_more and num > 4:
                            if st.button("Show fewer similar jobs", key="show_fewer_btn"):
                                st.session_state.show_more_similar = False
                                st.rerun()
                except Exception:
                    # Fallback to simple table if anything goes wrong
                    st.dataframe(display_df.reset_index(drop=True))
                selected_similar_displayed = True
    else:
        st.info("Select a target job above to see similar opportunities.")

# Footer
st.divider()
st.markdown("""
<div style="
    text-align: center;
    padding: 2rem 0;
    color: {colors['text_secondary']};
    font-size: 0.9rem;
">
    <p style="margin: 0.5rem 0;">
        <strong style="color: {colors['accent_primary']};">🚀 Skills Gap Analyzer</strong> — AI-Powered Career Development Platform
    </p>
    <p style="margin: 0.5rem 0;">
        Built with Machine Learning (Association Rules & K-Means Clustering)
    </p>
    <p style="margin: 0.5rem 0; font-size: 0.85rem;">
        © 2025 | <a href="https://github.com/sarrazer24/skills-gap-analyzer" style="color: {colors['accent_primary']}; text-decoration: none;">GitHub Repository</a>
    </p>
</div>
""", unsafe_allow_html=True)
