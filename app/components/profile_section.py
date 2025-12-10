"""Section 1: Profile Building - skills input and job selection."""
import streamlit as st
import pandas as pd
from src.models.skill_extractor import SkillExtractor


def render_profile(
    jobs_df: pd.DataFrame,
    skills_df: pd.DataFrame,
    available_skills: list,
    colors: dict
) -> dict:
    """Render profile building section.
    
    Displays:
    - 3 ways to input skills: CV upload, text description, manual selection
    - Job selection dropdown with job details card
    
    Args:
        jobs_df: DataFrame with jobs data
        skills_df: DataFrame with skills taxonomy
        available_skills: List of valid skills
        colors: Color dictionary from get_colors()
        
    Returns:
        dict with 'user_skills' list and 'selected_job' dict (or empty dict)
    """
    st.divider()
    st.markdown("<h2 class='section-title'>1️⃣ Build Your Profile</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Add your skills and pick your target role.</div>",
        unsafe_allow_html=True
    )
    
    # Initialize session state if needed
    if 'user_skills' not in st.session_state:
        st.session_state.user_skills = []
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    
    # Input method tabs
    tab1, tab2, tab3 = st.tabs(["📄 Upload CV", "✍️ Describe Yourself", "✋ Pick from List"])
    
    with tab1:
        _render_cv_upload(colors)
    
    with tab2:
        _render_text_description(colors, available_skills)
    
    with tab3:
        _render_skill_selection(available_skills, colors)
    
    st.write("")
    
    # Job selection
    st.markdown("<h3 style='margin: 1.5rem 0 0.5rem 0;'>Select Your Target Role</h3>", unsafe_allow_html=True)
    job_names = [j for j in jobs_df['job_title'].unique() if pd.notna(j)]
    selected_job_name = st.selectbox("Choose a role:", job_names, key='job_select')
    
    if selected_job_name:
        job_row = jobs_df[jobs_df['job_title'] == selected_job_name].iloc[0]
        st.session_state.selected_job = job_row.to_dict()
        
        # Display job card
        _render_job_info_card(job_row, colors)
    
    return {
        'user_skills': st.session_state.user_skills,
        'selected_job': st.session_state.selected_job
    }


def _render_cv_upload(colors: dict) -> None:
    """Render CV upload interface.
    
    Args:
        colors: Color dictionary
    """
    st.markdown("Upload a PDF or text CV and we'll extract your skills.", help="Uses AI to parse your CV")
    uploaded_file = st.file_uploader("Choose a CV file", type=['pdf', 'txt'], key='cv_upload')
    
    if uploaded_file:
        try:
            if uploaded_file.type == 'application/pdf':
                text = uploaded_file.read().decode('utf-8', errors='ignore')
            else:
                text = uploaded_file.read().decode('utf-8')
            
            st.markdown(f"""
            <div style="background: {colors['bg_secondary']}; border-radius: 8px; padding: 12px; margin: 0.5rem 0;">
                <p style="margin: 0; font-size: 0.85rem; color: {colors['text_secondary']};">
                    📎 {uploaded_file.name} ({len(text)} chars)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Extract skills from CV"):
                with st.spinner("Extracting skills..."):
                    extractor = SkillExtractor()
                    try:
                        extracted = extractor.extract_from_text(text)
                        st.session_state.user_skills = list(set(st.session_state.user_skills + extracted))
                        st.success(f"Added {len(extracted)} skills!")
                    except Exception as e:
                        st.error(f"Extraction failed: {str(e)}")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")


def _render_text_description(colors: dict, available_skills: list) -> None:
    """Render text description interface.
    
    Args:
        colors: Color dictionary
        available_skills: List of valid skills for autocomplete
    """
    st.markdown("Describe your background and expertise.", help="Tell us about yourself")
    description = st.text_area(
        "Your background:",
        height=150,
        placeholder="E.g., I have 5 years of Python development, 2 years with Django...",
        key='desc_input'
    )
    
    if description and st.button("Extract from description"):
        with st.spinner("Analyzing..."):
            extractor = SkillExtractor()
            try:
                extracted = extractor.extract_from_text(description)
                st.session_state.user_skills = list(set(st.session_state.user_skills + extracted))
                st.success(f"Added {len(extracted)} skills!")
            except Exception as e:
                st.error(f"Extraction failed: {str(e)}")


def _render_skill_selection(available_skills: list, colors: dict) -> None:
    """Render manual skill selection multiselect.
    
    Args:
        available_skills: List of valid skills
        colors: Color dictionary
    """
    st.markdown("Pick skills from our database.", help="Browse and select skills")
    selected = st.multiselect(
        "Available skills:",
        available_skills,
        default=st.session_state.user_skills,
        key='manual_select'
    )
    
    st.session_state.user_skills = selected
    
    st.markdown(f"""
    <div style="background: {colors['accent_bg']}; border-radius: 8px; padding: 12px; margin-top: 1rem;">
        <p style="margin: 0; font-size: 0.9rem; color: {colors['text_primary']};">
            ✓ {len(selected)} skills selected
        </p>
    </div>
    """, unsafe_allow_html=True)


def _render_job_info_card(job_row: pd.Series, colors: dict) -> None:
    """Render job info card with title, company, salary, skills.
    
    Args:
        job_row: Pandas Series with job data
        colors: Color dictionary
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid {colors['accent_primary']};
        margin: 1rem 0;
    ">
        <h4 style="margin: 0 0 0.5rem 0; color: {colors['text_primary']};">
            {job_row.get('job_title', 'Job')}
        </h4>
        <p style="margin: 0.25rem 0; color: {colors['text_secondary']}; font-size: 0.9rem;">
            Company: <strong>{job_row.get('company', 'N/A')}</strong>
        </p>
        <p style="margin: 0.25rem 0; color: {colors['text_secondary']}; font-size: 0.9rem;">
            Salary: <strong>{job_row.get('salary_range', 'N/A')}</strong>
        </p>
        <p style="margin: 0.5rem 0 0 0; color: {colors['text_secondary']}; font-size: 0.85rem;">
            {job_row.get('description', '')[:200]}...
        </p>
    </div>
    """, unsafe_allow_html=True)
