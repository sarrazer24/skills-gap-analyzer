"""
Skill Metadata Enrichment

Creates enriched skill metadata with:
- Difficulty levels (Easy/Medium/Hard)
- Estimated learning time (weeks)
- Category classification
- Priority scoring (from association rules)
- Course links and learning resources
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import ast
import warnings
warnings.filterwarnings('ignore')


class SkillMetadataEnricher:
    """Enrich skills with metadata for recommendations"""
    
    # Default difficulty levels
    DEFAULT_DIFFICULTY = {
        # Programming Languages
        'python': 'Medium', 'java': 'Hard', 'javascript': 'Medium', 'c++': 'Hard',
        'c#': 'Hard', 'r': 'Medium', 'php': 'Medium', 'ruby': 'Easy', 'go': 'Hard',
        'rust': 'Hard', 'scala': 'Hard', 'swift': 'Medium', 'kotlin': 'Medium',
        
        # Databases
        'sql': 'Easy', 'mysql': 'Easy', 'postgresql': 'Easy', 'mongodb': 'Easy',
        'redis': 'Medium', 'cassandra': 'Hard', 'oracle': 'Hard', 'sqlite': 'Easy',
        'dynamodb': 'Medium', 'elasticsearch': 'Medium',
        
        # Cloud & DevOps
        'aws': 'Medium', 'azure': 'Medium', 'gcp': 'Medium', 'docker': 'Medium',
        'kubernetes': 'Hard', 'terraform': 'Medium', 'ansible': 'Medium',
        'jenkins': 'Medium', 'gitlab': 'Medium', 'github': 'Easy',
        
        # Data Science & ML
        'machine learning': 'Hard', 'deep learning': 'Hard', 'nlp': 'Hard',
        'computer vision': 'Hard', 'tensorflow': 'Hard', 'pytorch': 'Hard',
        'keras': 'Hard', 'scikit-learn': 'Medium', 'pandas': 'Easy',
        'numpy': 'Easy', 'scipy': 'Medium', 'statsmodels': 'Medium',
        
        # Web Development
        'html': 'Easy', 'css': 'Easy', 'react': 'Medium', 'angular': 'Hard',
        'vue': 'Medium', 'node.js': 'Medium', 'django': 'Medium', 'flask': 'Easy',
        'fastapi': 'Medium', 'spring': 'Hard', 'asp.net': 'Hard',
        
        # Big Data
        'spark': 'Hard', 'hadoop': 'Hard', 'hive': 'Medium', 'pig': 'Medium',
        'mapreduce': 'Hard', 'scala spark': 'Hard',
        
        # Visualization
        'tableau': 'Easy', 'power bi': 'Easy', 'looker': 'Medium',
        'qlik': 'Medium', 'matplotlib': 'Easy', 'plotly': 'Easy',
        
        # Tools & Soft Skills
        'git': 'Easy', 'linux': 'Medium', 'unix': 'Medium', 'jira': 'Easy',
        'agile': 'Easy', 'scrum': 'Easy', 'excel': 'Easy', 'vba': 'Medium',
        'communication': 'Easy', 'leadership': 'Easy', 'teamwork': 'Easy',
        'problem solving': 'Medium', 'time management': 'Easy', 'project management': 'Medium',
    }
    
    # Default learning time in weeks
    DEFAULT_TIME_WEEKS = {
        # Programming (hours to weeks: 40-50 hrs/week)
        'python': 8, 'java': 12, 'javascript': 10, 'c++': 16,
        'c#': 12, 'r': 8, 'php': 6, 'ruby': 6, 'go': 10, 'rust': 14,
        
        # Databases
        'sql': 3, 'mysql': 4, 'postgresql': 4, 'mongodb': 4,
        'redis': 3, 'cassandra': 10, 'oracle': 12, 'sqlite': 2,
        'dynamodb': 4, 'elasticsearch': 6,
        
        # Cloud & DevOps
        'aws': 10, 'azure': 10, 'gcp': 10, 'docker': 6,
        'kubernetes': 12, 'terraform': 8, 'ansible': 6,
        'jenkins': 6, 'gitlab': 4, 'github': 2,
        
        # Data Science & ML
        'machine learning': 16, 'deep learning': 20, 'nlp': 16,
        'computer vision': 18, 'tensorflow': 12, 'pytorch': 12,
        'keras': 8, 'scikit-learn': 6, 'pandas': 4, 'numpy': 3,
        
        # Web Development
        'html': 1, 'css': 2, 'react': 8, 'angular': 12,
        'vue': 6, 'node.js': 8, 'django': 10, 'flask': 6,
        
        # Big Data
        'spark': 12, 'hadoop': 14, 'hive': 8, 'pig': 6,
        'mapreduce': 10,
        
        # Visualization
        'tableau': 4, 'power bi': 4, 'looker': 6, 'qlik': 6,
        
        # Tools
        'git': 2, 'linux': 8, 'unix': 8, 'jira': 2,
        'agile': 2, 'scrum': 2, 'excel': 3, 'vba': 4,
        
        # Soft skills
        'communication': 4, 'leadership': 8, 'teamwork': 2,
        'problem solving': 6, 'time management': 2, 'project management': 6,
    }
    
    # Default course suggestions
    DEFAULT_COURSES = {
        'python': ['Codecademy Python', 'Real Python', 'Coursera Python for Data Science', 'DataCamp Python'],
        'sql': ['Khan Academy SQL', 'Mode Analytics SQL', 'Udemy SQL', 'DataCamp SQL'],
        'machine learning': ['Fast.ai ML', 'Coursera ML by Andrew Ng', 'Kaggle ML Competitions', 'Udacity ML'],
        'aws': ['AWS Training & Certification', 'A Cloud Guru', 'Linux Academy AWS', 'Pluralsight AWS'],
        'docker': ['Docker Official Documentation', 'Pluralsight Docker', 'Udemy Docker Mastery', 'KataCoda'],
        'kubernetes': ['Linux Foundation CKA', 'Kubernetes Official', 'Pluralsight K8s', 'Udemy Kubernetes'],
        'react': ['React Official Documentation', 'Codecademy React', 'Scrimba React', 'Udemy React'],
        'javascript': ['MDN Web Docs', 'Codecademy JavaScript', 'Udemy JavaScript', 'JavaScript.info'],
        'git': ['GitHub Learning', 'Codecademy Git', 'Udemy Git', 'Atlassian Git Tutorials'],
        'tableau': ['Tableau Official Training', 'Udemy Tableau', 'Pluralsight Tableau', 'Maven Analytics'],
    }
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent
        self.association_rules_a1 = None  # Will load from CSV
    
    def _load_association_rules(self, rules_file: str = None) -> pd.DataFrame:
        """Load association rules for priority scoring"""
        if rules_file is None:
            rules_file = self.base_path / 'data' / 'processed' / 'association_rules_skills.csv'
        
        if not Path(rules_file).exists():
            print(f"⚠️  Association rules file not found: {rules_file}")
            return pd.DataFrame()
        
        try:
            rules = pd.read_csv(rules_file)
            print(f"✅ Loaded {len(rules)} association rules")
            return rules
        except Exception as e:
            print(f"⚠️  Error loading rules: {e}")
            return pd.DataFrame()
    
    def _parse_frozenset(self, s):
        """Parse frozenset string to list of items"""
        if pd.isna(s):
            return []
        if isinstance(s, list):
            return s
        s = str(s).strip()
        if s.startswith("frozenset({") and s.endswith("})"):
            # Parse frozenset format: frozenset({'item1', 'item2'})
            try:
                s = s.replace("frozenset(", "").replace(")", "")
                items = ast.literal_eval(s)
                return list(items) if isinstance(items, (set, frozenset)) else [items]
            except:
                return []
        return []
    
    def _calculate_skill_priority(self, skill: str, rules_df: pd.DataFrame) -> float:
        """Calculate priority score from association rules
        
        Priority = average lift of rules where skill is consequent
        High lift = skill is strongly recommended after other skills
        """
        if rules_df.empty:
            return 0.5  # Default middle priority
        
        skill_lower = str(skill).lower().strip()
        
        # Find rules where this skill is the consequent
        matching_rules = []
        for idx, row in rules_df.iterrows():
            try:
                consequents = self._parse_frozenset(row['consequents'])
                if any(c.lower().strip() == skill_lower for c in consequents):
                    matching_rules.append(row)
            except:
                continue
        
        if not matching_rules:
            return 0.5  # Default priority
        
        # Calculate average lift, confidence, and support
        avg_lift = np.mean([r.get('lift', 1.0) for r in matching_rules if pd.notna(r.get('lift'))])
        avg_confidence = np.mean([r.get('confidence', 0.5) for r in matching_rules if pd.notna(r.get('confidence'))])
        
        # Priority = normalized lift * confidence
        # Normalize lift to 0-1 (lift > 2 is very good)
        normalized_lift = min(avg_lift / 3.0, 1.0)
        priority = (normalized_lift + avg_confidence) / 2.0
        
        return min(max(priority, 0.0), 1.0)  # Clamp to 0-1
    
    def enrich_skills(
        self,
        output_file: str = None,
        source_skills: List[str] = None,
        rules_file: str = None
    ) -> pd.DataFrame:
        """
        Create enriched skill metadata.
        
        Args:
            output_file: Path to save enriched metadata CSV
            source_skills: List of skills to enrich (if None, uses all known skills)
            rules_file: Path to association rules for priority scoring
        
        Returns:
            DataFrame with enriched skill metadata
        """
        
        if output_file is None:
            output_file = self.base_path / 'data' / 'processed' / 'skills_enriched.csv'
        
        # Load association rules for priority scoring
        rules_df = self._load_association_rules(rules_file)
        
        # Collect all unique skills from metadata
        if source_skills is None:
            source_skills = set()
            source_skills.update(self.DEFAULT_DIFFICULTY.keys())
            source_skills.update(self.DEFAULT_TIME_WEEKS.keys())
            source_skills.update(self.DEFAULT_COURSES.keys())
        
        source_skills = sorted(list(set(s.lower().strip() for s in source_skills)))
        print(f"📊 Enriching {len(source_skills)} unique skills...")
        
        enriched_data = []
        
        for skill in source_skills:
            skill_lower = skill.lower().strip()
            
            # Get metadata with defaults
            difficulty = self.DEFAULT_DIFFICULTY.get(skill_lower, 'Medium')
            weeks = self.DEFAULT_TIME_WEEKS.get(skill_lower, 6)
            courses = self.DEFAULT_COURSES.get(skill_lower, [f'Udemy {skill}', f'Coursera {skill}'])
            
            # Calculate priority from rules
            priority_score = self._calculate_skill_priority(skill, rules_df)
            
            # Determine category
            category = self._determine_category(skill_lower)
            
            enriched_data.append({
                'skill': skill,
                'category': category,
                'difficulty': difficulty,
                'estimated_weeks': weeks,
                'estimated_hours': weeks * 40,  # Assuming 40 hrs/week
                'priority_score': round(priority_score, 3),
                'priority_level': self._get_priority_level(priority_score),
                'courses': ', '.join(courses[:3]),  # Top 3 courses
                'num_courses': len(courses),
            })
        
        enriched_df = pd.DataFrame(enriched_data)
        
        # Sort by priority
        enriched_df = enriched_df.sort_values('priority_score', ascending=False)
        
        # Save to CSV
        print(f"\n💾 Saving enriched metadata to {output_file}...")
        enriched_df.to_csv(output_file, index=False)
        print(f"✅ Saved {len(enriched_df)} enriched skills")
        
        # Print summary
        print("\n📈 Summary Statistics:")
        print(f"   Total skills: {len(enriched_df)}")
        print(f"   By difficulty:")
        for diff in ['Easy', 'Medium', 'Hard']:
            count = len(enriched_df[enriched_df['difficulty'] == diff])
            print(f"      {diff}: {count}")
        
        print(f"\n   By category:")
        for cat in enriched_df['category'].unique():
            count = len(enriched_df[enriched_df['category'] == cat])
            print(f"      {cat}: {count}")
        
        print("\n📋 Top 10 Skills by Priority:")
        for idx, row in enriched_df.head(10).iterrows():
            print(f"   {row['skill']}: {row['priority_level']} (score: {row['priority_score']:.2f})")
        
        return enriched_df
    
    def _determine_category(self, skill: str) -> str:
        """Determine skill category"""
        skill_lower = skill.lower()
        
        categories = {
            'programming': ['python', 'java', 'javascript', 'c', 'r', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin', 'swift'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle', 'sqlite', 'dynamodb'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'ansible', 'terraform'],
            'machine_learning': ['machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn'],
            'data_science': ['python', 'r', 'pandas', 'numpy', 'scipy', 'machine learning', 'statistics'],
            'web_development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask'],
            'tools': ['git', 'jira', 'excel', 'vba', 'linux', 'tableau', 'power bi'],
            'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'time management', 'agile', 'scrum'],
        }
        
        for category, skills in categories.items():
            if any(s in skill_lower for s in skills) or any(skill_lower in s for s in skills):
                return category
        
        return 'other'
    
    def _get_priority_level(self, score: float) -> str:
        """Convert numeric priority to level"""
        if score >= 0.75:
            return 'Critical'
        elif score >= 0.55:
            return 'High'
        elif score >= 0.35:
            return 'Medium'
        else:
            return 'Low'


if __name__ == '__main__':
    """Test the enricher"""
    enricher = SkillMetadataEnricher()
    
    try:
        enriched = enricher.enrich_skills()
        print("\n✅ Enrichment completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
