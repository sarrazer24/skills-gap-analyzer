"""Data loading utilities for skills gap analyzer"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional


def load_jobs_data(path: str = 'data/processed/all_jobs_mapped.csv') -> pd.DataFrame:
    """Load jobs dataset with skill lists."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()


def load_skill_metadata(path: str = 'data/raw/skill_migration_clean.csv') -> pd.DataFrame:
    """Load skill metadata with categories."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()


def load_skill_to_category_map(path: str = 'data/raw/skill_migration_clean.csv') -> Dict[str, str]:
    """Load mapping of skills to their categories."""
    try:
        df = pd.read_csv(path)
        return dict(zip(df['skill_group_name'], df['skill_group_category']))
    except:
        return {}


def load_association_rules(
    data_dir: str = 'data/processed'
) -> tuple:
    """Load all three association rule sets (A1, A2, A3)."""
    data_path = Path(data_dir)
    
    rules_a1 = _try_load_csv(data_path / 'association_rules_skills.csv')
    rules_a2 = _try_load_csv(data_path / 'association_rules_categories.csv')
    rules_a3 = _try_load_csv(data_path / 'association_rules_combined.csv')
    
    return rules_a1, rules_a2, rules_a3


def _try_load_csv(path: Path) -> pd.DataFrame:
    """Try to load CSV, return empty DataFrame if fails."""
    try:
        return pd.read_csv(path)
    except:
        return pd.DataFrame()
