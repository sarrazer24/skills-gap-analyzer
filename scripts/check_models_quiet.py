"""Quiet model check for clustering and association packages.
Exits with code 0 on success, non-zero on failure.
"""
import sys
import os
from pathlib import Path
import joblib

proj_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proj_root))

from src.models.association_miner import AssociationMiner


def locate_model_file(preferred_paths):
    for p in preferred_paths:
        if os.path.exists(p):
            return p
    return None


def check_clustering():
    paths = [
        os.path.join('app', 'models', 'clustering_model.pkl'),
        os.path.join('data', 'processed', 'clustering_model.pkl'),
        os.path.join('data', 'processed', 'clustering_results_kmeans.pkl'),
    ]
    path = locate_model_file(paths)
    if not path:
        print('CLUSTERING: model file not found')
        return False
    try:
        pkg = joblib.load(path)
    except Exception as e:
        print('CLUSTERING: failed to load:', e)
        return False
    required_keys = {'trained_model', 'feature_hasher'}
    if not required_keys.issubset(set(pkg.keys())):
        print('CLUSTERING: missing keys in package:', set(pkg.keys()))
        return False
    # Transform a sample
    hasher = pkg['feature_hasher']
    model = pkg['trained_model']
    sample = ['python', 'sql', 'pandas']
    try:
        dicts = [{s: 1 for s in sample}]
        X = hasher.transform(dicts)
        print('CLUSTERING: transformed sample shape ->', getattr(X, 'shape', None))
        pred = model.predict(X)
        print('CLUSTERING: sample prediction ->', pred)
    except Exception as e:
        print('CLUSTERING: transform/predict failed:', e)
        return False
    return True


def check_association():
    paths = [
        os.path.join('app', 'models', 'association_rules.pkl'),
        os.path.join('data', 'processed', 'association_rules_a2.pkl'),
        os.path.join('data', 'processed', 'association_rules.pkl'),
    ]
    path = locate_model_file(paths)
    if not path:
        print('ASSOCIATION: model file not found')
        return False
    try:
        # Prefer using AssociationMiner for a real recommendation check
        miner = AssociationMiner.load(path)
        sample = ['python', 'sql', 'pandas']
        recs = miner.get_recommendations(sample, top_n=5)
        print('ASSOCIATION: recommendations shape ->', None if recs is None else recs.shape)
        # Print a short preview
        if recs is not None and not recs.empty:
            print(recs.head(3).to_string(index=False))
        else:
            print('ASSOCIATION: no recommendations returned (this can be normal for category-level rules)')
    except Exception as e:
        print('ASSOCIATION: load/get_recommendations failed:', e)
        return False
    return True


if __name__ == '__main__':
    ok1 = check_clustering()
    ok2 = check_association()
    if ok1 and ok2:
        print('OK: both checks passed')
        sys.exit(0)
    else:
        print('ERROR: one or more checks failed:', ok1, ok2)
        sys.exit(2)
