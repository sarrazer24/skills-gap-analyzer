# components/learning_path_tab.py
import streamlit as st
import pandas as pd

def render_learning_path_tab(user_data):
    """Render the learning path tab"""
    current_skills = st.session_state.get('current_skills', [])
    required_skills = st.session_state.get('required_skills', [])
    missing_skills = list(set(required_skills) - set(current_skills))
    
    if not missing_skills:
        render_congratulations()
    else:
        render_learning_roadmap(missing_skills, current_skills, required_skills)
        render_career_impact(current_skills, required_skills)

def render_congratulations():
    """Render congratulations message when all skills are met"""
    st.success("""
    <div class="custom-card">
        <h2 style='text-align: center; color: #065f46;'>Congratulations!</h2>
        <p style='text-align: center; font-size: 1.2em; color: #065f46;'>You have all the required skills for this role!</p>
        <p style='text-align: center;'>Consider exploring advanced topics or adjacent technologies to further enhance your profile.</p>
    </div>
    """, unsafe_allow_html=True)

def render_learning_roadmap(missing_skills, current_skills, required_skills):
    """Render the learning roadmap"""
    st.markdown("### Your Personalized Learning Roadmap")
    st.markdown(f"""
    *Based on your skill gap of **{len(missing_skills)} skills**, estimated completion: **{len(missing_skills) * 2} - {len(missing_skills) * 4} weeks***
    """)
    
    # Create a timeline view
    skill_batches = [missing_skills[i:i+2] for i in range(0, len(missing_skills), 2)]
    
    for week_num, skill_batch in enumerate(skill_batches, 1):
        with st.expander(f"Week {week_num}: Focus on {', '.join(skill_batch)}", expanded=week_num == 1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                for skill in skill_batch:
                    render_skill_learning_plan(skill)
            
            with col2:
                render_weekly_timeline(week_num, len(skill_batch))
    
    if len(missing_skills) > len(skill_batches) * 2:
        st.markdown(f"... and {len(missing_skills) - len(skill_batches) * 2} more skills to learn")
    
    # Recommended learning order
    render_learning_order(missing_skills)

def render_skill_learning_plan(skill):
    """Render learning plan for a specific skill"""
    st.markdown(f"""
    <div class="custom-card">
        <h4>{skill}</h4>
        <p><strong>Learning Objectives:</strong></p>
        <ul>
            <li>Understand core concepts and fundamentals</li>
            <li>Complete hands-on tutorials and exercises</li>
            <li>Build a small project demonstrating proficiency</li>
        </ul>
        
        <p><strong>Recommended Resources:</strong></p>
        <div style='display: flex; gap: 0.5rem; flex-wrap: wrap;'>
            <span style='background: #e0f2fe; padding: 0.25rem 0.5rem; border-radius: 6px;'>Official Docs</span>
            <span style='background: #f0fdf4; padding: 0.25rem 0.5rem; border-radius: 6px;'>Video Courses</span>
            <span style='background: #fef7cd; padding: 0.25rem 0.5rem; border-radius: 6px;'>Practice Labs</span>
            <span style='background: #fce7f3; padding: 0.25rem 0.5rem; border-radius: 6px;'>eBooks</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_weekly_timeline(week_num, skills_count):
    """Render weekly timeline information"""
    st.markdown("""
    <div class="custom-card">
        <h4>Time Investment</h4>
        <div style='background: #3b82f6; color: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
            <h3 style='margin: 0;'>10-15</h3>
            <p style='margin: 0;'>hours/week</p>
        </div>
        <p><strong>Weekly Goal:</strong></p>
        <p>Complete 1-2 projects</p>
        <p>Master core concepts</p>
    </div>
    """, unsafe_allow_html=True)

def render_learning_order(missing_skills):
    """Render recommended learning order"""
    st.markdown("### Recommended Learning Order")
    learning_order = pd.DataFrame({
        "Order": range(1, len(missing_skills)+1),
        "Skill": missing_skills,
        "Prerequisites": ["None"] + missing_skills[:-1],
        "Difficulty": ["Medium"] * len(missing_skills),
        "Priority": ["High" if i < 3 else "Medium" if i < 6 else "Low" for i in range(len(missing_skills))]
    })
    st.dataframe(learning_order, use_container_width=True, hide_index=True)

def render_career_impact(current_skills, required_skills):
    """Render career impact analysis"""
    matched_skills = set(current_skills) & set(required_skills)
    progress_pct = len(matched_skills) / len(required_skills)
    
    st.markdown("### Career Impact")
    st.markdown(f"""
    <div class="custom-card">
        <h4>After Completing This Path</h4>
        <p>• <strong>Job Readiness:</strong> Increase from {progress_pct*100:.0f}% to 100%</p>
        <p>• <strong>Salary Potential:</strong> Estimated 20-30% increase</p>
        <p>• <strong>Job Opportunities:</strong> 3-5x more relevant positions</p>
        <p>• <strong>Career Growth:</strong> Faster promotion track</p>
    </div>
    """, unsafe_allow_html=True)