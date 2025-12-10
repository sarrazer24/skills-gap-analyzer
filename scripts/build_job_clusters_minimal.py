from pathlib import Path
import pandas as pd
import os
ROOT = Path(__file__).resolve().parents[1]
IN_PKL = ROOT / 'data' / 'processed' / 'job_clusters_small.pkl'
OUT_MIN_CSV_GZ = ROOT / 'data' / 'processed' / 'job_clusters_minimal.csv.gz'
OUT_MIN_PKL_GZ = ROOT / 'data' / 'processed' / 'job_clusters_minimal.pkl.gz'

if not IN_PKL.exists():
    print('Input mapping not found at', IN_PKL)
    raise SystemExit(2)

print('Loading', IN_PKL)
df = pd.read_pickle(IN_PKL)
print('Original shape:', df.shape)
min_df = df[['job_id','cluster_id']]
print('Minimal shape:', min_df.shape)
print('Saving compressed CSV (gzip) to', OUT_MIN_CSV_GZ)
min_df.to_csv(OUT_MIN_CSV_GZ, index=False, compression='gzip')
print('Saving compressed pickle (gzip) to', OUT_MIN_PKL_GZ)
# pandas to_pickle supports compression via the compression argument in newer versions
try:
    min_df.to_pickle(OUT_MIN_PKL_GZ, compression='gzip')
except TypeError:
    # Fallback: write to pickle then gzip externally
    import pickle, gzip
    with gzip.open(OUT_MIN_PKL_GZ, 'wb') as f:
        pickle.dump(min_df, f)

print('Done.')
size_csv = os.path.getsize(OUT_MIN_CSV_GZ)
size_pkl = os.path.getsize(OUT_MIN_PKL_GZ)
print('Minimal CSV gzip size:', size_csv)
print('Minimal PKL gzip size:', size_pkl)

def human(n):
    for unit in ['B','KB','MB','GB']:
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"

print('Sizes (human):', human(size_csv), human(size_pkl))
