"""Section 4: Similar Opportunities - job clustering."""
import streamlit as st
import pandas as pd


def render_similar_opportunities(
    cluster_analyzer,
    selected_job: dict,
    colors: dict,
    jobs_df: pd.DataFrame = None
) -> dict:
    """Render similar opportunities section using job clustering.
    
    Displays:
    - Similar jobs in same cluster
    - Job comparison metrics (salary, company, skills overlap)
    - Alternative career paths
    
    Args:
        cluster_analyzer: ClusterAnalyzer instance
        selected_job: Selected job dict
        colors: Color dictionary from get_colors()
        jobs_df: Optional full jobs DataFrame for reference
        
    Returns:
        dict with 'similar_jobs' list
    """
    if not selected_job:
        st.info("Select a target role to see similar opportunities.")
        return {}
    
    st.divider()
    st.markdown("<h2 class='section-title'>🎪 Similar Opportunities</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Other roles with similar requirements and growth potential.</div>",
        unsafe_allow_html=True
    )
    
    try:
        # Find similar jobs
        similar_jobs = cluster_analyzer.find_similar(
            job=selected_job.get('job_title', ''),
            top_n=6
        )
    except Exception as e:
        st.error(f"Could not find similar opportunities: {str(e)}")
        return {}
    
    if not similar_jobs:
        st.info("No similar opportunities found in our database.")
        return {}
    
    # Display similar jobs as card grid
    st.markdown("##### 🏆 Other Roles in Your Career Cluster")
    cols = st.columns(3)
    
    for idx, job in enumerate(similar_jobs):
        with cols[idx % 3]:
            job_title = job.get('job_title', 'Job')
            company = job.get('company', 'Unknown')
            salary = job.get('salary_range', 'N/A')
            similarity = job.get('similarity_score', 0)
            skill_overlap = job.get('skill_overlap', 0)
            
            # Color code by similarity
            if similarity >= 0.8:
                sim_color = '#10b981'
            elif similarity >= 0.6:
                sim_color = '#f59e0b'
            else:
                sim_color = '#6366f1'
            
            st.markdown(f"""
            <div style="
                background: {colors['bg_secondary']};
                border-radius: 12px;
                padding: 16px;
                border-left: 4px solid {sim_color};
                height: 100%;
                display: flex;
                flex-direction: column;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: {colors['text_primary']};">
                    {job_title}
                </h4>
                <p style="margin: 0.25rem 0; color: {colors['text_secondary']}; font-size: 0.85rem;">
                    <strong>{company}</strong>
                </p>
                <p style="margin: 0.25rem 0; color: {colors['text_secondary']}; font-size: 0.85rem;">
                    {salary}
                </p>
                <div style="margin-top: auto; padding-top: 0.5rem; border-top: 1px solid {colors['bg_tertiary']};">
                    <div style="font-size: 0.75rem; color: {sim_color};">
                        ⭐ {similarity*100:.0f}% similar
                    </div>
                    <div style="font-size: 0.75rem; color: {colors['text_secondary']};">
                        {skill_overlap:.0f}% skill overlap
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Career path analysis
    st.markdown("##### 📈 Career Path Analysis")
    
    try:
        # Get cluster info for career trajectory
        cluster_info = cluster_analyzer.get_cluster_info(
            job=selected_job.get('job_title', '')
        )
        
        if cluster_info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Cluster Size",
                    cluster_info.get('cluster_size', 0),
                    help="Number of jobs in this career cluster"
                )
            
            with col2:
                avg_salary = cluster_info.get('avg_salary', 'N/A')
                st.metric(
                    "Avg. Salary in Cluster",
                    str(avg_salary),
                    help="Average salary for roles in this cluster"
                )
            
            with col3:
                growth = cluster_info.get('growth_trend', 'Stable')
                st.metric(
                    "Growth Trend",
                    growth,
                    help="Job market trend for this cluster"
                )
    except Exception:
        pass
    
    # Skill bridge opportunities
    st.markdown("##### 🌉 Skill Bridge Opportunities")
    
    try:
        bridge_skills = cluster_analyzer.find_bridge_skills(
            from_job=selected_job.get('job_title', ''),
            top_n=3
        )
        
        if bridge_skills:
            st.markdown("Learn these skills to transition to related higher-paying roles:")
            skill_cols = st.columns(3)
            for idx, skill in enumerate(bridge_skills):
                with skill_cols[idx % 3]:
                    skill_name = skill.get('skill', skill) if isinstance(skill, dict) else skill
                    impact = skill.get('impact_score', 0)
                    
                    st.markdown(f"""
                    <div style="
                        background: {colors['accent_bg']};
                        border-radius: 8px;
                        padding: 12px;
                    ">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">
                            {skill_name}
                        </div>
                        <div style="font-size: 0.75rem; color: {colors['accent_primary']};">
                            ⬆️ Impact: {impact*100:.0f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No bridge skills identified yet.")
    except Exception:
        st.info("Skill bridge analysis not available.")
    
    return {
        'similar_jobs': similar_jobs,
        'count': len(similar_jobs)
    }
