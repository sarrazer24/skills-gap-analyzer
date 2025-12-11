"""Improved cluster analyzer with skill-based filtering for similar job recommendations."""

import pandas as pd
import ast
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from src.utils.skill_filter import get_similar_jobs_with_filtering, get_top_skills


class ClusterAnalyzer:
    """Load cluster mappings and find similar jobs using skill-based filtering.
    
    Supports both legacy and improved (v2) mapping formats with optional skill-based filtering.
    """

    def __init__(self, path: str = None):
        """Initialize ClusterAnalyzer with mapping file.
        
        Args:
            path: Path to cluster mapping pickle/CSV file. If None, tries default locations.
        """
        # Try to find v2 file first, fall back to original
        if path is None:
            candidate_paths = [
                'data/processed/job_clusters_small_v2.pkl',
                'data/processed/job_clusters_small.pkl',
                'data/processed/all_jobs_clustered_full_kmeans.csv'
            ]
            for candidate in candidate_paths:
                p = Path(candidate)
                if p.exists():
                    path = str(p)
                    break
        
        if path is None:
            raise FileNotFoundError("No cluster mapping file found")
        
        self.path = Path(path)
        self._load_mapping()
        self._load_skills_lookup()

    def _load_mapping(self):
        """Load the cluster mapping from pickle or CSV."""
        p = self.path
        
        try:
            self.df = pd.read_pickle(str(p))
        except Exception:
            try:
                self.df = pd.read_pickle(str(p), compression='gzip')
            except Exception:
                # Fallback to CSV
                self.df = pd.read_csv(str(p), compression='infer')

        # Normalize column names
        if 'job_id' not in self.df.columns:
            for alt in ('job_key', 'jobId', 'id'):
                if alt in self.df.columns:
                    self.df = self.df.rename(columns={alt: 'job_id'})
                    break

        if 'cluster_id' not in self.df.columns:
            for alt in ('cluster', 'cluster_label', 'labels'):
                if alt in self.df.columns:
                    self.df = self.df.rename(columns={alt: 'cluster_id'})
                    break

        # Validate required columns
        if 'job_id' not in self.df.columns or 'cluster_id' not in self.df.columns:
            raise ValueError('Mapping must contain job_id and cluster_id columns')

        # Normalize types
        self.df['job_id'] = self.df['job_id'].astype(str)
        
        # Check for enhanced columns (v2)
        self.is_v2 = 'main_category' in self.df.columns

    def _load_skills_lookup(self):
        """Try to load the skills lookup table for improved filtering."""
        lookup_path = self.path.parent / 'skills_lookup_v2.pkl'
        
        self.skills_lookup = None
        if lookup_path.exists():
            try:
                self.skills_lookup = pd.read_pickle(str(lookup_path))
            except Exception:
                pass

    def _parse_skill_list(self, skill_list_str) -> List[str]:
        """Parse skill_list from string representation to list."""
        if isinstance(skill_list_str, list):
            return skill_list_str
        if pd.isna(skill_list_str):
            return []
        try:
            val = ast.literal_eval(str(skill_list_str))
            if isinstance(val, list):
                return [str(s).strip().lower() for s in val]
        except:
            pass
        return []

    def get_similar_jobs(
        self,
        job_id: str,
        top_n: int = 8,
        min_skill_overlap: int = 1
    ) -> pd.DataFrame:
        """Get similar jobs for a given job ID using skill-based filtering.
        
        Uses improved filtering if skills_lookup is available, otherwise falls back to cluster-only.
        
        Args:
            job_id: The job ID to find similar jobs for
            top_n: Number of similar jobs to return
            min_skill_overlap: Minimum overlapping skills required for a match
        
        Returns:
            DataFrame with similar jobs (columns: job_id, cluster_id, job_title, company, location)
        """
        job_id = str(job_id)
        
        # Find the target job
        row = self.df[self.df['job_id'] == job_id]
        if row.empty:
            return pd.DataFrame(columns=['job_id', 'cluster_id'])
        
        target_job = row.iloc[0]
        cluster_id = target_job['cluster_id']
        target_category = target_job.get('main_category', 'other')
        
        # Get all jobs in the same cluster
        cluster_jobs = self.df[self.df['cluster_id'] == cluster_id].copy()
        
        # If skills lookup available, apply skill-based filtering
        if self.skills_lookup is not None:
            target_skills_row = self.skills_lookup[self.skills_lookup['job_id'] == job_id]
            
            if not target_skills_row.empty:
                target_skills = target_skills_row.iloc[0]['top_skills']
                
                # Prepare cluster candidates with skill data
                cluster_candidates = self.skills_lookup[
                    self.skills_lookup['cluster_id'] == cluster_id
                ].copy()
                
                # Apply filtering
                similar, quality = get_similar_jobs_with_filtering(
                    target_job_id=job_id,
                    target_skills=target_skills,
                    target_category=target_category,
                    cluster_candidates=cluster_candidates,
                    top_n=top_n,
                    min_skill_overlap=min_skill_overlap
                )
                
                # Add metadata from main mapping
                similar = similar.merge(
                    self.df[['job_id', 'job_title', 'company', 'location']],
                    on='job_id',
                    how='left'
                )
                
                return similar[['job_id', 'cluster_id', 'job_title', 'company', 'location']].head(top_n)
        
        # Fallback: simple cluster-based filtering (no skill overlap)
        similar = cluster_jobs[cluster_jobs['job_id'] != job_id]
        required_cols = ['job_id', 'cluster_id']
        
        # Add available columns
        for col in ['job_title', 'company', 'location']:
            if col in similar.columns:
                required_cols.append(col)
        
        return similar[required_cols].head(top_n)

    def find_similar(
        self,
        job: str = None,
        job_id: str = None,
        top_n: int = 6
    ) -> List[Dict]:
        """Find similar jobs by job title or job ID.
        
        Args:
            job: Job title to search for (fuzzy match)
            job_id: Exact job ID (takes precedence over job title)
            top_n: Number of results to return
        
        Returns:
            List of similar job dictionaries
        """
        # Resolve job ID
        if job_id:
            target_id = str(job_id)
        elif job:
            # Fuzzy match by job title
            matches = self.df[self.df['job_title'].str.contains(job, case=False, na=False)]
            if matches.empty:
                return []
            target_id = matches.iloc[0]['job_id']
        else:
            return []
        
        # Get similar jobs
        similar_df = self.get_similar_jobs(target_id, top_n=top_n)
        
        # Convert to list of dictionaries
        result = []
        for _, row in similar_df.iterrows():
            result.append({
                'job_id': row['job_id'],
                'job_title': row.get('job_title', 'Unknown'),
                'company': row.get('company', 'Unknown'),
                'location': row.get('location', 'Unknown'),
                'cluster_id': row['cluster_id']
            })
        
        return result

    def get_jobs_in_cluster(self, cluster_id) -> pd.DataFrame:
        """Get all jobs in a specific cluster.
        
        Args:
            cluster_id: The cluster ID
        
        Returns:
            DataFrame with jobs in the cluster
        """
        return self.df[self.df['cluster_id'] == cluster_id]

    def get_cluster_info(self, cluster_id) -> Dict:
        """Get summary information about a cluster.
        
        Args:
            cluster_id: The cluster ID
        
        Returns:
            Dictionary with cluster statistics
        """
        cluster_jobs = self.get_jobs_in_cluster(cluster_id)
        
        info = {
            'cluster_id': cluster_id,
            'size': len(cluster_jobs),
            'job_count': len(cluster_jobs),
        }
        
        # Add category info if available
        if self.is_v2 and 'main_category' in cluster_jobs.columns:
            info['top_categories'] = cluster_jobs['main_category'].value_counts().head(5).to_dict()
        
        # Add location info if available
        if 'location' in cluster_jobs.columns:
            info['locations'] = cluster_jobs['location'].value_counts().head(3).to_dict()
        
        # Add company info if available
        if 'company' in cluster_jobs.columns:
            info['companies'] = cluster_jobs['company'].value_counts().head(3).to_dict()
        
        return info

    def find_bridge_skills(
        self,
        source_job_id: str,
        target_job_id: str
    ) -> List[str]:
        """Find overlapping skills between two jobs (for career path suggestions).
        
        Args:
            source_job_id: Current job ID
            target_job_id: Target job ID
        
        Returns:
            List of overlapping skills
        """
        if self.skills_lookup is None:
            return []
        
        source = self.skills_lookup[self.skills_lookup['job_id'] == str(source_job_id)]
        target = self.skills_lookup[self.skills_lookup['job_id'] == str(target_job_id)]
        
        if source.empty or target.empty:
            return []
        
        source_skills = set(source.iloc[0]['top_skills'])
        target_skills = set(target.iloc[0]['top_skills'])
        
        return list(source_skills & target_skills)
