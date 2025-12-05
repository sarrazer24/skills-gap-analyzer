# components/gap_analysis_tab.py
import streamlit as st
import pandas as pd
import plotly.express as px
from config.constants import PRIORITY_LEVELS

def render_gap_analysis_tab(user_data):
    """Render the gap analysis tab"""
    st.markdown("### Detailed Gap Analysis")
    
    current_skills = st.session_state.get('current_skills', [])
    required_skills = st.session_state.get('required_skills', [])
    
    # Summary metrics
    render_summary_metrics(current_skills, required_skills)
    
    # Side-by-side comparison
    render_skills_comparison(current_skills, required_skills)
    
    # Learning difficulty visualization
    render_learning_difficulty(current_skills, required_skills)

def render_summary_metrics(current_skills, required_skills):
    """Render summary metrics and progress"""
    matched_skills = set(current_skills) & set(required_skills)
    missing_skills = set(required_skills) - set(current_skills)
    progress_pct = len(matched_skills) / len(required_skills)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Required", len(required_skills))
    with col2:
        st.metric("Your Skills", len(matched_skills))
    with col3:
        st.metric("To Learn", len(missing_skills))
    with col4:
        st.metric("Readiness", f"{progress_pct*100:.1f}%")
    
    # Progress bar
    st.progress(progress_pct, text=f"Career Readiness: {progress_pct*100:.1f}%")

def render_skills_comparison(current_skills, required_skills):
    """Render side-by-side skills comparison"""
    matched_skills = set(current_skills) & set(required_skills)
    missing_skills = set(required_skills) - set(current_skills)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h3>Skills You Have</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if matched_skills:
            for skill in sorted(matched_skills):
                st.markdown(f"""
                <div style='background: var(--background-color); padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #10b981;'>
                    <div style='display: flex; justify-content: between; align-items: center;'>
                        <span style='font-weight: 600;'>{skill}</span>
                        <span style='background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8em;'>Owned</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matching skills yet. Start building your skill set!")
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h3>Skills to Learn</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if missing_skills:
            for i, skill in enumerate(sorted(missing_skills)):
                priority = "High" if i < 3 else "Medium" if i < 6 else "Low"
                priority_color = PRIORITY_LEVELS[priority]
                
                st.markdown(f"""
                <div style='background: var(--background-color); padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid {priority_color};'>
                    <div style='display: flex; justify-content: between; align-items: center;'>
                        <span style='font-weight: 600;'>{skill}</span>
                        <span style='background: {priority_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8em;'>{priority} Priority</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Amazing! You have all the required skills for this role!")

def render_learning_difficulty(current_skills, required_skills):
    """Render learning difficulty visualization"""
    missing_skills = list(set(required_skills) - set(current_skills))
    
    if missing_skills:
        st.markdown("### Learning Effort Estimation")
        
        difficulty_data = pd.DataFrame({
            "Skill": missing_skills[:6],
            "Difficulty Level": ["Beginner", "Intermediate", "Advanced", "Intermediate", "Beginner", "Advanced"][:len(missing_skills)],
            "Estimated Hours": [20, 40, 80, 35, 25, 100][:len(missing_skills)],
            "Priority": ["High", "High", "Medium", "Medium", "Low", "Low"][:len(missing_skills)]
        })
        
        fig = px.bar(
            difficulty_data,
            x="Skill",
            y="Estimated Hours",
            color="Difficulty Level",
            color_discrete_map={
                "Beginner": "#10b981",
                "Intermediate": "#f59e0b", 
                "Advanced": "#ef4444"
            },
            title="Estimated Learning Time per Skill"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)