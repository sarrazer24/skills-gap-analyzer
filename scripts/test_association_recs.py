import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `src` imports resolve when running scripts
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.loader import DataLoader
from src.models.association_miner import AssociationMiner

model_path = 'app/models/association_rules.pkl'
print('Model exists:', os.path.exists(model_path))
if not os.path.exists(model_path):
    print('No model file found; exiting')
    exit(1)

miner = AssociationMiner.load(model_path)
print('Rules loaded:', miner.rules is not None and len(miner.rules) > 0)
if miner.rules is not None and len(miner.rules) > 0:
    print('\nSample rules head:')
    try:
        # show first 10 rules with antecedents/consequents types
        for idx, row in miner.rules.head(10).iterrows():
            print(f"- antecedents(type={type(row['antecedents'])}): {row['antecedents']} -> consequents(type={type(row['consequents'])}): {row['consequents']} | conf={row.get('confidence')} | supp={row.get('support')}")
    except Exception as e:
        print('Could not display rule samples:', e)

# sample user skills
user_skills = ['python', 'sql', 'pandas']
print('User skills:', user_skills)

# map skills to categories
try:
    dl = DataLoader()
    skills_tax = dl.load_skills_taxonomy()
    skill_to_cat = {}
    if hasattr(skills_tax, 'iterrows'):
        for _, r in skills_tax.iterrows():
            name = str(r['skill_group_name']).lower().strip()
            cat = str(r['skill_group_category']).lower().strip()
            if name:
                skill_to_cat[name] = cat
    user_items = [skill_to_cat.get(s.lower().strip(), None) for s in user_skills]
    user_items = [u for u in user_items if u]
    if not user_items:
        user_items = user_skills
except Exception as e:
    user_items = user_skills

print('User items passed to miner:', user_items)
recs = miner.get_recommendations(user_items, top_n=10)
print('Recommendations shape:', None if recs is None else getattr(recs, 'shape', None))
print(recs.head(10) if hasattr(recs, 'head') else recs)
