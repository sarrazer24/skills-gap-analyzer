"""
Concrete Example: How to Integrate Personalized Learning Path into app/main.py

This file shows the exact code to add to your Streamlit app to display
the model-driven personalized learning path.

USAGE:
Copy the code blocks below into app/main.py at the appropriate section.
"""

# ============================================================================
# OPTION 1: Complete Replacement for Section 3 (Learning Path)
# ============================================================================
# This replaces the old "📚 View Suggested Learning Path" section

def display_personalized_learning_path(user_skills, job_skills, job_title):
    """
    Display personalized learning path driven by association rules.
    
    This section appears after the gap analysis and shows a ranked,
    phased learning plan based on both gap importance and model signals.
    """
    import streamlit as st
    import pandas as pd
    from src.models.personalized_path import build_personalized_learning_path
    from src.models.association_miner import get_association_rules_from_csv
    from src.models.skill_matcher import SkillMatcher
    
    if st.checkbox("📚 **View Personalized Learning Path** (Powered by Association Rules)", value=False):
        st.markdown("---")
        
        with st.spinner("Generating personalized learning path..."):
            try:
                # Load models
                ensemble = get_association_rules_from_csv('data/processed')
                matcher = SkillMatcher()
                
                # Build path
                path = build_personalized_learning_path(
                    user_skills=user_skills,
                    target_job_skills=job_skills,
                    ensemble=ensemble,
                    gap_analyzer=matcher,
                    max_phases=4,
                    weight_importance=0.5,  # 50% gap importance
                    weight_model=0.5,        # 50% model signals
                )
                
                # Display summary
                st.success(f"**Learning Path Generated**")
                st.info(path['summary'])
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Duration", f"{path['total_weeks']} weeks")
                with col2:
                    st.metric("Model Coverage", f"{path['model_coverage']:.0%}")
                with col3:
                    st.metric("Ranking Algorithm", "Hybrid")
                
                st.caption(f"Algorithm: {path['ranking_algorithm']}")
                
                # Display phases
                if path['phases']:
                    st.subheader("Learning Phases")
                    
                    for phase in path['phases']:
                        # Phase header with metadata
                        emoji_map = {
                            1: "🎯",
                            2: "📚",
                            3: "⚡",
                            4: "🚀",
                            5: "🏆",
                        }
                        emoji = emoji_map.get(phase['phase_number'], "📌")
                        
                        expander_title = (
                            f"{emoji} **{phase['title']}** "
                            f"({phase['difficulty']}) — "
                            f"{phase['duration_weeks']} weeks"
                        )
                        
                        with st.expander(expander_title, expanded=(phase['phase_number'] == 1)):
                            # Skills table
                            skills_data = []
                            for skill in phase['skills']:
                                skills_data.append({
                                    'Skill': skill['name'].title(),
                                    'Score': f"{skill['score']:.0%}",
                                    'Importance': f"{skill['importance']:.0%}",
                                    'Model Signal': f"{skill['model_score']:.0%}",
                                    'Confidence': f"{skill['confidence']:.0%}" if skill['confidence'] > 0 else "—",
                                    'Sources': ', '.join(skill['sources']) if skill['sources'] else "Gap-only",
                                })
                            
                            skills_df = pd.DataFrame(skills_data)
                            st.dataframe(skills_df, use_container_width=True, hide_index=True)
                            
                            # Show explanations
                            st.markdown("**Why these skills?**")
                            for skill in phase['skills']:
                                with st.expander(f"**{skill['name'].title()}** ({skill['score']:.0%})", expanded=False):
                                    st.write(skill['explanation'])
                                    
                                    # Show model breakdown
                                    if skill['model_score'] > 0:
                                        st.markdown("**Model Signals:**")
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Confidence", f"{skill['confidence']:.1%}")
                                        with col2:
                                            st.metric("Lift", f"{skill['lift']:.2f}x")
                                        with col3:
                                            st.metric("Sources", len(skill['sources']))
                else:
                    st.success("✅ **Excellent!** You already have all required skills for this job!")
                
                # Recommendations for how to follow the path
                st.markdown("---")
                st.subheader("💡 Tips for Following This Path")
                st.markdown("""
                1. **Start with Foundation**: Phase 1 skills are fundamental and will help you learn later phases
                2. **Use Model Signals**: Skills with higher confidence scores are more strongly connected to your current skills
                3. **Consider Lift Values**: Lift > 1 means the association is stronger than random chance
                4. **Check Sources**: Skills recommended by multiple models (A1, A2, A3) are more reliable
                5. **Time Management**: Estimate 1-2 weeks per skill, depending on complexity
                """)
                
            except Exception as e:
                st.error(f"❌ Error generating learning path: {str(e)}")
                st.info("Make sure the association rule CSV files exist in `data/processed/` directory.")
                st.code(f"Error details:\n{str(e)}", language="python")


# ============================================================================
# OPTION 2: Minimal Integration (Just the Phases)
# ============================================================================
# Use this if you want a more compact version

def display_learning_path_minimal(user_skills, job_skills):
    """Compact version showing only essential information."""
    import streamlit as st
    import pandas as pd
    from src.models.personalized_path import build_personalized_learning_path
    from src.models.association_miner import get_association_rules_from_csv
    from src.models.skill_matcher import SkillMatcher
    
    if st.checkbox("📚 Personalized Learning Path"):
        try:
            ensemble = get_association_rules_from_csv('data/processed')
            matcher = SkillMatcher()
            
            path = build_personalized_learning_path(
                user_skills=user_skills,
                target_job_skills=job_skills,
                ensemble=ensemble,
                gap_analyzer=matcher,
            )
            
            if path['phases']:
                for phase in path['phases']:
                    st.write(f"**{phase['title']}** ({phase['duration_weeks']} weeks)")
                    for skill in phase['skills']:
                        st.write(f"  • {skill['name']}: {skill['score']:.0%}")
            else:
                st.success("✅ All skills acquired!")
        except Exception as e:
            st.warning(f"Could not generate path: {e}")


# ============================================================================
# OPTION 3: Advanced with User Controls
# ============================================================================
# Use this if you want to let users adjust the weighting

def display_learning_path_advanced(user_skills, job_skills):
    """Advanced version with customization options."""
    import streamlit as st
    import pandas as pd
    from src.models.personalized_path import build_personalized_learning_path
    from src.models.association_miner import get_association_rules_from_csv
    from src.models.skill_matcher import SkillMatcher
    
    if st.checkbox("📚 Personalized Learning Path (Advanced)"):
        st.markdown("---")
        
        # User controls
        col1, col2, col3 = st.columns(3)
        with col1:
            max_phases = st.slider("Max Phases", 2, 6, 4)
        with col2:
            weight_gap = st.slider("Gap Importance Weight", 0.0, 1.0, 0.5, step=0.1)
        with col3:
            weight_model = 1.0 - weight_gap
            st.metric("Model Weight", f"{weight_model:.0%}")
        
        try:
            ensemble = get_association_rules_from_csv('data/processed')
            matcher = SkillMatcher()
            
            path = build_personalized_learning_path(
                user_skills=user_skills,
                target_job_skills=job_skills,
                ensemble=ensemble,
                gap_analyzer=matcher,
                max_phases=max_phases,
                weight_importance=weight_gap,
                weight_model=weight_model,
            )
            
            st.info(path['summary'])
            
            if path['phases']:
                for phase in path['phases']:
                    with st.expander(f"{phase['title']} ({phase['difficulty']})"):
                        skills_df = pd.DataFrame([
                            {
                                'Skill': s['name'].title(),
                                'Score': f"{s['score']:.0%}",
                                'Model': f"{s['model_score']:.0%}" if s['model_score'] > 0 else "Gap-only",
                            }
                            for s in phase['skills']
                        ])
                        st.table(skills_df)
        except Exception as e:
            st.error(f"Error: {e}")


# ============================================================================
# INTEGRATION TEMPLATE FOR app/main.py
# ============================================================================
"""
Add this code to your app/main.py main() function, after the gap analysis section:

```python
def main():
    st.set_page_config(...)
    
    # ... existing code ...
    
    # SECTION 1: Gap Analysis (existing)
    with st.container():
        # ... your existing gap analysis code ...
        pass
    
    # SECTION 2B: AI-Powered Recommendations (existing)
    with st.container():
        # ... your existing recommendations code ...
        pass
    
    # SECTION 3: Personalized Learning Path (NEW - Add here)
    st.markdown("---")
    st.header("🎓 Section 3: Personalized Learning Path")
    st.markdown(
        "Based on gap analysis and association rule models, "
        "here's a customized learning plan to reach your target role."
    )
    
    # Choose one of the options above:
    display_personalized_learning_path(user_skills, job_skills, job_title)
    
    # Or use the advanced version:
    # display_learning_path_advanced(user_skills, job_skills)
```
"""

# ============================================================================
# DATA STRUCTURES RETURNED
# ============================================================================
"""
The build_personalized_learning_path function returns:

{
    'phases': [
        {
            'phase_number': 1,
            'title': '🎯 Foundation Skills',
            'skills': [
                {
                    'name': 'sql',
                    'score': 0.87,                    # Combined score (0-1)
                    'importance': 0.8,               # Gap-based importance
                    'model_score': 0.9,              # Association rule signal
                    'sources': ['A1', 'A3'],         # Which models recommended it
                    'confidence': 0.78,              # Avg confidence from rules
                    'lift': 1.4,                     # Avg lift from rules
                    'explanation': 'Job requires...'  # Human-readable reason
                },
                ...
            ],
            'duration_weeks': 4,
            'difficulty': 'Easy'
        },
        ...
    ],
    'total_weeks': 20,
    'summary': 'Personalized learning path: X skills in Y phases...',
    'model_coverage': 0.85,                          # % with model signals
    'ranking_algorithm': 'Association Rules + Gap Analysis'
}
"""

# ============================================================================
# KEY CONCEPTS
# ============================================================================
"""
1. **Score Components**:
   - base_importance: How critical is this skill for the target job? (0-1)
   - model_score: How often does this skill appear in association rules? (0-1)
   - final_score: Combined score = 0.5 * base + 0.5 * model

2. **Model Sources**:
   - A1: Skill-level rules (308 rules) - most specific
   - A2: Category-level rules (22 rules) - most abstract
   - A3: Combined rules (7,147 rules) - most comprehensive
   - Gap-only: No rules found, uses gap importance alone

3. **Confidence & Lift**:
   - Confidence: How often does user's skill lead to target skill? (0-1)
   - Lift: Is this association stronger than random chance? (>1 is good)

4. **Phases**:
   - Foundation (Easy): Most fundamental, prerequisites for other skills
   - Core (Easy-Medium): Core competencies needed for the role
   - Intermediate: Build on foundation
   - Advanced: Specialized skills
   - Expert (Hard): Most challenging, most specialized
"""
