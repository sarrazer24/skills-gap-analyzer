"""ML enhancement helpers for Skills Gap Analyzer (Phase 1)

This module provides lightweight, dependency-minimal helpers that use
the existing association rules CSVs to produce a suggested learning order
and simple skill prioritization metrics. Designed for quick integration
into the Streamlit app as a non-blocking enhancement.

Notes:
- Safe parsing with ast.literal_eval
- Fallbacks if processed CSVs are missing (graceful behavior)
"""
from typing import List, Dict, Any
import os
import ast
import pandas as pd


def load_rules(csv_path: str) -> pd.DataFrame:
    """Load association rules from CSV and safely parse antecedents/consequents.

    Expected columns: antecedents, consequents, confidence, lift
    If the file is missing, return an empty DataFrame with expected columns.
    """
    cols = ["antecedents", "consequents", "confidence", "lift"]
    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=cols)

    df = pd.read_csv(csv_path)

    # Ensure expected columns exist
    for c in cols:
        if c not in df.columns:
            df[c] = None

    def _safe_parse(x):
        if pd.isna(x):
            return []
        if isinstance(x, (list, tuple, set)):
            return list(x)
        try:
            return list(ast.literal_eval(x))
        except Exception:
            # last-resort: if it's a comma-separated string
            try:
                return [s.strip() for s in str(x).split(",") if s.strip()]
            except Exception:
                return [str(x)]

    df["antecedents"] = df["antecedents"].apply(_safe_parse)
    df["consequents"] = df["consequents"].apply(_safe_parse)

    # Ensure numeric columns
    for col in ("confidence", "lift"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    return df


def load_skill_category_map(skills_enriched_path: str = "data/processed/skills_enriched.csv") -> Dict[str, str]:
    """Load a mapping from skill -> category.

    If the enriched file is not present, return an empty dict and callers
    should fall back to naive categorization.
    """
    if not os.path.exists(skills_enriched_path):
        return {}

    try:
        df = pd.read_csv(skills_enriched_path)
    except Exception:
        return {}

    # Try common column names
    key_col = None
    cat_col = None
    for c in df.columns:
        lc = c.lower()
        if lc in ("skill", "skill_name", "name"):
            key_col = c
        if lc in ("category", "skill_category", "group"):
            cat_col = c

    if key_col is None or cat_col is None:
        return {}

    mapping = dict(zip(df[key_col].astype(str).str.lower().str.strip(), df[cat_col].astype(str).str.strip()))
    return mapping


def skills_to_categories(skills: List[str], mapping: Dict[str, str] = None) -> Dict[str, str]:
    """Map skills to categories using provided mapping or naive fallback.

    Returns a dict: {skill: category}
    """
    mapping = mapping or {}
    out = {}
    for s in skills:
        if s is None:
            continue
        key = str(s).lower().strip()
        if key in mapping:
            out[s] = mapping[key]
        else:
            # naive fallback: use first token as category
            tok = key.split()[0] if key else "misc"
            out[s] = tok
    return out


def get_optimal_learning_order(user_skills: List[str],
                               missing_skills: List[str],
                               category_rules_csv: str = "data/processed/association_rules_categories.csv",
                               skills_enriched_path: str = "data/processed/skills_enriched.csv") -> List[Dict[str, Any]]:
    """Produce an ordered list of categories (and contained skills) to learn first.

    Strategy:
    - Map skills -> categories (using enriched CSV if available)
    - For each missing category, look up category-level rules whose consequents
      include the target category.
    - Prefer rules where antecedents are already present in user's categories.
    - Return steps sorted by confidence.
    """
    rules_df = load_rules(category_rules_csv)
    cat_map = load_skill_category_map(skills_enriched_path)

    user_cat_map = skills_to_categories(user_skills, cat_map)
    missing_cat_map = skills_to_categories(missing_skills, cat_map)

    user_categories = set(user_cat_map.values())
    missing_categories = set(missing_cat_map.values())

    steps = []
    for cat in missing_categories:
        # Find rules where consequents include this category
        matching = rules_df[rules_df["consequents"].apply(lambda cs: cat in cs)]

        chosen = None
        if not matching.empty:
            # Prefer rules whose antecedents are satisfied by user_categories
            def antecedents_satisfied(row):
                antecedents = set(row["antecedents"])
                return antecedents.issubset(user_categories)

            satisfied = matching[matching.apply(antecedents_satisfied, axis=1)]
            if not satisfied.empty:
                # pick highest confidence
                chosen = satisfied.sort_values(["confidence", "lift"], ascending=False).iloc[0]
            else:
                chosen = matching.sort_values(["confidence", "lift"], ascending=False).iloc[0]

        confidence = float(chosen["confidence"]) if chosen is not None else 0.0
        prerequisites = list(chosen["antecedents"]) if chosen is not None else []

        skills_in_cat = [s for s, c in missing_cat_map.items() if c == cat]

        steps.append({
            "category": cat,
            "confidence": confidence,
            "prerequisites": prerequisites,
            "skills": skills_in_cat
        })

    # Sort by confidence desc
    steps = sorted(steps, key=lambda x: x["confidence"], reverse=True)
    return steps


def prioritize_skills_with_rules(missing_skills: List[str],
                                 skill_rules_csv: str = "data/processed/association_rules_skills.csv") -> List[Dict[str, Any]]:
    """Prioritize missing skills by how many other skills they unlock.

    Simple heuristic:
    - For each candidate skill, count rules where that skill appears in antecedents
      (i.e., learning it unlocks consequents).
    - Compute average confidence for those rules.
    - Score = count * avg_confidence
    - Return sorted list of skill dicts.
    """
    rules = load_rules(skill_rules_csv)
    out = []
    for s in missing_skills:
        # antecedent-based unlocks
        rows = rules[rules["antecedents"].apply(lambda ants: s in ants)]
        count = len(rows)
        avg_conf = float(rows["confidence"].mean()) if count > 0 else 0.0
        score = count * avg_conf
        # Top consequents (what this skill opens)
        consequents = []
        if count > 0:
            # flatten and count freq
            all_cons = [c for lst in rows["consequents"].tolist() for c in lst]
            cons_series = pd.Series(all_cons)
            top = cons_series.value_counts().head(3).index.tolist()
            consequents = top

        out.append({
            "skill": s,
            "opens_doors_count": count,
            "avg_confidence": avg_conf,
            "score": score,
            "top_consequents": consequents
        })

    out = sorted(out, key=lambda x: x["score"], reverse=True)
    return out


__all__ = [
    "load_rules",
    "load_skill_category_map",
    "skills_to_categories",
    "get_optimal_learning_order",
    "prioritize_skills_with_rules",
]
