"""
Job-Skill Requirements Extractor

Extracts top skills required for each job title from the dataset.
This creates a mapping for gap analysis and learning recommendations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import ast
import warnings
warnings.filterwarnings('ignore')


class JobSkillExtractor:
    """Extract top skills per job title from dataset"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent
        
    def _parse_skill_list(self, skill_str):
        """Safely parse skill list from string"""
        if pd.isna(skill_str):
            return []
        if isinstance(skill_str, list):
            return skill_str
        if isinstance(skill_str, str):
            try:
                # Try literal_eval first (for Python list format)
                return ast.literal_eval(skill_str)
            except (ValueError, SyntaxError):
                # Fall back to comma split
                return [s.strip() for s in skill_str.split(',') if s.strip()]
        return []
    
    def extract_job_skills(
        self,
        input_file: str = None,
        output_file: str = None,
        top_n_skills: int = 10,
        min_job_occurrences: int = 5,
        sample_size: int = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Extract top N skills per job title.
        
        Args:
            input_file: Path to jobs data CSV (with job_title and skill_list columns)
            output_file: Path to save mapping CSV
            top_n_skills: Number of top skills to extract per job
            min_job_occurrences: Minimum job postings required to include job title
            sample_size: Limit rows loaded (None = all)
        
        Returns:
            Dictionary mapping job_title -> [(skill, frequency_score), ...]
        """
        
        # Set default paths
        if input_file is None:
            # Try different possible input files
            candidates = [
                self.base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
                self.base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
                self.base_path / 'data' / 'processed' / 'minimal_jobs.csv',
            ]
            for cand in candidates:
                if cand.exists():
                    input_file = cand
                    break
            if input_file is None:
                raise FileNotFoundError(f"No job data found in {candidates}")
        
        if output_file is None:
            output_file = self.base_path / 'data' / 'processed' / 'job_skill_mapping.csv'
        
        print(f"📥 Loading job data from {input_file}...")
        
        # Load data
        if sample_size:
            df = pd.read_csv(input_file, nrows=sample_size)
            print(f"   Loaded {len(df):,} sample rows")
        else:
            df = pd.read_csv(input_file)
            print(f"   Loaded {len(df):,} rows")
        
        # Validate required columns
        if 'job_title' not in df.columns or 'skill_list' not in df.columns:
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Parse skill lists
        print("🔍 Parsing skill lists...")
        df['skill_list'] = df['skill_list'].apply(self._parse_skill_list)
        
        # Remove rows with missing or empty job titles
        print("🧹 Cleaning job titles...")
        df = df[df['job_title'].notna()]
        df = df[df['job_title'].astype(str).str.len() >= 3]
        df = df[df['job_title'].astype(str).str.lower() != 'nan']
        df['job_title_lower'] = df['job_title'].astype(str).str.lower().str.strip()
        
        # Remove rows with empty skill lists
        df = df[df['skill_list'].apply(len) > 0]
        
        print(f"✅ After cleaning: {len(df):,} rows with valid titles and skills")
        
        # Group by job title and extract top skills
        print("📊 Extracting top skills per job...")
        job_skills_mapping = {}
        job_title_counts = df['job_title_lower'].value_counts()
        
        # Filter to jobs with min occurrences
        valid_jobs = job_title_counts[job_title_counts >= min_job_occurrences].index
        print(f"   Found {len(valid_jobs)} unique job titles (>= {min_job_occurrences} postings)")
        
        for job_title_lower in valid_jobs:
            job_data = df[df['job_title_lower'] == job_title_lower]
            
            # Collect all skills for this job and count frequencies
            skill_counts = {}
            for skills in job_data['skill_list']:
                for skill in skills:
                    skill_lower = str(skill).lower().strip()
                    skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1
            
            # Calculate frequency scores (normalize by total skill instances)
            total_skills = sum(skill_counts.values())
            skill_scores = {
                skill: count / total_skills 
                for skill, count in skill_counts.items()
            }
            
            # Sort and get top N
            top_skills = sorted(
                skill_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n_skills]
            
            # Get original case for job title (use most common one)
            original_titles = job_data['job_title'].unique()
            original_title = original_titles[0] if len(original_titles) > 0 else job_title_lower
            
            job_skills_mapping[original_title] = top_skills
        
        print(f"✅ Extracted skills for {len(job_skills_mapping)} job titles")
        
        # Convert to DataFrame for saving
        mapping_data = []
        for job_title, skills in job_skills_mapping.items():
            num_postings = len(df[df['job_title_lower'] == job_title.lower()])
            skills_str = ', '.join([f"{s} ({score:.2%})" for s, score in skills])
            skills_only = [s for s, _ in skills]
            
            mapping_data.append({
                'job_title': job_title,
                'num_postings': num_postings,
                'top_skills': ', '.join(skills_only),
                'top_skills_with_freq': skills_str,
                'skills_json': str(skills)
            })
        
        mapping_df = pd.DataFrame(mapping_data)
        mapping_df = mapping_df.sort_values('num_postings', ascending=False)
        
        # Save to CSV
        print(f"\n💾 Saving job-skill mapping to {output_file}...")
        mapping_df.to_csv(output_file, index=False)
        print(f"✅ Saved {len(mapping_df)} job-skill mappings")
        
        # Print summary statistics
        print("\n📈 Summary Statistics:")
        print(f"   Total unique jobs: {len(mapping_df)}")
        print(f"   Avg skills per job: {len(mapping_df['top_skills'].str.split(',')) / len(mapping_df):.1f}")
        
        print("\n📋 Top 10 Jobs by Posting Frequency:")
        for idx, row in mapping_df.head(10).iterrows():
            print(f"   {row['job_title']}: {row['num_postings']} postings")
            print(f"      Skills: {row['top_skills']}")
        
        return job_skills_mapping
    
    def get_job_skills(self, job_title: str, mapping_df: pd.DataFrame = None) -> List[str]:
        """Get top skills for a specific job title"""
        if mapping_df is None:
            mapping_file = self.base_path / 'data' / 'processed' / 'job_skill_mapping.csv'
            if not mapping_file.exists():
                raise FileNotFoundError(f"Job-skill mapping not found. Run extract_job_skills() first.")
            mapping_df = pd.read_csv(mapping_file)
        
        # Case-insensitive search
        job_lower = job_title.lower().strip()
        match = mapping_df[mapping_df['job_title'].str.lower().str.strip() == job_lower]
        
        if len(match) == 0:
            return []
        
        skills_str = match.iloc[0]['top_skills']
        return [s.strip() for s in skills_str.split(',') if s.strip()]
    
    def get_all_job_skills_flat(self, mapping_df: pd.DataFrame = None) -> List[str]:
        """Get all unique skills across all jobs"""
        if mapping_df is None:
            mapping_file = self.base_path / 'data' / 'processed' / 'job_skill_mapping.csv'
            if not mapping_file.exists():
                raise FileNotFoundError(f"Job-skill mapping not found.")
            mapping_df = pd.read_csv(mapping_file)
        
        all_skills = set()
        for skills_str in mapping_df['top_skills']:
            skills = [s.strip() for s in str(skills_str).split(',') if s.strip()]
            all_skills.update(skills)
        
        return sorted(list(all_skills))


if __name__ == '__main__':
    """Test the extractor"""
    extractor = JobSkillExtractor()
    
    try:
        job_skills = extractor.extract_job_skills(
            sample_size=50000,  # Use subset for testing
            min_job_occurrences=10,
            top_n_skills=10
        )
        print("\n✅ Extraction completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
