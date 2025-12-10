"""UI Components for Skills Gap Analyzer.

This package contains reusable Streamlit UI components for the main app.
Each module handles rendering one major section of the app.
"""

from .hero import render_hero
from .profile_section import render_profile
from .gap_section import render_gap_analysis
from .recommendations_section import render_recommendations
from .learning_path_section import render_learning_path
from .similar_opportunities_section import render_similar_opportunities

__all__ = [
    "render_hero",
    "render_profile",
    "render_gap_analysis",
    "render_recommendations",
    "render_learning_path",
    "render_similar_opportunities",
]
