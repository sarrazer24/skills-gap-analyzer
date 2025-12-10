import pandas as pd
from pathlib import Path
from typing import Optional

class ClusterAnalyzer:
    """Minimal helper to load a compact job->cluster mapping and query similar jobs.

    The mapping file should contain at least two columns: `job_id` and `cluster_id`.
    Accepts pickles (optionally gzip-compressed) or CSV (optionally gzipped).
    """

    def __init__(self, path: str):
        p = Path(path)
        # Try pandas read_pickle with compression, then read_csv
        try:
            # pandas supports compression kw for to_pickle/read_pickle in recent versions
            self.df = pd.read_pickle(str(p))
        except Exception:
            try:
                self.df = pd.read_pickle(str(p), compression='gzip')
            except Exception:
                # Fallback to CSV
                self.df = pd.read_csv(str(p), compression='infer')

        # Normalize
        if 'job_id' not in self.df.columns:
            # try common alternatives
            for alt in ('job_key', 'jobId', 'id'):
                if alt in self.df.columns:
                    self.df = self.df.rename(columns={alt: 'job_id'})
                    break

        if 'cluster_id' not in self.df.columns:
            for alt in ('cluster', 'cluster_label', 'labels'):
                if alt in self.df.columns:
                    self.df = self.df.rename(columns={alt: 'cluster_id'})
                    break

        if 'job_id' not in self.df.columns or 'cluster_id' not in self.df.columns:
            raise ValueError('Mapping must contain job_id and cluster_id columns')

        # Normalize types
        self.df['job_id'] = self.df['job_id'].astype(str)
        # Keep cluster as-is

    def get_similar_jobs(self, job_id: str, top_n: int = 5):
        job_id = str(job_id)
        row = self.df[self.df['job_id'] == job_id]
        if row.empty:
            return pd.DataFrame(columns=['job_id', 'cluster_id'])
        cluster_id = row.iloc[0]['cluster_id']
        same_cluster = self.df[(self.df['cluster_id'] == cluster_id) & (self.df['job_id'] != job_id)]
        return same_cluster.head(top_n)[['job_id', 'cluster_id']]

    def get_jobs_in_cluster(self, cluster_id):
        return self.df[self.df['cluster_id'] == cluster_id]
