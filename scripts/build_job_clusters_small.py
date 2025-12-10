"""
Script: build_job_clusters_small.py

Purpose:
- Inspect `clustering_results_kmeans.pkl` to determine how cluster labels are stored.
- Build a compact DataFrame mapping jobs -> cluster_id using `data/processed/all_jobs_mapped.csv`.
- Save a small mapping file to `data/processed/job_clusters_small.pkl` and CSV.

Run from repo root:
    python scripts\build_job_clusters_small.py

This script is defensive: it handles several possible pickle structures and
attempts to join cluster labels to the jobs metadata using common keys.
"""

from pathlib import Path
import pickle
from joblib import load as joblib_load
import gzip
import pandas as pd
import numpy as np
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
PKL_CANDIDATES = [
    ROOT / "clustering_results_kmeans.pkl",
    ROOT / "data" / "processed" / "clustering_results_kmeans.pkl",
    ROOT / "scripts" / "clustering_results_kmeans.pkl",
]

JOBS_META = ROOT / "data" / "processed" / "all_jobs_mapped.csv"
OUT_CSV = ROOT / "data" / "processed" / "job_clusters_small.csv"
OUT_PKL = ROOT / "data" / "processed" / "job_clusters_small.pkl"


def find_pkl_path():
    for p in PKL_CANDIDATES:
        if p.exists():
            return p
    return None


def load_pickle(path: Path):
    # Try pickle, then joblib, then gzip+pickle as fallbacks.
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        # try joblib
        try:
            return joblib_load(path)
        except Exception:
            # try gzip + pickle
            try:
                with gzip.open(path, "rb") as gf:
                    return pickle.load(gf)
            except Exception:
                # re-raise original for debugging
                raise e


def safe_head(obj, n=5):
    try:
        if hasattr(obj, "head"):
            return obj.head(n)
        if isinstance(obj, (list, tuple, np.ndarray)):
            return obj[:n]
        if isinstance(obj, dict):
            return {k: (v.shape if hasattr(v, 'shape') else type(v)) for k, v in list(obj.items())[:n]}
    except Exception:
        return str(type(obj))
    return str(type(obj))


def discover_label_arrays(pkl_obj, jobs_df=None):
    """
    Attempt to get an array/series of cluster labels and, if possible, an array of job identifiers/indices.
    Returns a DataFrame with columns ['job_key', 'cluster_id'] where job_key is either job index or job_id.
    """
    # Case 1: pkl_obj is a dict-like with explicit arrays
    if isinstance(pkl_obj, dict):
        # Common keys
        possible_label_keys = [k for k in pkl_obj.keys() if 'label' in k.lower() or 'cluster' in k.lower() or 'labels' in k.lower()]
        possible_id_keys = [k for k in pkl_obj.keys() if 'job' in k.lower() or 'id' in k.lower() or 'index' in k.lower() or 'key' in k.lower()]

        # If explicit labels key exists
        for lk in possible_label_keys:
            labels = pkl_obj.get(lk)
            if isinstance(labels, (list, tuple, np.ndarray, pd.Series)):
                # If pkl contains corresponding ids
                for ik in possible_id_keys:
                    ids = pkl_obj.get(ik)
                    if isinstance(ids, (list, tuple, np.ndarray, pd.Series)) and len(ids) == len(labels):
                        return pd.DataFrame({"job_key": ids, "cluster_id": np.asarray(labels)})
                # Otherwise, if jobs_df provided and lengths match, align by position
                if jobs_df is not None and len(labels) == len(jobs_df):
                    # Use jobs_df index or job_id column
                    if 'job_id' in jobs_df.columns:
                        return pd.DataFrame({"job_key": jobs_df['job_id'].values, "cluster_id": np.asarray(labels)})
                    else:
                        return pd.DataFrame({"job_key": jobs_df.index.values, "cluster_id": np.asarray(labels)})
        # If pkl_obj itself maps job_key -> cluster
        # e.g., {jobkey1: cluster1, jobkey2: cluster2}
        if all(isinstance(v, (int, np.integer)) for v in pkl_obj.values()):
            return pd.DataFrame([{"job_key": k, "cluster_id": v} for k, v in pkl_obj.items()])

    # Case 2: pkl_obj is a pandas Series or ndarray of labels
    if isinstance(pkl_obj, pd.Series):
        labels = pkl_obj.values
        if jobs_df is not None and len(labels) == len(jobs_df):
            if 'job_id' in jobs_df.columns:
                return pd.DataFrame({"job_key": jobs_df['job_id'].values, "cluster_id": labels})
            else:
                return pd.DataFrame({"job_key": jobs_df.index.values, "cluster_id": labels})

    if isinstance(pkl_obj, (list, tuple, np.ndarray)):
        labels = np.asarray(pkl_obj)
        if jobs_df is not None and len(labels) == len(jobs_df):
            if 'job_id' in jobs_df.columns:
                return pd.DataFrame({"job_key": jobs_df['job_id'].values, "cluster_id": labels})
            else:
                return pd.DataFrame({"job_key": jobs_df.index.values, "cluster_id": labels})

    # Case 3: pkl_obj is a DataFrame
    if isinstance(pkl_obj, pd.DataFrame):
        # find cluster-like column
        for col in pkl_obj.columns:
            if 'cluster' in col.lower() or 'label' in col.lower():
                # find id-like column
                idcol = None
                for c in pkl_obj.columns:
                    if 'job' in c.lower() or 'id' in c.lower() or 'index' in c.lower() or 'key' in c.lower():
                        idcol = c; break
                if idcol is None:
                    # Align by index
                    if jobs_df is not None and len(pkl_obj) == len(jobs_df):
                        if 'job_id' in jobs_df.columns:
                            return pd.DataFrame({"job_key": jobs_df['job_id'].values, "cluster_id": pkl_obj[col].values})
                        else:
                            return pd.DataFrame({"job_key": jobs_df.index.values, "cluster_id": pkl_obj[col].values})
                else:
                    return pd.DataFrame({"job_key": pkl_obj[idcol].values, "cluster_id": pkl_obj[col].values})

    # If none matched
    return None


def find_job_id_column(jobs_df: pd.DataFrame):
    candidates = [
        'job_id', 'jobkey', 'job_key', 'id', 'jobId', 'jobID'
    ]
    for c in candidates:
        if c in jobs_df.columns:
            return c
    # fallback to index
    return None


def choose_title_company_location(jobs_df: pd.DataFrame):
    title_cols = ['job_title', 'title', 'job_title_clean']
    company_cols = ['company', 'employer', 'company_name']
    location_cols = ['location', 'city', 'job_location']

    title = next((c for c in title_cols if c in jobs_df.columns), None)
    company = next((c for c in company_cols if c in jobs_df.columns), None)
    location = next((c for c in location_cols if c in jobs_df.columns), None)
    return title, company, location


def main():
    pkl_path = find_pkl_path()
    if pkl_path is None:
        print("ERROR: clustering_results_kmeans.pkl not found in expected locations:")
        for c in PKL_CANDIDATES:
            print("  -", c)
        sys.exit(2)

    print("Using clustering results pickle:", pkl_path)
    pkl_obj = load_pickle(pkl_path)
    print("Pickle type:", type(pkl_obj))
    print("Pickle sample:", safe_head(pkl_obj, 5))

    # Load jobs metadata
    if not JOBS_META.exists():
        print(f"ERROR: jobs metadata not found at {JOBS_META}")
        sys.exit(2)

    jobs_df = pd.read_csv(JOBS_META)
    print("Loaded jobs metadata with shape:", jobs_df.shape)

    job_id_col = find_job_id_column(jobs_df)
    if job_id_col:
        print(f"Detected job id column: {job_id_col}")
    else:
        print("No explicit job id column found; will use DataFrame index for joining.")

    title_col, company_col, location_col = choose_title_company_location(jobs_df)
    print('Using columns:', {'title': title_col, 'company': company_col, 'location': location_col})

    # Try to discover labels
    mapping_df = discover_label_arrays(pkl_obj, jobs_df=jobs_df)

    if mapping_df is None:
        print("Could not automatically extract a job->cluster mapping from the pickle.")
        print("Attempting to extract mapping from the large clustered CSV (offline) instead.")

        # Try to find the large clustered CSV file (offline processing allowed)
        BIG_CANDIDATES = [
            ROOT / "data" / "processed" / "all_jobs_clustered_full_kmeans.csv",
            ROOT / "data" / "raw" / "all_jobs_clustered_full_kmeans.csv",
            ROOT / "all_jobs_clustered_full_kmeans.csv",
        ]
        big_path = None
        for p in BIG_CANDIDATES:
            if p.exists():
                big_path = p
                break

        if big_path is None:
            print("Large clustered CSV not found in expected locations. Showing pickle contents for manual inspection:")
            if isinstance(pkl_obj, dict):
                for k, v in pkl_obj.items():
                    print(f"Key: {k} -> type: {type(v)}, len: {getattr(v, '__len__', lambda: 'N/A')()}")
            elif isinstance(pkl_obj, pd.DataFrame):
                print(pkl_obj.columns)
                print(pkl_obj.head(5))
            else:
                print(repr(pkl_obj)[:1000])
            sys.exit(2)

        print("Found large clustered CSV:", big_path)
        # Inspect columns
        sample = pd.read_csv(big_path, nrows=5)
        print("Big CSV columns:", list(sample.columns))

        # Identify candidate columns
        job_id_candidates = ['job_id', 'job_key', 'jobkey', 'id', 'jobId']
        cluster_candidates = ['cluster', 'cluster_id', 'kmeans_cluster', 'cluster_label', 'labels']

        job_id_col_big = next((c for c in job_id_candidates if c in sample.columns), None)
        cluster_col_big = next((c for c in cluster_candidates if c in sample.columns), None)

        title_col_big, company_col_big, location_col_big = choose_title_company_location(sample)

        if cluster_col_big is None:
            print("Could not find a cluster column in the big CSV. Columns present:", sample.columns)
            sys.exit(2)

        print(f"Using cluster column: {cluster_col_big}, job id column: {job_id_col_big}")

        # Build output CSV by streaming required columns
        usecols = [c for c in [job_id_col_big, title_col_big, company_col_big, location_col_big, cluster_col_big] if c]
        print("Streaming columns:", usecols)

        chunksize = 200_000
        first = True
        # Remove existing outputs if any
        if OUT_CSV.exists():
            OUT_CSV.unlink()

        for chunk in pd.read_csv(big_path, usecols=usecols, chunksize=chunksize):
            # Normalize column names
            to_keep = {}
            if job_id_col_big:
                to_keep['job_id'] = chunk[job_id_col_big]
            else:
                # if no explicit job id, create from index offset
                to_keep['job_id'] = chunk.index
            to_keep['job_title'] = chunk[title_col_big] if title_col_big in chunk.columns else None
            to_keep['company'] = chunk[company_col_big] if company_col_big in chunk.columns else None
            to_keep['location'] = chunk[location_col_big] if location_col_big in chunk.columns else None
            to_keep['cluster_id'] = chunk[cluster_col_big]

            small_chunk = pd.DataFrame(to_keep)
            # Append to CSV
            small_chunk.to_csv(OUT_CSV, mode='a', header=first, index=False)
            first = False

        # After streaming CSV, load it and save pickle
        out_df = pd.read_csv(OUT_CSV)
        out_df.to_pickle(OUT_PKL)
        size_pkl = os.path.getsize(OUT_PKL) if OUT_PKL.exists() else None
        size_csv = os.path.getsize(OUT_CSV) if OUT_CSV.exists() else None

        def human(n):
            if n is None:
                return 'N/A'
            for unit in ['B','KB','MB','GB']:
                if n < 1024.0:
                    return f"{n:.1f}{unit}"
                n /= 1024.0
            return f"{n:.1f}TB"

        print(f"Saved pickle: {OUT_PKL} ({human(size_pkl)})")
        print(f"Saved csv: {OUT_CSV} ({human(size_csv)})")
        print("Done (extracted from large CSV).")
        sys.exit(0)

    # Normalize mapping_df column names
    mapping_df = mapping_df.rename(columns={mapping_df.columns[0]: 'job_key', mapping_df.columns[1]: 'cluster_id'})

    # If job_key matches job_id column directly, merge. Otherwise try matching by index.
    if job_id_col and mapping_df['job_key'].dtype == jobs_df[job_id_col].dtype:
        merged = pd.merge(jobs_df, mapping_df, left_on=job_id_col, right_on='job_key', how='inner')
    else:
        # try matching by position: if counts match, align
        if len(mapping_df) == len(jobs_df):
            jobs_df = jobs_df.reset_index(drop=False)
            # use the reset index name
            idxcol = jobs_df.columns[0]
            merged = pd.concat([jobs_df, mapping_df['cluster_id']], axis=1)
            # ensure column name
            merged = merged.rename(columns={merged.columns[-1]: 'cluster_id'})
        else:
            # attempt to coerce types and merge
            try:
                merged = pd.merge(jobs_df, mapping_df, left_on=job_id_col if job_id_col else jobs_df.index, right_on='job_key', how='inner')
            except Exception as e:
                print("Failed to merge automatically:", e)
                sys.exit(2)

    print("Merged mapping shape:", merged.shape)

    # Build the compact DataFrame
    job_id_field = job_id_col if job_id_col else merged.columns[0]
    out_df = pd.DataFrame()
    out_df['job_id'] = merged[job_id_field]
    out_df['job_title'] = merged[title_col] if title_col in merged.columns else merged[merged.columns[0]]
    out_df['company'] = merged[company_col] if company_col in merged.columns else None
    out_df['location'] = merged[location_col] if location_col in merged.columns else None
    out_df['cluster_id'] = merged['cluster_id']

    # Keep only necessary columns
    out_df = out_df[['job_id', 'job_title', 'company', 'location', 'cluster_id']]

    # Save both pickle (smaller) and csv
    out_df.to_pickle(OUT_PKL)
    out_df.to_csv(OUT_CSV, index=False)

    size_pkl = os.path.getsize(OUT_PKL) if OUT_PKL.exists() else None
    size_csv = os.path.getsize(OUT_CSV) if OUT_CSV.exists() else None

    def human(n):
        if n is None:
            return 'N/A'
        for unit in ['B','KB','MB','GB']:
            if n < 1024.0:
                return f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}TB"

    print(f"Saved pickle: {OUT_PKL} ({human(size_pkl)})")
    print(f"Saved csv: {OUT_CSV} ({human(size_csv)})")

    print("Done.")


if __name__ == '__main__':
    main()
