"""Sanity check loader for exported models
Loads clustering_model.pkl and association_rules.pkl from app/models,
performs a sample transform+predict and prints a few diagnostics.
"""
import joblib
import os
import traceback

MODEL_DIR = os.path.join('app', 'models')
CLUSTER_PATH = os.path.join(MODEL_DIR, 'clustering_model.pkl')
ASSOC_PATH = os.path.join(MODEL_DIR, 'association_rules.pkl')

print('SANITY CHECK: model files')
print(' - clustering model:', CLUSTER_PATH)
print(' - association rules:', ASSOC_PATH)
print()

errors = []

# Load clustering model
try:
    clustering_pkg = joblib.load(CLUSTER_PATH)
    print('Loaded clustering package keys:', list(clustering_pkg.keys()))
except Exception as e:
    print('ERROR loading clustering model:', e)
    traceback.print_exc()
    errors.append(('clustering_load', str(e)))
    clustering_pkg = None

# Load association rules
try:
    assoc_pkg = joblib.load(ASSOC_PATH)
    print('Loaded association package keys:', list(assoc_pkg.keys()))
except Exception as e:
    print('ERROR loading association rules:', e)
    traceback.print_exc()
    errors.append(('assoc_load', str(e)))
    assoc_pkg = None

print('\n-- CLUSTERING SANITY CHECK --')
if clustering_pkg is not None:
    # Expect keys like 'trained_model' and 'feature_hasher' or similar
    model = clustering_pkg.get('trained_model') or clustering_pkg.get('model') or clustering_pkg.get('trained')
    hasher = clustering_pkg.get('feature_hasher') or clustering_pkg.get('hasher')
    n_clusters = clustering_pkg.get('n_clusters') or (getattr(model, 'n_clusters', None) if model is not None else None)

    print('model object type:', type(model))
    print('hasher object type:', type(hasher))
    print('n_clusters (pkg):', n_clusters)

    sample_skills = ['python', 'sql', 'pandas']
    print('\nSample skills:', sample_skills)

    try:
        # Prepare dict form expected by FeatureHasher
        skill_dict = {s: 1 for s in sample_skills}
        if hasher is not None:
            X = hasher.transform([skill_dict])
        else:
            # Fallback: try to use a basic feature vector
            import numpy as np
            X = np.zeros((1, getattr(model, 'n_features_in_', 100)))

        print('Transformed sample shape:', getattr(X, 'shape', 'unknown'))

        # Predict cluster
        if model is not None:
            try:
                labels = model.predict(X)
            except Exception:
                # If sparse -> toarray
                try:
                    labels = model.predict(X.toarray())
                except Exception as e:
                    print('ERROR predicting cluster:', e)
                    traceback.print_exc()
                    labels = None
            print('Predicted cluster for sample:', labels)
        else:
            print('No clustering model found in package')
    except Exception as e:
        print('ERROR during clustering sanity check:', e)
        traceback.print_exc()
        errors.append(('clustering_check', str(e)))

else:
    print('Skipping clustering checks (package not loaded)')

print('\n-- ASSOCIATION RULES SANITY CHECK --')
if assoc_pkg is not None:
    # assoc_pkg may be a dict with key 'rules' containing a DataFrame
    rules = None
    if isinstance(assoc_pkg, dict):
        # Try common keys
        for key in ['rules', 'rules_df', 'association_rules', 'model']:
            if key in assoc_pkg:
                rules = assoc_pkg[key]
                break
        # If not found, maybe the dict itself is the rules
        if rules is None:
            # Try to find a DataFrame in values
            for v in assoc_pkg.values():
                try:
                    import pandas as pd
                    if isinstance(v, pd.DataFrame):
                        rules = v
                        break
                except Exception:
                    pass
    else:
        # If assoc_pkg is already a DataFrame
        try:
            import pandas as pd
            if isinstance(assoc_pkg, pd.DataFrame):
                rules = assoc_pkg
        except Exception:
            pass

    if rules is None:
        print('Could not locate rules DataFrame inside association package. Keys:', list(assoc_pkg.keys()) if isinstance(assoc_pkg, dict) else 'non-dict')
    else:
        print('Rules DataFrame shape:', getattr(rules, 'shape', 'unknown'))
        # Simple lookup: given user categories, find consequents where antecedents subset
        user_cats = ['data science', 'software development', 'backend']
        print('Sample user categories:', user_cats)

        try:
            recs = set()
            import pandas as pd
            for _, row in rules.iterrows():
                antecedents = row.get('antecedents')
                consequents = row.get('consequents')
                # Normalize antecedents/consequents to sets
                try:
                    if isinstance(antecedents, str):
                        antecedents_set = set(eval(antecedents))
                    else:
                        antecedents_set = set(antecedents)
                except Exception:
                    antecedents_set = set(antecedents) if antecedents is not None else set()

                try:
                    if isinstance(consequents, str):
                        consequents_set = set(eval(consequents))
                    else:
                        consequents_set = set(consequents)
                except Exception:
                    consequents_set = set(consequents) if consequents is not None else set()

                if antecedents_set and antecedents_set.issubset(set(user_cats)):
                    recs.update(consequents_set)

            print('Recommendations from category rules (sample):', list(recs)[:20])
        except Exception as e:
            print('ERROR while deriving recommendations:', e)
            traceback.print_exc()
            errors.append(('assoc_check', str(e)))

else:
    print('Skipping association rules checks (package not loaded)')

print('\nSanity check completed. Errors:', errors)

if errors:
    raise SystemExit(1)

print('\nAll sanity checks passed (or no errors captured).')
