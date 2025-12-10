"""Section 2: Skill Gap Analysis - gap metrics, missing/matching skills, priority groups."""
import streamlit as st
import pandas as pd
import ast
from src.models.skill_matcher import SkillMatcher


def render_gap_analysis(
    skill_matcher: SkillMatcher,
    user_skills: list,
    selected_job: dict,
    colors: dict,
    skills_df: pd.DataFrame = None
) -> dict:
    """Render skill gap analysis section.
    
    Displays:
    - Summary metrics (required skills, matching, match %)
    - Expandable lists: matching skills, missing skills, extra skills
    - Priority groups for missing skills (Critical/Important/Nice-to-have)
    
    Args:
        skill_matcher: SkillMatcher instance for gap analysis
        user_skills: List of user's skills (strings)
        selected_job: Selected job dict with 'skill_list' key
        colors: Color dictionary from get_colors()
        skills_df: Optional skills taxonomy (for future category mapping)
        
    Returns:
        dict with 'matching', 'missing', 'extra' sets and 'match_percent'
    """
    # Early exit if insufficient input
    if not user_skills or not selected_job:
        st.info("Add skills and select a job to see gap analysis.")
        return {}
    
    st.divider()
    st.markdown("<h2 class='section-title'>2️⃣ Skill gap analysis</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Compare your skills to the role and prioritize the most important gaps.</div>",
        unsafe_allow_html=True
    )
    
    # Parse job skills from various formats
    job_skills = _parse_job_skills(selected_job)
    user_skills_norm = [s.lower().strip() for s in user_skills if s]
    
    # Calculate sets
    user_set = set(user_skills_norm)
    job_set = set(job_skills)
    user_set.discard('')
    job_set.discard('')
    
    matching = user_set & job_set
    missing = job_set - user_set
    extra = user_set - job_set
    
    match_percent = (len(matching) / len(job_set) * 100) if job_set else 0
    
    # Display summary metrics
    _render_gap_summary(len(job_set), len(matching), match_percent, colors)
    
    # Progress bar
    st.progress(match_percent / 100, text=f"Career Readiness: {match_percent:.1f}%")
    st.write("")
    
    # Set up color scheme for skill cards
    match_bg, match_border, match_title = '#dcfce7', '#22c55e', '#15803d'
    missing_bg, missing_border, missing_title = '#fee2e2', '#dc2626', '#7f1d1d'
    extra_bg, extra_border, extra_title = '#e0e7ff', '#6366f1', '#312e81'
    
    # Section 1: Matching Skills (expander)
    with st.expander("✅ Your Matching Skills", expanded=False):
        if matching:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(matching)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: {match_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid {match_border};">
                        <div style="font-weight: 600; color: {match_title} !important;">✓ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No matching skills found yet.")
    
    # Section 2: Missing Skills (priority groups)
    with st.expander("❌ Skills You Need", expanded=True):
        if missing:
            # Try to use SkillMatcher for learning time estimates
            try:
                gap_analysis = skill_matcher.analyze_gap(list(user_set), list(job_set))
                learning_estimate = skill_matcher.estimate_learning_time(gap_analysis['missing'])
                missing_sorted = gap_analysis.get('missing', sorted(missing))
            except Exception:
                # Fallback if matcher fails
                learning_estimate = {
                    'total_hours': len(missing) * 50,  # rough estimate
                    'total_weeks': len(missing) * 2,
                    'total_months': len(missing) * 0.5
                }
                missing_sorted = sorted(missing)
            
            # Display learning metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(
                    f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#ef4444;'>{len(missing)}</div>"
                    f"<div style='font-size:0.75rem; color:#666; margin-top:4px;'>Skills to Learn</div></div>",
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#3b82f6;'>"
                    f"{learning_estimate['total_hours']:.0f}h</div>"
                    f"<div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Hours</div></div>",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(
                    f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#f59e0b;'>"
                    f"{learning_estimate['total_weeks']:.1f}w</div>"
                    f"<div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Weeks</div></div>",
                    unsafe_allow_html=True
                )
            with col4:
                st.markdown(
                    f"<div style='text-align:center;'><div style='font-weight:700; font-size:1.5rem; color:#10b981;'>"
                    f"{learning_estimate['total_months']:.1f}m</div>"
                    f"<div style='font-size:0.75rem; color:#666; margin-top:4px;'>Est. Months</div></div>",
                    unsafe_allow_html=True
                )
            
            # Render priority groups (critical/important/nice-to-have)
            _render_priority_groups(missing_sorted, colors)
        else:
            st.success("✅ You have all the required skills!")
    
    # Section 3: Extra Skills (bonus)
    with st.expander("📊 Additional Skills You Have", expanded=False):
        if extra:
            cols = st.columns(4)
            for idx, skill in enumerate(sorted(extra)):
                with cols[idx % 4]:
                    st.markdown(f"""
                    <div style="background: {extra_bg}; border-radius: 8px; padding: 10px; border-left: 3px solid {extra_border};">
                        <div style="font-weight: 600; color: {extra_title};">+ {skill.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No additional skills beyond what's required.")
    
    return {
        'matching': matching,
        'missing': missing,
        'extra': extra,
        'match_percent': match_percent,
        'job_set': job_set,
        'user_set': user_set
    }


def _parse_job_skills(job_data: dict) -> list:
    """Parse job skills from various formats (str/list/tuple).
    
    Args:
        job_data: Job dictionary with 'skill_list' key
        
    Returns:
        List of skill strings (lowercase)
    """
    job_skills_raw = job_data.get('skill_list', [])
    job_skills = []
    
    if isinstance(job_skills_raw, str):
        # Try literal_eval first (for stringified list/tuple)
        try:
            parsed = ast.literal_eval(job_skills_raw)
            if isinstance(parsed, (list, tuple)):
                job_skills = [str(s).strip().lower() for s in parsed if s]
        except (ValueError, SyntaxError):
            # Fallback: comma-separated
            job_skills = [s.strip().lower() for s in job_skills_raw.split(',') if s.strip()]
    elif isinstance(job_skills_raw, (list, tuple)):
        job_skills = [str(s).strip().lower() for s in job_skills_raw if s]
    
    return job_skills


def _render_gap_summary(job_count: int, matching_count: int, match_pct: float, colors: dict) -> None:
    """Render the summary metrics card (required / matching / match %).
    
    Args:
        job_count: Total required skills
        matching_count: Number of matching skills
        match_pct: Match percentage
        colors: Color dictionary
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors['bg_tertiary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid {colors['accent_primary']};
        margin: 1.5rem 0;
    ">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Required for role:</p>
                <p style="color: {colors['text_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">{job_count} skills</p>
            </div>
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Your matching:</p>
                <p style="color: #10b981; font-size: 1.5rem; font-weight: 700; margin: 0;">{matching_count} skills</p>
            </div>
            <div>
                <p style="color: {colors['text_secondary']}; margin: 0 0 0.5rem 0; font-weight: 500;">Your match rate:</p>
                <p style="color: {colors['accent_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0;">{match_pct:.1f}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_priority_groups(missing_sorted: list, colors: dict) -> None:
    """Render missing skills grouped by priority (Critical/Important/Nice-to-have).
    
    Uses responsive card grid layout (3 cols desktop, 2 cols tablet, 1 col mobile).
    
    Args:
        missing_sorted: Sorted list of missing skills
        colors: Color dictionary
    """
    third = max(1, len(missing_sorted) // 3)
    high_priority = missing_sorted[:third]
    med_priority = missing_sorted[third:third*2]
    low_priority = missing_sorted[third*2:]
    
    critical_bg, critical_border, critical_title = '#fee2e2', '#dc2626', '#7f1d1d'
    med_bg, med_border, med_title = '#fef3c7', '#f59e0b', '#78350f'
    low_bg, low_border, low_title = '#dcfce7', '#22c55e', '#15803d'
    
    if high_priority:
        st.markdown("##### 🔴 Critical — Learn first")
        cards_html = '<div class="card-grid">'
        for skill in high_priority:
            cards_html += f"""
            <div class="card">
                <div style="background: {critical_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {critical_border}; height: 100%;">
                    <div style="font-weight: 600; color: {critical_title} !important;">{skill.title()}</div>
                </div>
            </div>
            """
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    
    if med_priority:
        st.markdown("##### 🟡 Important — Learn after critical")
        cards_html = '<div class="card-grid">'
        for skill in med_priority:
            cards_html += f"""
            <div class="card">
                <div style="background: {med_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {med_border}; height: 100%;">
                    <div style="font-weight: 600; color: {med_title} !important;">{skill.title()}</div>
                </div>
            </div>
            """
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    
    if low_priority:
        st.markdown("##### 🟢 Nice to have — Learn if time permits")
        cards_html = '<div class="card-grid">'
        for skill in low_priority:
            cards_html += f"""
            <div class="card">
                <div style="background: {low_bg}; border-radius: 8px; padding: 12px; border-left: 4px solid {low_border}; height: 100%;">
                    <div style="font-weight: 600; color: {low_title} !important;">{skill.title()}</div>
                </div>
            </div>
            """
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
