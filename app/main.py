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
"""Professional Tech-Focused UI with Light/Dark Mode Support"""

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
</style>
""", unsafe_allow_html=True)

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
        <div style="
            margin: 1.5rem auto;
            width: 120px;
            height: 4px;
            background: linear-gradient(90deg, {colors['accent_primary']}, {colors['accent_secondary']}, {colors['accent_tertiary']});
            border-radius: 2px;
        "></div>
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
# SECTION 1: USER INPUT
# ====================
st.markdown(f"""
<div style="margin-top: 2rem;">
    <h2 style="
        color: {colors['text_primary']};
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 2px solid {colors['accent_primary']};
        padding-bottom: 12px;
    "><span style="font-size: 1.75rem;">1️⃣</span> Build Your Profile</h2>
</div>
""", unsafe_allow_html=True)

# Create columns for layout
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="
        background: {colors['card_gradient']};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {colors['border']};
    ">
        <h3 style="
            color: {colors['text_primary']};
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        "><span style="font-size: 1.5rem;">📊</span> Your Technical Skills</h3>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown(f"""
    <div style="
        background: {colors['card_gradient']};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {colors['border']};
    ">
        <h3 style="
            color: {colors['text_primary']};
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        "><span style="font-size: 1.5rem;">🎯</span> Target Job Role</h3>
    </div>
    """, unsafe_allow_html=True)
    
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
        if 'user_skills' not in st.session_state:
            st.session_state.user_skills = []

        if st.session_state.user_skills:
            try:
                from src.models.cluster_analyzer import ClusterAnalyzer

                # Prefer app/models, fallback to data/processed
                model_path = locate_model_file([
                    os.path.join('app', 'models', 'clustering_model.pkl'),
                    os.path.join('data', 'processed', 'clustering_model.pkl'),
                    os.path.join('data', 'processed', 'clustering_results_kmeans.pkl'),
                ])
                if model_path:
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
            <div style="
                background: linear-gradient(135deg, {colors['warning']} 0%, rgba(245, 158, 11, 0.1) 100%);
                border-radius: 12px;
                padding: 14px;
                margin: 1rem 0;
                border-left: 4px solid {colors['warning']};
            ">
                <p style="margin: 0; font-weight: 600; color: {colors['text_primary']};">
                💡 <strong>{len(recommended_jobs_info)} Job Matches Found</strong> — Based on your skills
                </p>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View personalized job matches", expanded=False):
                for i, rec in enumerate(recommended_jobs_info, 1):
                    match_color = "{colors['success']}" if rec['match'] >= 75 else "{colors['warning']}" if rec['match'] >= 50 else "{colors['error']}"
                    st.markdown(f"""
                    <div style="
                        padding: 12px;
                        background: {colors['bg_secondary']};
                        border-radius: 8px;
                        margin: 0.5rem 0;
                        border-left: 3px solid {match_color};
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: {colors['text_primary']};">{i}. {rec['title']}</strong>
                            <span style="background: {match_color}; color: white; padding: 4px 10px; border-radius: 16px; font-weight: 600; font-size: 0.85rem;">{rec['match']:.1f}% match</span>
                        </div>
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
# SECTION 2: GAP ANALYSIS
# ====================
if st.session_state.user_skills and st.session_state.selected_job:
    st.markdown(f"""
    <hr style="margin: 2rem 0; border: none; border-top: 2px solid {colors['border']};">
    <h2 style="
        color: {colors['text_primary']};
        font-size: 1.5rem;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 2px solid {colors['accent_primary']};
        padding-bottom: 12px;
    "><span style="font-size: 1.75rem;">2️⃣</span> Skill Gap Analysis</h2>
    """, unsafe_allow_html=True)
    
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
    
    # Detailed breakdown in tabs
    tab1, tab2, tab3 = st.tabs(["✅ Your Matching Skills", "❌ Skills You Need", "📊 Additional Skills You Have"])

    # Theme-aware card colors (light vs dark mode)
    if st.session_state.get('theme', 'dark') == 'dark':
        critical_bg = '#fee2e2'
        critical_border = '#dc2626'
        critical_title = '#4b0000'
        critical_sub = '#6b0000'

        med_bg = '#fef3c7'
        med_border = '#f59e0b'
        med_title = '#5a3c0a'
        med_sub = '#6b4608'

        low_bg = '#dcfce7'
        low_border = '#22c55e'
        low_title = '#0a4e1a'
        low_sub = '#0a4e1a'

        match_bg = '#dcfce7'
        match_border = '#22c55e'
        match_title = '#0a4e1a'

        extra_bg = '#e0e7ff'
        extra_title = '#1e1b4b'
    else:
        # Light mode: use slightly darker accents for readability on light backgrounds
        critical_bg = '#fee2e2'
        critical_border = '#dc2626'
        critical_title = '#7f1d1d'
        critical_sub = '#991b1b'

        med_bg = '#fef3c7'
        med_border = '#f59e0b'
        med_title = '#78350f'
        med_sub = '#92400e'

        low_bg = '#dcfce7'
        low_border = '#22c55e'
        low_title = '#15803d'
        low_sub = '#166534'

        match_bg = '#dcfce7'
        match_border = '#22c55e'
        match_title = '#15803d'

        extra_bg = '#e0e7ff'
        extra_title = '#312e81'
    
    with tab1:
        st.markdown("### Skills that match the job requirements")
        if matching:
            st.markdown(f"**You have {len(matching)} matching skills:**")
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(matching)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: {match_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid {match_border};">
                        <div style="font-weight: 600; color: {match_title} !important;">✓ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No matching skills found. You'll need to learn the required skills.")
    
    with tab2:
        st.markdown("### Skills required for the job that you don't have")
        if missing:
            # Use SkillMatcher for optimized gap analysis
            from src.models.skill_matcher import SkillMatcher
            from src.data.loader import DataLoader
            
            try:
                # Build skill-to-category mapping
                loader = DataLoader()
                skill_to_cat_map = loader.get_skill_to_category_map()
                matcher = SkillMatcher(skill_to_cat_map)
                
                # Get prioritized missing skills
                gap_analysis = matcher.analyze_gap(
                    list(user_set),
                    list(job_set)
                )
                
                st.markdown(f"**You need to learn {len(missing)} skills:**")
                
                # Show learning time estimate
                learning_estimate = matcher.estimate_learning_time(gap_analysis['missing'])
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Skills", len(missing))
                with col2:
                    st.metric("Est. Hours", f"{learning_estimate['total_hours']:.0f}h")
                with col3:
                    st.metric("Est. Weeks", f"{learning_estimate['total_weeks']:.1f}w")
                with col4:
                    st.metric("Est. Months", f"{learning_estimate['total_months']:.1f}m")
                
                # Display missing skills organized by priority
                missing_sorted = sorted(missing)
                
                # Split into priority tiers
                third = len(missing_sorted) // 3
                high_priority = missing_sorted[:third] if third > 0 else missing_sorted
                med_priority = missing_sorted[third:third*2] if third > 0 else []
                low_priority = missing_sorted[third*2:] if third > 0 else []
                
                if high_priority:
                    st.markdown("#### 🔴 Critical - Must Learn First")
                    cols = st.columns(4)
                    for idx, skill in enumerate(high_priority):
                        with cols[idx % 4]:
                            category = skill_to_cat_map.get(skill, 'general')
                            st.markdown(f"""
                            <div style="background: {critical_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {critical_border}; margin-bottom: 10px;">
                                <div style="font-weight: 600; color: {critical_title} !important;">{skill.title()}</div>
                                <div style="font-size: 0.8rem; color: {critical_sub} !important; margin-top: 6px;">{category.replace('_', ' ').title()}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                if med_priority:
                    st.markdown("#### 🟡 Important - Should Learn After Critical")
                    cols = st.columns(4)
                    for idx, skill in enumerate(med_priority):
                        with cols[idx % 4]:
                            category = skill_to_cat_map.get(skill, 'general')
                            st.markdown(f"""
                            <div style="background: {med_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {med_border}; margin-bottom: 10px;">
                                <div style="font-weight: 600; color: {med_title} !important;">{skill.title()}</div>
                                <div style="font-size: 0.8rem; color: {med_sub} !important; margin-top: 6px;">{category.replace('_', ' ').title()}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                if low_priority:
                    st.markdown("#### 🟢 Nice to Have - Learn if Time Permits")
                    cols = st.columns(4)
                    for idx, skill in enumerate(low_priority):
                        with cols[idx % 4]:
                            category = skill_to_cat_map.get(skill, 'general')
                            st.markdown(f"""
                            <div style="background: {low_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {low_border}; margin-bottom: 10px;">
                                <div style="font-weight: 600; color: {low_title} !important;">{skill.title()}</div>
                                <div style="font-size: 0.8rem; color: {low_sub} !important; margin-top: 6px;">{category.replace('_', ' ').title()}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show suggested learning path
                with st.expander("📚 View Suggested Learning Path", expanded=False):
                    st.markdown("**Learn in this order for best results:**")
                    phases = matcher.get_learning_path(missing_sorted, max_skills_per_phase=3)
                    for phase_idx, phase in enumerate(phases[:5], 1):  # Show first 5 phases
                        phase_str = ", ".join(s.title() for s in phase)
                        st.write(f"**Phase {phase_idx}:** {phase_str}")
                
            except Exception as e:
                # Fallback: simple list display
                st.markdown(f"**Missing Skills ({len(missing)}):**")
                cols = st.columns(4)
                for idx, skill in enumerate(sorted(missing)):
                    with cols[idx % 4]:
                        st.markdown(f"""
                        <div style="background: #fee2e2; border-radius: 8px; padding: 10px; border-left: 3px solid #dc2626;">
                            <div style="font-weight: 600; color: #7f1d1d;">✗ {skill.title()}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.success("🎉 Excellent! You have all the required skills for this job!")
    
    with tab3:
        st.markdown("### Additional skills you have (not required for this job)")
        if extra:
            st.markdown(f"**You have {len(extra)} extra skills:**")
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(extra)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: #e0e7ff; border-radius: 8px; padding: 10px; border-left: 3px solid #6366f1;">
                        <div style="font-weight: 600; color: #1e1b4b !important;">+ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No additional skills beyond what's required.")
    
    # ====================
    # SECTION 3: RECOMMENDATIONS
    # ====================
    st.markdown(f"""
    <hr style="margin: 2rem 0; border: none; border-top: 2px solid {colors['border']};">
    <h2 style="
        color: {colors['text_primary']};
        font-size: 1.5rem;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 2px solid {colors['accent_primary']};
        padding-bottom: 12px;
    "><span style="font-size: 1.75rem;">3️⃣</span> Personalized Learning Path</h2>
    """, unsafe_allow_html=True)
    
    # Model Selector
    if recommender_available:
        model_choice = st.radio(
            "Select Recommendation Type:",
            [
                "A1: 🎯 Specific Skills (What to learn)",
                "A2: 🗺️  Career Coaching (How to advance)",
                "A3: 📊 Comprehensive Analysis (Full profile)"
            ],
            horizontal=True,
            help="A1: Quick skill recommendations | A2: Career guidance | A3: Deep analysis"
        )
        # Import recommender models
        try:
            from src.models.recommender import ModelA1Recommender, ModelA2Recommender, ModelA3Recommender
            recommender_imported = True
        except ImportError:
            recommender_imported = False
            st.warning("⚠️ Recommender models not available. Using basic recommendations.")
    else:
        st.info("Recommender models not available — showing basic learning path and fallbacks.")
        model_choice = "Fallback"
        recommender_imported = False
    
    if missing:
        # Model-specific recommendation logic
        if "A1" in model_choice and recommender_imported:
            # ===== MODEL A1: Specific Skills =====
            with st.spinner("🎯 Generating skill recommendations..."):
                try:
                    a1_recommender = ModelA1Recommender()
                    
                    # Get all skills from jobs for popularity scoring
                    all_job_skills = []
                    for skills in jobs_df['skill_list']:
                        if isinstance(skills, list):
                            all_job_skills.extend(skills)
                        elif isinstance(skills, str):
                            import ast
                            try:
                                skills_list = ast.literal_eval(skills)
                                if isinstance(skills_list, list):
                                    all_job_skills.extend(skills_list)
                            except:
                                pass
                    
                    a1_recs = a1_recommender.get_recommendations(
                        user_skills=user_skills,
                        missing_skills=list(missing) if isinstance(missing, set) else missing,
                        all_job_skills=all_job_skills,
                        top_n=10
                    )
                    
                    if not a1_recs.empty:
                        st.markdown("""
                        <div style="
                            background: linear-gradient(135deg, #3B82F6 0%, rgba(59, 130, 246, 0.1) 100%);
                            border-radius: 12px;
                            padding: 16px;
                            border-left: 4px solid #3B82F6;
                            margin: 1.5rem 0;
                        ">
                            <p style="margin: 0; color: {colors['text_primary']}; font-weight: 600;">
                            🎯 Top Skills To Learn (Ranked by Importance)
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for idx, (_, rec) in enumerate(a1_recs.iterrows(), 1):
                            with st.expander(f"{idx}. **{rec['skill']}** - Priority {rec['priority']}/10"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Difficulty", rec['difficulty'])
                                with col2:
                                    st.metric("Time", f"{rec['estimated_weeks']} weeks")
                                with col3:
                                    st.metric("Success Rate", f"{rec['success_rate']:.0f}%")
                                
                                st.write(f"**Why learn this?** {rec['reason']}")
                                st.write(f"**📚 Recommended Courses:** {rec['courses']}")
                    else:
                        st.info("💡 No specific skill recommendations available at this time.")
                
                except Exception as e:
                    st.error(f"❌ Error generating A1 recommendations: {str(e)}")
        
        elif "A2" in model_choice and recommender_imported:
            # ===== MODEL A2: Career Coaching =====
            with st.spinner("🗺️  Generating career roadmap..."):
                try:
                    a2_recommender = ModelA2Recommender(jobs_df, skills_df)
                    
                    # Get user context
                    years_exp = st.number_input("Years of experience:", 0, 50, 3, key="a2_years")
                    target_for_a2 = st.selectbox(
                        "Target career role:",
                        unique_job_titles[:15] if unique_job_titles else ["Data Scientist", "Senior Engineer", "ML Engineer"],
                        key="a2_target"
                    )
                    
                    if st.button("Generate Career Roadmap", key="gen_roadmap"):
                        # Assess career stage
                        stage_info = a2_recommender.assess_career_stage(years_exp, user_skills)
                        
                        # Analyze market
                        market = a2_recommender.analyze_career_market(target_for_a2)
                        
                        # Generate progression
                        progression = a2_recommender.generate_progression_path(
                            "Current Role",
                            user_skills,
                            target_for_a2,
                            years_horizon=3
                        )
                        
                        # Generate coaching
                        coaching = a2_recommender.provide_coaching(
                            stage_info['stage'],
                            years_exp,
                            target_for_a2,
                            progression,
                            market
                        )
                        
                        st.markdown(coaching)
                
                except Exception as e:
                    st.error(f"❌ Error generating A2 roadmap: {str(e)}")
        
        elif "A3" in model_choice and recommender_imported:
            # ===== MODEL A3: Comprehensive Analysis =====
            with st.spinner("📊 Generating comprehensive analysis..."):
                try:
                    from src.models.cluster_analyzer import ClusterAnalyzer
                    
                    # Try to load cluster analyzer
                    cluster_model = None
                    try:
                        if os.path.exists('app/models/clustering_model.pkl'):
                            cluster_model = ClusterAnalyzer.load('app/models/clustering_model.pkl')
                    except:
                        pass
                    
                    a3_recommender = ModelA3Recommender(jobs_df, skills_df, cluster_model)
                    
                    # Get user context for A3
                    years_exp_a3 = st.number_input("Years of experience:", 0, 50, 3, key="a3_years")
                    target_for_a3 = st.selectbox(
                        "Target career role:",
                        unique_job_titles[:15] if unique_job_titles else ["Data Scientist", "Senior Engineer", "ML Engineer"],
                        key="a3_target"
                    )
                    
                    if st.button("Generate Full Analysis", key="gen_a3"):
                        # Generate comprehensive report
                        report = a3_recommender.comprehensive_report(
                            user_profile={'skills': user_skills},
                            years_experience=years_exp_a3,
                            target_role=target_for_a3
                        )
                        
                        # Display tabs
                        tab_summary, tab_skills, tab_paths, tab_clusters = st.tabs(
                            ["📊 Summary", "🎯 A1 Skills", "🗺️  A2 Paths", "📈 A3 Clusters"]
                        )
                        
                        with tab_summary:
                            st.markdown(report['executive_summary'])
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Career Stage", report['career_stage']['stage'])
                            with col2:
                                st.metric("Opportunity Score", f"{report['opportunity_score']:.1f}/10")
                            with col3:
                                st.metric("Success Probability", f"{report['success_probability']:.0%}")
                        
                        with tab_skills:
                            st.subheader("🎯 Immediate Skill Recommendations (A1)")
                            if report['immediate_recommendations']:
                                for idx, rec in enumerate(report['immediate_recommendations'][:5], 1):
                                    st.write(f"**{idx}. {rec.get('skill', 'N/A')}** (Priority: {rec.get('priority', 'N/A')}/10)")
                            else:
                                st.info("No A1 recommendations available.")
                        
                        with tab_paths:
                            st.subheader("🗺️  Career Progression Paths (A2)")
                            for path in report['alternative_paths'][:3]:
                                with st.expander(f"{path['target_role']} ({path['success_probability']:.0%} success)"):
                                    st.write(f"**Timeline:** {path['estimated_timeline_months']} months")
                                    st.write(f"**New Skills Needed:** {path['total_new_skills']}")
                                    st.write(f"**Difficulty:** {path['difficulty_level']}")
                                    st.write(f"**Estimated Salary:** ${path['estimated_salary']:,.0f}")
                        
                        with tab_clusters:
                            st.subheader("📈 Skill Cluster Analysis (A3)")
                            clusters = report['skill_clusters']
                            st.write(f"**Primary Clusters:** {', '.join(clusters.get('primary_clusters', []))}")
                            st.write(f"**Secondary Clusters:** {', '.join(clusters.get('secondary_clusters', []))}")
                            
                            st.write("**Peer Group Analysis:**")
                            peer = report['peer_analysis']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Your Percentile", f"{peer['percentile']:.0f}th")
                            with col2:
                                st.metric("Success Rate", f"{peer['success_rate']:.0%}")
                            with col3:
                                st.metric("Avg Salary", f"${peer['average_salary']:,.0f}")
                
                except Exception as e:
                    st.error(f"❌ Error generating A3 analysis: {str(e)}")
        
        else:
            # ===== FALLBACK: Original Learning Path =====
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, {colors['warning']} 0%, rgba(255, 193, 7, 0.1) 100%);
                border-radius: 12px;
                padding: 16px;
                border-left: 4px solid {colors['warning']};
                margin: 1.5rem 0;
            ">
                <p style="margin: 0; color: {colors['text_primary']}; font-weight: 600;">
                ⚡ Smart Learning Order: Skills ranked by priority and dependencies
                </p>
            </div>
            """, unsafe_allow_html=True)
        
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
        st.markdown("""
        <div style="margin-top: 2rem;">
            <h3 style="
                color: {colors['text_primary']};
                font-size: 1.25rem;
                margin: 1rem 0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            "><span style="font-size: 1.5rem;">📚</span> Recommended Skills to Learn</h3>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            from src.models.association_miner import AssociationEnsemble

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

            if found_paths:
                ensemble = AssociationEnsemble()
                ensemble.load_paths(found_paths)

                # Map user skills to categories when possible
                try:
                    dl = DataLoader()
                    skills_tax = dl.load_skills_taxonomy()
                    skill_to_cat = {}
                    if isinstance(skills_tax, pd.DataFrame) and 'skill_group_name' in skills_tax.columns and 'skill_group_category' in skills_tax.columns:
                        for _, r in skills_tax.iterrows():
                            name = str(r['skill_group_name']).lower().strip()
                            cat = str(r['skill_group_category']).lower().strip()
                            if name:
                                skill_to_cat[name] = cat
                    user_items = []
                    for s in st.session_state.user_skills:
                        mapped = skill_to_cat.get(s.lower().strip())
                        if mapped:
                            user_items.append(mapped)
                    if not user_items:
                        user_items = st.session_state.user_skills
                except Exception:
                    user_items = st.session_state.user_skills

                recommendations = ensemble.get_recommendations(user_items, top_n=5)

                if recommendations is not None and not recommendations.empty:
                    st.markdown("### 📚 Based on Association Rules (ensemble), you should also consider learning:")
                    for idx, (_, row) in enumerate(recommendations.iterrows(), 1):
                        skill_name = row['skill'].title()
                        score_pct = float(row.get('score', 0.0)) * 100
                        sources = row.get('sources', '')
                        context_line = f"💡 Combined score {score_pct:.0f}% — sources: {sources}"
                        st.markdown(f"**{idx}. {skill_name}**\n\n{context_line}\n*(From combined association models)*")
                else:
                    # fallback to A1 as before
                    handled = False
                    try:
                        # Try A1 explicitly
                        model_path_a1 = locate_model_file([
                            os.path.join('app', 'models', 'association_rules_a1.pkl'),
                            os.path.join('data', 'processed', 'association_rules_a1.pkl'),
                        ])
                        if model_path_a1:
                            from src.models.association_miner import AssociationMiner
                            miner_a1 = AssociationMiner.load(model_path_a1)
                            recs_a1 = miner_a1.get_recommendations([s.lower().strip() for s in st.session_state.user_skills], top_n=6)
                            if recs_a1 is not None and not recs_a1.empty:
                                st.markdown("### 🔁 Skill-level suggestions (A1 fallback)")
                                for idx, (_, row) in enumerate(recs_a1.iterrows(), 1):
                                    skill_name = row['skill'].title()
                                    confidence_pct = row.get('confidence', 0) * 100
                                    st.markdown(f"**{idx}. {skill_name}** — {confidence_pct:.0f}% confidence (from skill-level rules)")
                                handled = True
                    except Exception:
                        handled = False

                    if not handled and st.session_state.user_skills:
                        # Existing job-description overlap fallback
                        try:
                            user_set_lower = set(s.lower().strip() for s in st.session_state.user_skills)
                            overlap_counts = {}
                            for _, jrow in jobs_df.iterrows():
                                jskills = jrow.get('skill_list', [])
                                if isinstance(jskills, str):
                                    import ast as _ast
                                    try:
                                        jskills = _ast.literal_eval(jskills)
                                    except:
                                        jskills = [s.strip() for s in jskills.split(',') if s.strip()]
                                if not isinstance(jskills, list):
                                    continue
                                jset = set(s.lower().strip() for s in jskills if s and str(s).strip())
                                if user_set_lower & jset:
                                    for sk in jset:
                                        if sk in user_set_lower:
                                            continue
                                        overlap_counts[sk] = overlap_counts.get(sk, 0) + 1

                            if overlap_counts:
                                top_skills = sorted(overlap_counts.items(), key=lambda x: x[1], reverse=True)[:6]
                                skills_list = [s[0].title() for s in top_skills]
                                st.info("💡 No direct association-rule suggestions — falling back to common complementary skills from matching job descriptions:")
                                cols = st.columns(min(3, len(skills_list)))
                                for i, sk in enumerate(skills_list):
                                    with cols[i % 3]:
                                        st.success(sk)
                            else:
                                st.info("💡 No specific skill recommendations found for your skill combination yet. Try learning complementary skills from the job descriptions below.")
                        except Exception:
                            st.info("💡 No specific skill recommendations found for your skill combination yet. Try learning complementary skills from the job descriptions below.")
            else:
                st.info("💡 Association rules models not found. Run `python scripts/download_models.py` or place model artifacts in `app/models/` or `data/processed/`")
        except Exception as e:
            st.warning(f"Skill recommendations temporarily unavailable: {str(e)}")
        
        # Similar jobs from Clustering (all from same cluster)
        st.markdown("""
        <div style="margin-top: 2rem;">
            <h3 style="
                color: {colors['text_primary']};
                font-size: 1.25rem;
                margin: 1rem 0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            "><span style="font-size: 1.5rem;">💼</span> Similar Opportunities</h3>
        </div>
        """, unsafe_allow_html=True)
        
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
                        # Fallback: cluster column missing — compute simple similarity across all jobs
                        try:
                            user_set_lower = set(s.lower().strip() for s in st.session_state.user_skills)
                            # Compute similarity (overlap) across all jobs
                            similarity_list = []
                            for _, jrow in jobs_df.iterrows():
                                jskills = jrow.get('skill_list', [])
                                if isinstance(jskills, str):
                                    import ast as _ast
                                    try:
                                        jskills = _ast.literal_eval(jskills)
                                    except:
                                        jskills = [s.strip() for s in jskills.split(',') if s.strip()]
                                if not isinstance(jskills, list):
                                    continue
                                jset = set(s.lower().strip() for s in jskills if s and str(s).strip())
                                if not jset:
                                    continue
                                match_pct = len(user_set_lower & jset) / len(jset) * 100
                                similarity_list.append((match_pct, jrow))

                            # Sort and display top 3 similar jobs (excluding current job)
                            similarity_list.sort(key=lambda x: x[0], reverse=True)
                            top_similar = []
                            current_job_title = job.get('job_title', '')
                            for match_pct, jrow in similarity_list:
                                if current_job_title and jrow.get('job_title', '') == current_job_title:
                                    continue
                                top_similar.append((match_pct, jrow))
                                if len(top_similar) >= 3:
                                    break

                            if top_similar:
                                for idx, (match_pct, jrow) in enumerate(top_similar, 1):
                                    st.markdown(f"**{idx}. {jrow.get('job_title','Unknown Job')} - {jrow.get('company','N/A')}** ({match_pct:.0f}% match)\n\n📍 {jrow.get('location','N/A')}")
                            else:
                                st.info("No similar jobs found (fallback similarity check returned no matches).")
                        except Exception as e:
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
        <div style="
            background: linear-gradient(135deg, {colors['success']} 0%, rgba(16, 185, 129, 0.1) 100%);
            border-radius: 12px;
            padding: 2.5rem;
            text-align: center;
            border: 1px solid {colors['success']};
        ">
            <h2 style="color: {colors['success']}; margin: 0 0 1rem 0; font-size: 2rem;">🎉 Excellent Match!</h2>
            <p style="color: {colors['text_primary']}; font-size: 1.1rem; margin: 0; font-weight: 500;">You have all the required skills for this position.</p>
            <p style="color: {colors['text_secondary']}; font-size: 0.95rem; margin: 0.75rem 0 0 0;">Time to apply and land your next opportunity!</p>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        border: 1px solid {colors['border']};
        margin: 2rem 0;
    ">
        <h3 style="
            color: {colors['accent_primary']};
            font-size: 1.3rem;
            margin: 0 0 0.75rem 0;
        ">👈 Let's Get Started</h3>
        <p style="
            color: {colors['text_primary']};
            font-size: 1rem;
            margin: 0;
            line-height: 1.6;
        ">Select your technical skills above and choose a target job role to receive a personalized analysis and learning recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

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
        © 2024 | <a href="https://github.com/sarrazer24/skills-gap-analyzer" style="color: {colors['accent_primary']}; text-decoration: none;">GitHub Repository</a>
    </p>
</div>
""", unsafe_allow_html=True)
