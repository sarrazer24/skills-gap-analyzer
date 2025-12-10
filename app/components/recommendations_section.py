"""Section 2B: AI-powered Recommendations - association rules."""
import streamlit as st
import pandas as pd


def render_recommendations(
    ensemble,
    user_skills: list,
    selected_job: dict,
    colors: dict
) -> dict:
    """Render AI-powered recommendations section using association rules.
    
    Displays:
    - Related skills to learn alongside each missing skill
    - Alternative roles based on user skills
    - Job clustering insights
    
    Args:
        ensemble: AssociationEnsemble instance
        user_skills: List of user's skills
        selected_job: Selected job dict
        colors: Color dictionary from get_colors()
        
    Returns:
        dict with 'recommendations' list
    """
    if not user_skills or not selected_job:
        return {}
    
    st.divider()
    st.markdown("<h2 class='section-title'>💡 AI-Powered Recommendations</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Skills that are frequently learned together (from association rules).</div>",
        unsafe_allow_html=True
    )
    
    try:
        # Get recommendations from ensemble
        user_skills_norm = [s.lower().strip() for s in user_skills if s]
        recommendations = ensemble.recommend(
            user_skills=user_skills_norm,
            target_job=selected_job.get('job_title', ''),
            top_n=5
        )
    except Exception as e:
        st.error(f"Could not generate recommendations: {str(e)}")
        return {}
    
    if not recommendations:
        st.info("No recommendations available yet. Add more skills to get suggestions.")
        return {}
    
    # Display recommendations as cards in responsive grid
    st.markdown("##### 🎯 Recommended Skills to Learn")
    cols = st.columns(3)
    
    for idx, rec in enumerate(recommendations[:6]):
        with cols[idx % 3]:
            confidence = rec.get('confidence', 0)
            conf_pct = confidence * 100 if confidence else 0
            
            # Color code by confidence
            if conf_pct >= 75:
                card_bg, card_border = '#dcfce7', '#22c55e'
            elif conf_pct >= 50:
                card_bg, card_border = '#fef3c7', '#f59e0b'
            else:
                card_bg, card_border = '#e0e7ff', '#6366f1'
            
            st.markdown(f"""
            <div style="
                background: {card_bg};
                border-radius: 8px;
                padding: 12px;
                border-left: 4px solid {card_border};
                height: 100%;
            ">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">
                    {rec.get('skill', 'Unknown').title()}
                </div>
                <div style="font-size: 0.75rem; color: {card_border};">
                    ⭐ {conf_pct:.0f}% confidence
                </div>
                <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                    {rec.get('reason', 'Frequently paired with your skills')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Alternative roles section
    st.markdown("##### 🔀 Alternative Roles You Might Fit")
    try:
        alt_roles = ensemble.find_alternative_roles(user_skills_norm, top_n=3)
        if alt_roles:
            for role in alt_roles:
                match_pct = role.get('match_percent', 0)
                st.markdown(f"""
                <div style="
                    background: {colors['bg_secondary']};
                    border-radius: 8px;
                    padding: 12px;
                    margin: 0.5rem 0;
                    border-left: 4px solid {colors['accent_primary']};
                ">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">
                        {role.get('role', 'Unknown')}
                    </div>
                    <div style="font-size: 0.85rem; color: {colors['text_secondary']};">
                        Match: <strong>{match_pct:.0f}%</strong> | 
                        {len(role.get('matching_skills', []))} matching skills
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No alternative roles found.")
    except Exception:
        st.info("Alternative roles analysis not available.")
    
    return {'recommendations': recommendations}
