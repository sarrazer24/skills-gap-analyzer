# components/skills_tab.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_skills_tab(user_data):
    """Render the skills analysis tab"""
    current_skills = st.session_state.get('current_skills', [])
    required_skills = st.session_state.get('required_skills', [])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_skills_breakdown(current_skills, required_skills)
        render_skills_dataframe(current_skills, required_skills)
    
    with col2:
        render_skills_distribution(current_skills, required_skills)
        render_quick_insights(current_skills, required_skills)

def render_skills_breakdown(current_skills, required_skills):
    """Render skills breakdown with badges"""
    st.markdown("### Skills Breakdown")
    st.markdown("#### Your Skills Match")
    
    skills_html = ""
    for skill in required_skills:
        if skill in current_skills:
            skills_html += f'<span class="skill-badge skill-badge-owned">✓ {skill}</span>'
        else:
            skills_html += f'<span class="skill-badge skill-badge-missing">✗ {skill}</span>'
    
    st.markdown(skills_html, unsafe_allow_html=True)

def render_skills_dataframe(current_skills, required_skills):
    """Render skills dataframe"""
    st.markdown("#### Detailed Skills Analysis")
    
    skills_df = pd.DataFrame({
        "Skill": required_skills,
        "Status": ["Owned" if skill in current_skills else "Needed" 
                  for skill in required_skills],
        "Priority": ["High" if i < 3 else "Medium" if i < 6 else "Low" 
                   for i in range(len(required_skills))],
        "Market Demand": ["Very High", "High", "High", "Medium", "High", "Medium", "High"][:len(required_skills)]
    })
    
    st.dataframe(skills_df, use_container_width=True, hide_index=True)

def render_skills_distribution(current_skills, required_skills):
    """Render skills distribution pie chart"""
    st.markdown("### Skills Distribution")
    
    status_counts = pd.Series([
        "Owned" if skill in current_skills else "Needed"
        for skill in required_skills
    ]).value_counts()
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=0.4,
        marker=dict(colors=['#10b981', '#f59e0b']),
        textinfo='percent+label'
    )])
    
    fig_pie.update_layout(
        height=300,
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=[dict(text='Skills', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig_pie, use_container_width=True)

def render_quick_insights(current_skills, required_skills):
    """Render quick insights card"""
    matched_skills = set(current_skills) & set(required_skills)
    high_priority_missing = len([s for s in required_skills[:3] if s not in current_skills])
    high_demand_skills = len([s for s in required_skills if s in ["Python", "JavaScript", "AWS", "Docker"]])
    
    st.markdown(f"""
    <div class="custom-card">
        <h4>Quick Insights</h4>
        <p>• You have <strong>{len(matched_skills)}</strong> of <strong>{len(required_skills)}</strong> required skills</p>
        <p>• Focus on <strong>{high_priority_missing}</strong> high-priority skills first</p>
        <p>• <strong>{high_demand_skills}</strong> skills are in high demand</p>
    </div>
    """, unsafe_allow_html=True)