"""Section 3: Personalized Learning Path - phased curriculum."""
import streamlit as st
import pandas as pd


def render_learning_path(
    generator,
    user_skills: list,
    selected_job: dict,
    gap_results: dict,
    colors: dict
) -> dict:
    """Render personalized learning path section.
    
    Displays:
    - Phased learning plan (weeks grouped by priority)
    - Estimated timeline
    - Resources and milestones
    - Progress indicators
    
    Args:
        generator: LearningPathGenerator instance
        user_skills: List of user's skills
        selected_job: Selected job dict
        gap_results: Dict from gap analysis with 'missing' and 'match_percent'
        colors: Color dictionary from get_colors()
        
    Returns:
        dict with 'learning_path' list and 'timeline'
    """
    if not user_skills or not selected_job or not gap_results.get('missing'):
        st.info("Complete skill gap analysis first to see learning path recommendations.")
        return {}
    
    st.divider()
    st.markdown("<h2 class='section-title'>📚 Personalized Learning Path</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>A phased curriculum to close your skill gaps.</div>",
        unsafe_allow_html=True
    )
    
    try:
        # Generate learning path
        learning_path = generator.generate(
            current_skills=user_skills,
            target_job=selected_job.get('job_title', ''),
            missing_skills=list(gap_results.get('missing', [])),
            target_weeks=26  # 6-month default plan
        )
    except Exception as e:
        st.error(f"Could not generate learning path: {str(e)}")
        return {}
    
    if not learning_path or not learning_path.get('phases', []):
        st.info("Unable to create a learning path with current data.")
        return {}
    
    # Display timeline overview
    total_weeks = learning_path.get('total_weeks', 26)
    total_skills = len(gap_results.get('missing', []))
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid {colors['accent_primary']};
        margin: 1.5rem 0;
    ">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Learning Timeline:</p>
                <p style="color: {colors['text_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">
                    {total_weeks} weeks
                </p>
            </div>
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Skills to Master:</p>
                <p style="color: {colors['accent_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">
                    {total_skills} skills
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display phases as timeline
    phases = learning_path.get('phases', [])
    for phase_idx, phase in enumerate(phases, 1):
        phase_title = phase.get('title', f'Phase {phase_idx}')
        phase_duration = phase.get('duration_weeks', 4)
        phase_skills = phase.get('skills', [])
        
        # Phase header with timeline indicator
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="text-align: center; font-weight: 700; color: {colors['accent_primary']};">
                PHASE {phase_idx}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: {colors['bg_secondary']}; border-radius: 4px; padding: 4px 8px; text-align: center; font-size: 0.85rem;">
                {phase_duration} weeks
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            pct = (phase_idx / len(phases)) * 100
            st.markdown(f"""
            <div style="text-align: right; color: {colors['text_secondary']}; font-size: 0.85rem;">
                {pct:.0f}% done
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable phase details
        with st.expander(f"🎯 {phase_title}", expanded=(phase_idx == 1)):
            # Phase description
            if phase.get('description'):
                st.markdown(f"**{phase['description']}**")
            
            # Skills in this phase
            if phase_skills:
                st.markdown("**Skills to learn:**")
                skill_cols = st.columns(2)
                for skill_idx, skill in enumerate(phase_skills):
                    with skill_cols[skill_idx % 2]:
                        skill_name = skill.get('name', skill) if isinstance(skill, dict) else skill
                        difficulty = skill.get('difficulty', 'intermediate') if isinstance(skill, dict) else 'intermediate'
                        
                        # Color code by difficulty
                        if difficulty == 'beginner':
                            diff_color = '#10b981'
                        elif difficulty == 'intermediate':
                            diff_color = '#f59e0b'
                        else:
                            diff_color = '#ef4444'
                        
                        st.markdown(f"""
                        <div style="
                            background: {colors['bg_secondary']};
                            border-radius: 8px;
                            padding: 10px;
                            margin: 0.5rem 0;
                        ">
                            <div style="font-weight: 600;">{skill_name}</div>
                            <div style="font-size: 0.75rem; color: {diff_color};">
                                {difficulty.capitalize()}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Resources
            if phase.get('resources'):
                st.markdown("**Resources:**")
                for resource in phase['resources']:
                    resource_name = resource.get('name', resource) if isinstance(resource, dict) else resource
                    resource_type = resource.get('type', 'Course') if isinstance(resource, dict) else 'Course'
                    st.caption(f"📖 {resource_type}: {resource_name}")
            
            # Milestones
            if phase.get('milestones'):
                st.markdown("**Milestones:**")
                for milestone in phase['milestones']:
                    milestone_text = milestone.get('description', milestone) if isinstance(milestone, dict) else milestone
                    st.caption(f"✓ {milestone_text}")
        
        st.write("")
    
    return {
        'learning_path': learning_path,
        'total_weeks': total_weeks,
        'phases_count': len(phases)
    }
