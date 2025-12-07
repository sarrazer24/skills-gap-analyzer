"""Skill gap analysis logic"""
import pandas as pd
from typing import List, Dict, Set, Tuple
import numpy as np


class SkillGapAnalyzer:
    def __init__(self, skill_to_category: Dict[str, str] = None):
        """Initialize with skill to category mapping"""
        self.skill_to_category = skill_to_category or {}
    
    def analyze_gap(self, user_skills: List[str], job_skills: List[str]) -> Dict:
        """Analyze skill gap between user and job"""
        user_set = set(s.lower().strip() for s in user_skills)
        job_set = set(s.lower().strip() for s in job_skills)
        
        # Calculate metrics
        matching_skills = user_set & job_set
        missing_skills = job_set - user_set
        extra_skills = user_set - job_set
        
        # Match percentage
        if len(job_set) == 0:
            match_percentage = 0.0
        else:
            match_percentage = (len(matching_skills) / len(job_set)) * 100
        
        # Categorize skills
        matching_by_category = self._categorize_skills(matching_skills)
        missing_by_category = self._categorize_skills(missing_skills)
        extra_by_category = self._categorize_skills(extra_skills)
        
        # Find transferable skills
        transferable = self._find_transferable_skills(extra_skills, missing_skills)
        
        # Priority missing skills (based on frequency in similar jobs)
        priority_missing = self._prioritize_skills(missing_skills)
        
        return {
            'match_percentage': round(match_percentage, 1),
            'matching_skills': sorted(list(matching_skills)),
            'missing_skills': sorted(list(missing_skills)),
            'extra_skills': sorted(list(extra_skills)),
            'matching_by_category': matching_by_category,
            'missing_by_category': missing_by_category,
            'extra_by_category': extra_by_category,
            'transferable_skills': transferable,
            'priority_missing': priority_missing,
            'total_job_skills': len(job_set),
            'total_matching': len(matching_skills),
            'total_missing': len(missing_skills),
            'total_extra': len(extra_skills)
        }
    
    def rank_jobs_by_match(self, user_skills: List[str], jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Rank all jobs by skill match percentage"""
        user_set = set(s.lower().strip() for s in user_skills)
        
        def calculate_match(job_skills):
            if not job_skills or len(job_skills) == 0:
                return 0.0
            
            if isinstance(job_skills, str):
                # Parse string representation of list
                import ast
                try:
                    job_skills = ast.literal_eval(job_skills)
                except:
                    job_skills = [s.strip() for s in job_skills.split(',')]
            
            if not isinstance(job_skills, list):
                return 0.0
            
            job_set = set(s.lower().strip() for s in job_skills if s)
            
            if len(job_set) == 0:
                return 0.0
            
            matching = len(user_set & job_set)
            return (matching / len(job_set)) * 100
        
        jobs_df = jobs_df.copy()
        jobs_df['match_percentage'] = jobs_df['skill_list'].apply(calculate_match)
        jobs_df = jobs_df.sort_values('match_percentage', ascending=False)
        
        return jobs_df
    
    def _categorize_skills(self, skills: Set[str]) -> Dict[str, List[str]]:
        """Group skills by category"""
        categorized = {}
        for skill in skills:
            category = self.skill_to_category.get(skill, 'other')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(skill)
        
        # Sort skills within each category
        for category in categorized:
            categorized[category] = sorted(categorized[category])
        
        return categorized
    
    def _find_transferable_skills(self, user_skills: Set[str], missing_skills: Set[str]) -> List[Dict]:
        """Find user's skills that are transferable to missing skills"""
        transferable = []
        
        # Get categories of missing skills
        missing_categories = {}
        for skill in missing_skills:
            cat = self.skill_to_category.get(skill, 'other')
            if cat not in missing_categories:
                missing_categories[cat] = []
            missing_categories[cat].append(skill)
        
        # Find user skills in those categories
        for user_skill in user_skills:
            cat = self.skill_to_category.get(user_skill, 'other')
            if cat in missing_categories:
                for missing_skill in missing_categories[cat]:
                    transferable.append({
                        'user_skill': user_skill,
                        'category': cat,
                        'missing_skill': missing_skill,
                        'transfer_score': self._calculate_transfer_score(user_skill, missing_skill)
                    })
        
        # Sort by transfer score
        transferable.sort(key=lambda x: x['transfer_score'], reverse=True)
        return transferable
    
    def _calculate_transfer_score(self, user_skill: str, missing_skill: str) -> float:
        """Calculate how transferable a skill is (0-1)"""
        # Simple implementation - can be enhanced with semantic similarity
        user_lower = user_skill.lower()
        missing_lower = missing_skill.lower()
        
        if user_lower in missing_lower or missing_lower in user_lower:
            return 0.8
        
        # Check for common prefixes/suffixes
        common_words = ['python', 'java', 'sql', 'aws', 'cloud']
        for word in common_words:
            if word in user_lower and word in missing_lower:
                return 0.6
        
        return 0.5
    
    def _prioritize_skills(self, missing_skills: Set[str]) -> List[Dict]:
        """Prioritize missing skills based on importance"""
        # Simple priority based on category
        category_priority = {
            'programming': 1.0,
            'tech skills': 0.9,
            'machine_learning': 0.9,
            'databases': 0.8,
            'cloud': 0.8,
            'devops': 0.7,
            'visualization': 0.6,
            'tools': 0.5,
            'business skills': 0.4,
            'soft_skills': 0.4,
            'other': 0.3
        }
        
        prioritized = []
        for skill in missing_skills:
            category = self.skill_to_category.get(skill, 'other')
            priority = category_priority.get(category.lower(), 0.5)
            prioritized.append({
                'skill': skill,
                'category': category,
                'priority': priority,
                'learning_resources': self._get_learning_resources(skill)
            })
        
        # Sort by priority
        prioritized.sort(key=lambda x: x['priority'], reverse=True)
        return prioritized
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """Get learning resources for a skill"""
        resources = {
            'python': ['Python.org', 'Coursera: Python for Everybody', 'Codecademy Python'],
            'sql': ['W3Schools SQL', 'Khan Academy SQL', 'SQLZoo'],
            'machine learning': ['Coursera: ML by Andrew Ng', 'fast.ai', 'Kaggle Learn'],
            'aws': ['AWS Training', 'A Cloud Guru', 'Linux Academy'],
            'docker': ['Docker Documentation', 'Docker Mastery on Udemy', 'Play with Docker'],
            'tableau': ['Tableau Training', 'Tableau Public', 'Udemy Tableau Courses'],
            'javascript': ['MDN Web Docs', 'JavaScript.info', 'FreeCodeCamp'],
            'react': ['React Documentation', 'React Tutorial on React.dev', 'Full Stack Open']
        }
        
        skill_lower = skill.lower()
        for key, value in resources.items():
            if key in skill_lower:
                return value
        
        return ['Online courses', 'Documentation', 'Practice projects']

