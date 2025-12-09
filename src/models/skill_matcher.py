"""
Optimized Skill Matcher - Fast Gap Analysis

Analyzes skill gaps with:
- O(1) skill lookups using sets
- Priority-based missing skill ordering
- Category-aware recommendations
"""

import pandas as pd
from typing import List, Dict, Set, Optional, Tuple
import numpy as np


class SkillMatcher:
    """Fast skill gap analysis and matching"""
    
    def __init__(self, skill_to_category: Optional[Dict[str, str]] = None):
        """
        Initialize SkillMatcher.
        
        Args:
            skill_to_category: Mapping of skill names to their categories
        """
        self.skill_to_category = skill_to_category or {}
        # Create normalized map for case-insensitive lookups
        self.skill_to_category_lower = {
            k.lower().strip(): v.lower().strip()
            for k, v in skill_to_category.items()
        }
    
    def analyze_gap(
        self,
        user_skills: List[str],
        target_job_skills: List[str],
        rules_df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Fast gap analysis with priority scoring.
        
        Args:
            user_skills: User's current skills
            target_job_skills: Skills required for target job
            rules_df: Optional association rules for priority calculation
            
        Returns:
            Dict with:
            - matching: skills user has
            - missing: skills user needs
            - extra: skills user has but not required
            - coverage: percentage of required skills user has
            - gap_priority: ordered list of missing skills by priority
            - skill_importance: importance score for each missing skill
        """
        # Normalize to lowercase sets for fast comparison
        user_skills_set = {s.lower().strip() for s in user_skills if s}
        target_skills_set = {s.lower().strip() for s in target_job_skills if s}
        
        # Calculate gaps
        matching = user_skills_set & target_skills_set
        missing = target_skills_set - user_skills_set
        extra = user_skills_set - target_skills_set
        
        # Calculate coverage
        coverage = len(matching) / len(target_skills_set) if target_skills_set else 0.0
        
        # Prioritize missing skills
        gap_priority = self._prioritize_missing_skills(
            missing, target_skills_set, rules_df
        )
        
        # Score skill importance
        skill_importance = self._calculate_skill_importance(
            gap_priority, rules_df
        )
        
        return {
            'matching': sorted(list(matching)),
            'missing': sorted(list(missing)),
            'extra': sorted(list(extra)),
            'coverage': coverage,
            'coverage_percentage': round(coverage * 100, 1),
            'gap_priority': gap_priority,
            'skill_importance': skill_importance,
            'matching_count': len(matching),
            'missing_count': len(missing),
            'total_required': len(target_skills_set)
        }
    
    def _prioritize_missing_skills(
        self,
        missing_skills: Set[str],
        all_target_skills: Set[str],
        rules_df: Optional[pd.DataFrame] = None
    ) -> List[str]:
        """
        Prioritize missing skills using:
        1. Unlocks (how many other skills depend on this skill)
        2. Frequency in job market
        3. Prerequisite status
        
        Returns:
            List of missing skills sorted by priority (highest first)
        """
        if not missing_skills:
            return []
        
        skill_scores = {}
        
        for skill in missing_skills:
            score = 0.0
            
            # Factor 1: Is this skill a prerequisite? (boost score)
            if rules_df is not None and not rules_df.empty:
                try:
                    # Find rules where this skill is antecedent (prerequisite)
                    prerequisite_rules = 0
                    for _, rule in rules_df.iterrows():
                        try:
                            antecedents = set(eval(str(rule.get('antecedents', '{}'))))
                            consequents = set(eval(str(rule.get('consequents', '{}'))))
                            
                            if skill in antecedents:
                                # This skill leads to other skills
                                unlocks = len(consequents & all_target_skills)
                                score += unlocks * 0.3
                                prerequisite_rules += 1
                        except:
                            pass
                    
                    # Factor 2: Confidence of rules (quality indicator)
                    if prerequisite_rules > 0:
                        avg_confidence = rules_df[
                            rules_df['antecedents'].astype(str).str.contains(skill, na=False)
                        ]['confidence'].mean()
                        if pd.notna(avg_confidence):
                            score += avg_confidence * 0.4
                except:
                    pass
            
            # Factor 3: Base priority (newer/more modern skills get boost)
            modern_skills = {
                'python', 'javascript', 'docker', 'kubernetes', 'aws',
                'machine learning', 'tensorflow', 'react', 'go', 'rust'
            }
            if skill in modern_skills:
                score += 0.2
            
            # Factor 4: Foundational skills (get highest priority)
            foundational = {'sql', 'git', 'communication', 'problem solving'}
            if skill in foundational:
                score += 0.5
            
            # All missing skills start with base score
            score += 0.5
            
            skill_scores[skill] = score
        
        # Sort by score (descending)
        return sorted(missing_skills, key=lambda s: skill_scores.get(s, 0.5), reverse=True)
    
    def _calculate_skill_importance(
        self,
        skills: List[str],
        rules_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        Calculate importance score (0-1) for each skill.
        
        Importance is based on:
        - How many other required skills depend on it
        - Frequency in job market
        - Complexity level
        """
        importance = {}
        
        for i, skill in enumerate(skills):
            # Higher position in priority list = higher importance
            importance[skill] = max(0.3, 1.0 - (i / max(len(skills), 1)) * 0.7)
        
        return importance
    
    def get_category_distribution(self, skills: List[str]) -> Dict[str, int]:
        """Get distribution of skills by category"""
        distribution = {}
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            category = self.skill_to_category_lower.get(skill_lower, 'other')
            distribution[category] = distribution.get(category, 0) + 1
        
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    def get_learning_path(
        self,
        missing_skills: List[str],
        max_skills_per_phase: int = 3
    ) -> List[List[str]]:
        """
        Create learning phases (groups) for missing skills.
        
        Args:
            missing_skills: List of missing skills (should be prioritized)
            max_skills_per_phase: Max skills to learn per phase
            
        Returns:
            List of skill groups (phases)
        """
        if not missing_skills:
            return []
        
        # Group skills by category to create coherent learning paths
        category_skills = {}
        uncategorized = []
        
        for skill in missing_skills:
            skill_lower = skill.lower().strip()
            category = self.skill_to_category_lower.get(skill_lower, None)
            
            if category:
                if category not in category_skills:
                    category_skills[category] = []
                category_skills[category].append(skill)
            else:
                uncategorized.append(skill)
        
        # Build phases
        phases = []
        current_phase = []
        
        # Add one skill from each category to ensure diversity
        for category, skills in sorted(category_skills.items()):
            for skill in skills:
                current_phase.append(skill)
                if len(current_phase) >= max_skills_per_phase:
                    phases.append(current_phase)
                    current_phase = []
        
        # Add uncategorized skills
        for skill in uncategorized:
            current_phase.append(skill)
            if len(current_phase) >= max_skills_per_phase:
                phases.append(current_phase)
                current_phase = []
        
        # Add remaining skills
        if current_phase:
            phases.append(current_phase)
        
        return phases if phases else [missing_skills[:max_skills_per_phase]]
    
    def estimate_learning_time(self, missing_skills: List[str]) -> Dict:
        """
        Estimate time to learn missing skills.
        
        Returns:
            Dict with total hours and breakdown by category
        """
        # Estimated learning hours per skill (domain knowledge)
        skill_hours = {
            'python': 100,
            'javascript': 80,
            'sql': 60,
            'machine learning': 200,
            'deep learning': 250,
            'tensorflow': 120,
            'pytorch': 120,
            'aws': 100,
            'docker': 50,
            'kubernetes': 80,
            'react': 80,
            'node.js': 80,
            'django': 100,
            'flask': 60,
            'git': 30,
            'agile': 40,
            'communication': 20
        }
        
        # Default hours for unknown skills
        default_hours = 80
        
        category_time = {}
        total_hours = 0
        
        for skill in missing_skills:
            skill_lower = skill.lower().strip()
            hours = skill_hours.get(skill_lower, default_hours)
            total_hours += hours
            
            category = self.skill_to_category_lower.get(skill_lower, 'other')
            category_time[category] = category_time.get(category, 0) + hours
        
        # Estimate weeks (assuming 10 hours/week)
        total_weeks = total_hours / 10
        
        return {
            'total_hours': total_hours,
            'total_weeks': round(total_weeks),
            'total_months': round(total_weeks / 4, 1),
            'by_category': dict(sorted(category_time.items(), key=lambda x: x[1], reverse=True)),
            'skills_count': len(missing_skills)
        }
