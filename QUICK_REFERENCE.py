"""
QUICK REFERENCE: Personalized Learning Path

Copy-paste quick start for integrating model-driven learning paths.
"""

# ============================================================================
# 1-MINUTE QUICK START
# ============================================================================

from src.models.personalized_path import build_personalized_learning_path
from src.models.association_miner import get_association_rules_from_csv
from src.models.skill_matcher import SkillMatcher

# Build learning path in 3 lines
ensemble = get_association_rules_from_csv('data/processed')
matcher = SkillMatcher()
path = build_personalized_learning_path(
    user_skills=['python', 'sql'],
    target_job_skills=['python', 'sql', 'spark', 'ml', 'aws'],
    ensemble=ensemble,
    gap_analyzer=matcher,
)

# Access results
print(f"Phases: {len(path['phases'])}")
print(f"Duration: {path['total_weeks']} weeks")
print(f"Model Coverage: {path['model_coverage']:.0%}")


# ============================================================================
# WHAT YOU GET
# ============================================================================

# path['phases'] = [
#     {
#         'phase_number': 1,
#         'title': '🎯 Foundation Skills',
#         'difficulty': 'Easy',
#         'duration_weeks': 4,
#         'skills': [
#             {
#                 'name': 'machine learning',
#                 'score': 0.85,           # Combined gap + model
#                 'importance': 0.90,      # Gap only
#                 'model_score': 0.80,     # Association rules
#                 'sources': ['A1', 'A3'], # Which models
#                 'confidence': 0.78,      # Rule confidence
#                 'lift': 1.35,            # Rule strength
#                 'explanation': '...'     # Why recommended
#             },
#             ...
#         ]
#     },
#     ...
# ]


# ============================================================================
# DISPLAY IN STREAMLIT
# ============================================================================

import streamlit as st

if st.checkbox("📚 View Learning Path"):
    # Build path
    path = build_personalized_learning_path(
        user_skills=user_skills,
        target_job_skills=job_skills,
        ensemble=ensemble,
        gap_analyzer=matcher,
    )
    
    # Show summary
    st.info(path['summary'])
    
    # Show phases
    for phase in path['phases']:
        with st.expander(f"{phase['title']} ({phase['duration_weeks']} weeks)"):
            for skill in phase['skills']:
                st.write(f"• **{skill['name']}** ({skill['score']:.0%})")
                st.caption(skill['explanation'])


# ============================================================================
# KEY PARAMETERS
# ============================================================================

path = build_personalized_learning_path(
    user_skills=['python', 'sql'],           # User's current skills
    target_job_skills=['python', 'sql', ...], # Target job requirements
    ensemble=ensemble,                       # Loaded models (A1, A2, A3)
    gap_analyzer=matcher,                    # Gap analyzer
    max_phases=4,                            # How many learning phases
    skills_per_phase=3,                      # Skills per phase
    weight_importance=0.5,                   # Gap weight (0-1)
    weight_model=0.5,                        # Model weight (0-1)
)

# Change weights to prefer models:
# weight_importance=0.2, weight_model=0.8


# ============================================================================
# WHAT EACH SCORE MEANS
# ============================================================================

# final_score (0-1):
#   = 0.5 * base_importance + 0.5 * model_score
#   Combined recommendation strength
#   Higher = learn first

# base_importance (0-1):
#   From gap analysis
#   How critical for target job

# model_score (0-1):
#   From association rules
#   How often learned with user's skills

# confidence (0-1):
#   % of people with user's skills who learn this
#   From association rules

# lift (>1 is good):
#   Association strength vs random
#   lift=1.5 means 50% more likely than random


# ============================================================================
# MODEL SOURCES (A1, A2, A3)
# ============================================================================

# 'sources': ['A1', 'A3']
#   A1 = Skill-level model (308 rules) - most specific
#   A2 = Category-level model (22 rules) - broad patterns
#   A3 = Combined model (7,147 rules) - comprehensive

# 'sources': [] 
#   No models recommended (gap-only recommendation)
#   Shows as "—" or "Gap-only" in explanations


# ============================================================================
# COMMON CUSTOMIZATIONS
# ============================================================================

# Option 1: Emphasize model signals
path = build_personalized_learning_path(
    ...,
    weight_importance=0.2,
    weight_model=0.8,
)

# Option 2: Emphasize gap importance
path = build_personalized_learning_path(
    ...,
    weight_importance=0.8,
    weight_model=0.2,
)

# Option 3: More phases, fewer skills per phase
path = build_personalized_learning_path(
    ...,
    max_phases=6,
    skills_per_phase=2,
)

# Option 4: Get raw model scores only
scores = ensemble.get_skill_model_scores(
    user_skills=['python', 'sql'],
    target_skills=['spark', 'ml', 'aws']
)
# Returns: {'spark': {'model_scores': {...}, 'best_confidence': 0.75, ...}, ...}


# ============================================================================
# ERROR HANDLING
# ============================================================================

try:
    path = build_personalized_learning_path(...)
except Exception as e:
    # Models not loaded, CSV files missing, etc.
    st.error(f"Could not generate path: {e}")

# Or with fallback
try:
    path = build_personalized_learning_path(...)
except Exception:
    # Fall back to gap analysis only
    path = get_gap_analysis_only(user_skills, job_skills)


# ============================================================================
# PERFORMANCE
# ============================================================================

# Gap analysis: ~50ms
# Load models: ~100-200ms
# Query models: ~200-500ms
# Ranking & grouping: ~100ms
# Total: ~500ms-1s

# For Streamlit: Use st.cache_resource to avoid reloading


# ============================================================================
# TESTING
# ============================================================================

# Quick test
from test_learning_path_integration import *
test_prioritize_missing_skills()    # Test ranking
test_build_learning_path()          # Test path builder
test_model_coverage()               # Test model signals

# Or run full test suite:
# python test_learning_path_integration.py


# ============================================================================
# DOCUMENTATION FILES
# ============================================================================

# LEARNING_PATH_INTEGRATION.md
#   - Full architecture and design
#   - Detailed function documentation
#   - Streamlit integration guide
#   - Customization options

# LEARNING_PATH_INTEGRATION_EXAMPLE.py
#   - 3 complete Streamlit code examples
#   - Copy-paste ready
#   - Data structure documentation
#   - Key concepts

# LEARNING_PATH_SUMMARY.md
#   - This quick reference
#   - Performance metrics
#   - File locations
#   - Future enhancements

# test_learning_path_integration.py
#   - Executable test suite
#   - Verifies all functions work


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

# [ ] Load ensemble: ensemble = get_association_rules_from_csv('data/processed')
# [ ] Load matcher: matcher = SkillMatcher()
# [ ] Call build_personalized_learning_path() with user/target skills
# [ ] Access path['phases'] for learning phases
# [ ] Display in Streamlit with st.expander() or st.table()
# [ ] Customize weights if needed (weight_importance, weight_model)
# [ ] Test with sample skills
# [ ] Deploy to production


# ============================================================================
# EXAMPLE OUTPUT
# ============================================================================

"""
Summary: Personalized learning path: 4 skills organized into 2 phases (~5 weeks). 
75% of skills recommended by association-rule models. Focus on Foundation skills 
first, then advance to Expert level.

Phase 1: 🎯 Foundation Skills (Easy, 4 weeks)
  • Machine Learning: 85% (importance: 90%, model: 80%, sources: A1, A3)
  • Spark: 75% (importance: 75%, model: 75%, sources: A1, A3)

Phase 2: ⚡ Intermediate Skills (Medium, 1 week)
  • AWS: 40% (importance: 80%, model: 0%, sources: Gap-only)

Model Coverage: 75% (3 of 4 skills have model signals)
Total Duration: 5 weeks
Algorithm: Association Rules + Gap Analysis
"""


# ============================================================================
# WHERE TO USE
# ============================================================================

# In app/main.py, Section 3:
st.header("🎓 Personalized Learning Path")
display_personalized_learning_path(user_skills, job_skills, job_title)

# In notebooks for analysis:
path = build_personalized_learning_path(...)
for phase in path['phases']:
    print(f"Phase {phase['phase_number']}: {len(phase['skills'])} skills")

# In backend API:
path = build_personalized_learning_path(...)
return jsonify(path)  # Flask/FastAPI response


# ============================================================================
# IMPORTANT: Files Required in data/processed/
# ============================================================================

# association_rules_skills.csv (308 rules)
# association_rules_categories.csv (22 rules)
# association_rules_combined.csv (7,147 rules)

# All three should exist for full functionality
# If missing: graceful degradation, uses available models
"""
