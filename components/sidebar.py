# components/sidebar.py
import streamlit as st
from config.constants import ALL_SKILLS
from data.sample_data import SAMPLE_JOBS

def render_sidebar():
    """Render the sidebar and return user input data"""
    with st.sidebar:
        # Sidebar header
        render_sidebar_header()
        
        # Input method selection
        input_method, job_data = render_input_section()
        
        # Current skills input
        current_skills = render_skills_input()
        
        # Quick stats
        render_quick_stats(current_skills, job_data.get('required_skills', []))
        
        # Analyze button
        if st.button("Start Analysis", type="primary", use_container_width=True):
            return handle_analysis_click(current_skills, job_data.get('required_skills', []), job_data)
        
        return {
            'analyzed': st.session_state.get('analyzed', False),
            'current_skills': current_skills,
            'required_skills': job_data.get('required_skills', []),
            'job_data': job_data
        }

def render_sidebar_header():
    """Render sidebar header"""
    st.markdown("""
    <div class="custom-card">
        <h3 style='margin: 0;'>Get Started</h3>
        <p style='margin: 0.5rem 0 0 0;'>Analyze your skills in minutes</p>
    </div>
    """, unsafe_allow_html=True)

def render_input_section():
    """Render the input method section"""
    input_method = st.radio(
        "Choose Input Method",
        ["Sample Job", "Paste Description", "Upload CV"],
        help="Select how you want to provide job information"
    )
    
    st.markdown("---")
    
    if input_method == "Sample Job":
        return render_sample_job_input()
    elif input_method == "Paste Description":
        return render_paste_input()
    else:
        return render_upload_input()

def render_sample_job_input():
    """Render sample job input section"""
    selected_job = st.selectbox(
        "Select Job Role",
        list(SAMPLE_JOBS.keys()),
        help="Choose from pre-analyzed job roles"
    )
    job_data = SAMPLE_JOBS[selected_job]
    
    # Display job info card
    render_job_info_card(job_data)
    
    return "sample", job_data

def render_paste_input():
    """Render paste description input section"""
    job_description = st.text_area(
        "Paste Job Description",
        height=150,
        placeholder="Paste the complete job description here...",
        help="Our AI will extract required skills automatically"
    )
    required_skills = st.multiselect(
        "Select Required Skills",
        ALL_SKILLS,
        default=["Python", "SQL", "JavaScript"],
        help="Choose skills mentioned in the job description"
    )
    
    return "paste", {
        "description": job_description,
        "required_skills": required_skills,
        "experience_level": "Custom",
        "salary_range": "Varies",
        "demand_level": "Custom"
    }

def render_upload_input():
    """Render CV upload input section"""
    uploaded_file = st.file_uploader(
        "Upload Your CV/Resume",
        type=["pdf", "docx"],
        help="Supported formats: PDF, DOCX"
    )
    job_description = st.text_area(
        "Paste Target Job Description",
        height=150,
        placeholder="Paste the job you're targeting...",
        help="Compare your CV against this job description"
    )
    required_skills = st.multiselect(
        "Required Skills for Target Job",
        ALL_SKILLS,
        help="Select skills required for your target role"
    )
    
    return "upload", {
        "description": job_description,
        "required_skills": required_skills,
        "experience_level": "Custom",
        "salary_range": "Varies",
        "demand_level": "Custom",
        "uploaded_file": uploaded_file
    }

def render_job_info_card(job_data):
    """Render job information card"""
    st.markdown(f"""
    <div class="custom-card">
        <h4>Job Insights</h4>
        <p><strong>Level:</strong> {job_data['experience_level']}</p>
        <p><strong>Salary:</strong> {job_data['salary_range']}</p>
        <p><strong>Demand:</strong> {job_data['demand_level']}</p>
    </div>
    """, unsafe_allow_html=True)

def render_skills_input():
    """Render current skills input section"""
    st.markdown("### Your Current Skills")
    return st.multiselect(
        "Select skills you currently have:",
        ALL_SKILLS,
        default=["Python", "SQL", "Git"],
        help="Choose all skills you're comfortable with",
        label_visibility="collapsed"
    )

def render_quick_stats(current_skills, required_skills):
    """Render quick statistics"""
    st.markdown("---")
    
    matched_skills = len(set(current_skills) & set(required_skills))
    total_required = len(required_skills) if required_skills else 1
    match_percentage = (matched_skills / total_required * 100) if required_skills else 0
    
    st.markdown("### Quick Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Skills Matched", matched_skills)
    
    with col2:
        st.metric("Readiness Score", f"{match_percentage:.0f}%")

def handle_analysis_click(current_skills, required_skills, job_data):
    """Handle analyze button click"""
    if not required_skills:
        st.warning("Please select required skills to analyze.")
        return {'analyzed': False}
    elif not current_skills:
        st.warning("Please select your current skills.")
        return {'analyzed': False}
    else:
        st.session_state.analyzed = True
        st.session_state.current_skills = current_skills
        st.session_state.required_skills = required_skills
        st.session_state.job_data = job_data
        st.rerun()
        return {'analyzed': True}