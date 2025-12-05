# app.py
import streamlit as st

# Import modular components
from components.header import render_header
from components.sidebar import render_sidebar
from components.skills_tab import render_skills_tab
from components.associations_tab import render_associations_tab
from components.gap_analysis_tab import render_gap_analysis_tab
from components.learning_path_tab import render_learning_path_tab
from utils.styling import apply_custom_styles

def main():
    # Apply custom styling
    apply_custom_styles()
    
    # Page configuration
    st.set_page_config(
        page_title="Job Skills Gap Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Render header
    render_header()
    
    # Render sidebar and get user inputs
    user_data = render_sidebar()
    
    # Main content based on analysis state
    if user_data.get('analyzed', False):
        render_analysis_tabs(user_data)
    else:
        render_welcome_screen()

def render_analysis_tabs(user_data):
    """Render the main analysis tabs"""
    tab1, tab2, tab3, tab4 = st.tabs([
        "Required Skills", 
        "Skill Associations", 
        "Gap Analysis", 
        "Learning Path"
    ])
    
    with tab1:
        render_skills_tab(user_data)
    
    with tab2:
        render_associations_tab(user_data)
    
    with tab3:
        render_gap_analysis_tab(user_data)
    
    with tab4:
        render_learning_path_tab(user_data)

def render_welcome_screen():
    """Render the welcome screen when no analysis is done"""
    from data.sample_data import render_welcome_content
    render_welcome_content()

if __name__ == "__main__":
    main()