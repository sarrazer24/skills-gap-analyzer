"""
Skill Gap Analyzer Module

Analyzes skill gaps between current and required skills for roles.
"""

from typing import Dict, List, Optional


class SkillGapAnalyzer:
    """Analyze gaps between user skills and required skills for roles."""
    
    def __init__(self, skill_to_category_map: Optional[Dict[str, str]] = None):
        """
        Initialize SkillGapAnalyzer.
        
        Args:
            skill_to_category_map: Mapping of skill names to their categories
        """
        self.skill_to_category_map = skill_to_category_map or {}
    
    def analyze_gap(self, user_skills: List[str], required_skills: List[str]) -> Dict:
        """
        Analyze the gap between user skills and required skills.
        
        Args:
            user_skills: List of user's current skills
            required_skills: List of skills required for the role
            
        Returns:
            Dictionary with gap analysis results
        """
        user_skills_set = set(s.lower().strip() for s in user_skills)
        required_skills_set = set(s.lower().strip() for s in required_skills)
        
        missing_skills = required_skills_set - user_skills_set
        matching_skills = required_skills_set & user_skills_set
        extra_skills = user_skills_set - required_skills_set
        
        coverage = len(matching_skills) / len(required_skills_set) if required_skills_set else 0
        
        return {
            'matching': list(matching_skills),
            'missing': list(missing_skills),
            'extra': list(extra_skills),
            'coverage': coverage,
            'gap_count': len(missing_skills)
        }
    
    def get_skill_category(self, skill: str) -> Optional[str]:
        """Get the category of a skill."""
        return self.skill_to_category_map.get(skill.lower().strip())
