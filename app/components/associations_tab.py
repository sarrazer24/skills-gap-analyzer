# components/associations_tab.py
import streamlit as st
from data.sample_data import SKILL_ASSOCIATIONS

def render_associations_tab(user_data):
    """Render the skill associations tab"""
    st.markdown("### Skill Dependencies & Market Insights")
    st.markdown("Understanding how skills connect and complement each other in the job market")
    
    # Create columns for associations
    cols = st.columns(2)
    col_idx = 0
    
    required_skills = st.session_state.get('required_skills', [])
    current_skills = st.session_state.get('current_skills', [])
    
    for skill, data in SKILL_ASSOCIATIONS.items():
        if skill in required_skills:
            with cols[col_idx]:
                render_skill_association_card(skill, data, current_skills)
            col_idx = (col_idx + 1) % 2
    
    # Market insights
    render_market_insights()

def render_skill_association_card(skill, data, current_skills):
    """Render individual skill association card"""
    with st.container():
        st.markdown(f"""
        <div class="custom-card">
            <h4>{skill}</h4>
            <div style='padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                <p><strong>Foundation Skills:</strong></p>
        """, unsafe_allow_html=True)
        
        for req_skill in data["requires"]:
            status = "✓" if req_skill in current_skills else "○"
            st.markdown(f"- {status} **{req_skill}**")
        
        st.markdown(f"""
            </div>
            <div style='display: flex; justify-content: space-between; margin-top: 1rem;'>
                <span>Confidence: <strong>{data['confidence']*100:.0f}%</strong></span>
                <span>Demand: <strong>{data['market_demand']}</strong></span>
                <span>Salary: <strong>{data['avg_salary_boost']}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_market_insights():
    """Render market trends and insights"""
    st.markdown("### Market Trends")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h4>High-Demand Skills</h4>
            <p>• Python + Machine Learning</p>
            <p>• AWS + Docker + Kubernetes</p>
            <p>• React + Node.js + TypeScript</p>
            <p><em>Combining these skills increases market value</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h4>Learning Strategy</h4>
            <p>• Master foundations first</p>
            <p>• Build projects combining skills</p>
            <p>• Focus on in-demand combinations</p>
            <p><em>Practical experience is key</em></p>
        </div>
        """, unsafe_allow_html=True)