import pandas as pd
import ast
import os
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import numpy as np

class DataLoader:
    """Optimized data loader for fast skill extraction and job loading"""

    def __init__(self, use_sample=False, cache_dir=None):
        self.use_sample = use_sample
        self.base_path = Path(__file__).parent.parent.parent
        self.cache_dir = cache_dir or (self.base_path / '.cache')
        self.cache_dir.mkdir(exist_ok=True)
        self._skills_cache = None
        self._jobs_cache = None

    def load_skills_taxonomy(self, force_reload=False):
        """Load skills taxonomy efficiently with caching"""
        if self._skills_cache is not None and not force_reload:
            return self._skills_cache
        
        skill_files = [
            self.base_path / 'data' / 'processed' / 'skill_migration_clean.csv',
            self.base_path / 'data' / 'processed' / 'minimal_skills.csv'
        ]
        
        for skill_file in skill_files:
            if os.path.exists(skill_file):
                try:
                    df = pd.read_csv(skill_file)
                    # Normalize columns
                    if 'skill_group_name' in df.columns:
                        df['skill_group_name'] = df['skill_group_name'].str.lower().str.strip()
                    if 'skill_group_category' in df.columns:
                        df['skill_group_category'] = df['skill_group_category'].str.lower().str.strip()
                    self._skills_cache = df
                    return df
                except Exception as e:
                    print(f"⚠️  Error loading {skill_file}: {e}")
                    continue
        
        # Fallback: Return comprehensive default skills
        default_skills = {
            'skill_group_name': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go',
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                'react', 'angular', 'vue', 'node.js', 'django', 'flask',
                'git', 'jenkins', 'gitlab', 'github', 'terraform',
                'excel', 'tableau', 'power bi', 'pandas', 'numpy',
                'api', 'rest', 'graphql', 'microservices', 'devops'
            ],
            'skill_group_category': [
                'programming', 'programming', 'programming', 'programming', 'programming', 'programming', 'programming', 'programming',
                'databases', 'databases', 'databases', 'databases', 'databases',
                'machine_learning', 'machine_learning', 'machine_learning', 'machine_learning', 'machine_learning',
                'cloud', 'cloud', 'cloud', 'devops', 'devops',
                'web_development', 'web_development', 'web_development', 'web_development', 'web_development', 'web_development',
                'devops', 'devops', 'devops', 'devops', 'devops',
                'tools', 'tools', 'tools', 'data_science', 'data_science',
                'api', 'api', 'api', 'architecture', 'devops'
            ]
        }
        
        df = pd.DataFrame(default_skills)
        self._skills_cache = df
        return df

    def get_all_skills_fast(self) -> Set[str]:
        """Get ALL skills from both taxonomy and job listings as a set for O(1) lookup"""
        all_skills = set()
        
        # 1. Add skills from taxonomy
        skills_df = self.load_skills_taxonomy()
        if not skills_df.empty and 'skill_group_name' in skills_df.columns:
            taxonomy_skills = set(skills_df['skill_group_name'].str.lower().str.strip().unique())
            all_skills.update(taxonomy_skills)
        
        # 2. Add skills from actual job listings
        try:
            job_files = [
                self.base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
                self.base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
                self.base_path / 'data' / 'raw' / 'all_jobs.csv'
            ]
            
            for job_file in job_files:
                if os.path.exists(job_file):
                    try:
                        # Load skills from job data
                        df = pd.read_csv(job_file, usecols=['skill_list'], nrows=10000, low_memory=False)
                        
                        # Extract unique skills
                        for skill_str in df['skill_list'].dropna():
                            skills = self._parse_skill_list_fast(skill_str)
                            all_skills.update(skills)
                        
                        break  # Found a valid file, stop searching
                    except Exception as e:
                        print(f"⚠️  Could not extract skills from {job_file.name}: {e}")
                        continue
        except Exception as e:
            print(f"⚠️  Error loading job skills: {e}")
        
        return all_skills

    def get_skill_to_category_map(self) -> Dict[str, str]:
        """Build skill -> category mapping for fast lookups"""
        skills_df = self.load_skills_taxonomy()
        return dict(zip(
            skills_df['skill_group_name'].str.lower().str.strip(),
            skills_df['skill_group_category'].str.lower().str.strip()
        ))

    def load_jobs_data(self, sample_size=5000, return_all_titles=False):
        """Load jobs efficiently with smart sampling
        
        Args:
            sample_size: Max number of jobs to load (5000 is a good balance)
            return_all_titles: If True, return list of all available job titles
        
        Returns:
            DataFrame with columns: job_title, skill_list, company, location
        """
        possible_paths = [
            self.base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
            self.base_path / 'data' / 'processed' / 'all_jobs_clustered_sample_dbscan.csv',
            self.base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
            self.base_path / 'data' / 'raw' / 'all_jobs.csv'
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"📂 Loading jobs from {file_path.name} ({file_size:.1f}MB)...")
                    
                    # Load with optimized settings
                    df = pd.read_csv(
                        file_path,
                        nrows=sample_size if sample_size else None,
                        dtype={'job_title': 'string', 'company': 'string', 'location': 'string'},
                        low_memory=False
                    )
                    
                    # Ensure skill_list is parsed
                    if 'skill_list' in df.columns:
                        df['skill_list'] = df['skill_list'].apply(self._parse_skill_list_fast)
                    else:
                        df['skill_list'] = [[]] * len(df)
                    
                    # Clean job titles
                    if 'job_title' in df.columns:
                        df['job_title'] = df['job_title'].str.strip().str.title()
                        df = df[df['job_title'].str.len() >= 3]
                        df = df[df['job_title'] != 'Nan']
                    
                    # Ensure required columns exist
                    for col in ['company', 'location']:
                        if col not in df.columns:
                            df[col] = 'Unknown'
                    
                    print(f"✅ Loaded {len(df):,} jobs")
                    return df
                    
                except Exception as e:
                    print(f"⚠️  Error loading {file_path.name}: {e}")
                    continue
        
        # Fallback to sample data
        print("📊 No jobs file found, using sample data...")
        return self._get_sample_jobs()

    def _parse_skill_list_fast(self, skill_str):
        """Fast skill list parsing"""
        if pd.isna(skill_str):
            return []
        
        if isinstance(skill_str, list):
            return [str(s).lower().strip() for s in skill_str if s]
        
        # Try literal_eval first
        if isinstance(skill_str, str):
            try:
                parsed = ast.literal_eval(skill_str)
                if isinstance(parsed, list):
                    return [str(s).lower().strip() for s in parsed if s]
            except:
                pass
            
            # Fallback: split by comma
            return [s.lower().strip() for s in str(skill_str).split(',') if s.strip()]
        
        return []

    def _get_sample_jobs(self):
        """Return sample jobs for testing"""
        return pd.DataFrame({
            'job_title': [
                'Data Scientist', 'Machine Learning Engineer', 'Data Analyst',
                'Python Developer', 'Software Engineer', 'DevOps Engineer',
                'Business Analyst', 'Full Stack Developer', 'Data Engineer', 'Cloud Architect'
            ],
            'skill_list': [
                ['python', 'sql', 'machine learning', 'pandas', 'numpy'],
                ['python', 'machine learning', 'tensorflow', 'pytorch', 'docker'],
                ['sql', 'excel', 'tableau', 'python', 'statistics'],
                ['python', 'django', 'flask', 'sql', 'git'],
                ['javascript', 'react', 'node.js', 'sql', 'git'],
                ['docker', 'kubernetes', 'aws', 'jenkins', 'terraform'],
                ['excel', 'sql', 'tableau', 'power bi', 'analytics'],
                ['javascript', 'react', 'node.js', 'mongodb', 'aws'],
                ['python', 'sql', 'aws', 'spark', 'hadoop'],
                ['aws', 'kubernetes', 'terraform', 'docker', 'devops']
            ],
            'company': ['Tech Corp'] * 10,
            'location': ['Remote'] * 10
        })

    def load_association_rules(self, rule_type='categories') -> pd.DataFrame:
        """Load association rules for skill recommendations
        
        Args:
            rule_type: 'skills', 'categories', or 'combined'
        
        Returns:
            DataFrame with columns: antecedents, consequents, support, confidence, lift
        """
        rule_files = {
            'skills': self.base_path / 'data' / 'processed' / 'association_rules_skills.csv',
            'categories': self.base_path / 'data' / 'processed' / 'association_rules_categories.csv',
            'combined': self.base_path / 'data' / 'processed' / 'association_rules_combined.csv'
        }
        
        rule_file = rule_files.get(rule_type)
        
        if rule_file and os.path.exists(rule_file):
            try:
                rules = pd.read_csv(rule_file)
                print(f"✅ Loaded {len(rules):,} {rule_type} association rules")
                return rules
            except Exception as e:
                print(f"⚠️  Error loading {rule_type} rules: {e}")
        
        # Return empty if not found
        return pd.DataFrame(columns=['antecedents', 'consequents', 'support', 'confidence', 'lift'])

    def load_skills_metadata(self) -> pd.DataFrame:
        """Load enriched skill metadata (difficulty, time, category, priority)"""
        metadata_file = self.base_path / 'data' / 'processed' / 'skills_enriched.csv'
        
        if os.path.exists(metadata_file):
            try:
                return pd.read_csv(metadata_file)
            except Exception as e:
                print(f"⚠️  Error loading skills metadata: {e}")
        
        return pd.DataFrame()

    def validate_data_structure(self, df):
        """Check if DataFrame has required columns"""
        required_columns = ['job_title', 'skill_list']
        return all(col in df.columns for col in required_columns)
