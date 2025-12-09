"""Association Rules Mining Model - Production Ready

Trains association rule models (A1: Skills, A2: Categories, A3: Combined)
using FP-Growth and Apriori algorithms from cleaned job skill data.
"""
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from typing import List, Dict, Any, Optional, Tuple
import joblib
import warnings
import ast
import os
from pathlib import Path
from collections import Counter
warnings.filterwarnings('ignore')


def train_all_models(
    df: pd.DataFrame,
    skill_column: str = 'skill_list',
    category_column: str = 'skill_categories',
    min_support: float = 0.01,
    min_confidence: float = 0.4,
    min_occurrences: int = 10,
    skill_dict: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Train all three association rule models from job skill data.
    
    Args:
        df: DataFrame with job data and skill lists
        skill_column: Name of column containing skill lists
        category_column: Name of column containing skill categories
        min_support: Minimum support threshold (0-1)
        min_confidence: Minimum confidence threshold (0-1)
        min_occurrences: Minimum occurrences to include skill
        skill_dict: Optional skill-to-category mapping
        
    Returns:
        Tuple of (rules_A1, rules_A2, rules_A3) DataFrames
    """
    # Prepare transactions
    transactions_skills = _prepare_skill_transactions(df, skill_column)
    transactions_cats = _prepare_category_transactions(df, category_column)
    transactions_combined = _prepare_combined_transactions(
        transactions_skills, transactions_cats
    )
    
    # Train models
    rules_a1 = _train_model_a1(
        transactions_skills, min_support, min_confidence, min_occurrences
    )
    rules_a2 = _train_model_a2(transactions_cats, min_support, min_confidence)
    rules_a3 = _train_model_a3(
        transactions_combined, min_support, min_confidence, min_occurrences
    )
    
    return rules_a1, rules_a2, rules_a3


def _prepare_skill_transactions(df: pd.DataFrame, skill_column: str) -> List[List[str]]:
    """Convert skill lists in DataFrame to transactions."""
    transactions = []
    for skills in df[skill_column]:
        if isinstance(skills, str):
            try:
                skills = ast.literal_eval(skills)
            except:
                skills = [s.strip().lower() for s in skills.split(',') if s.strip()]
        
        if isinstance(skills, list):
            transactions.append([str(s).strip().lower() for s in skills if s])
        else:
            transactions.append([])
    
    return transactions


def _prepare_category_transactions(df: pd.DataFrame, cat_column: str) -> List[List[str]]:
    """Convert skill categories to transactions."""
    transactions = []
    for cats_str in df[cat_column]:
        if pd.isna(cats_str):
            transactions.append([])
            continue
        
        cats_str = str(cats_str).strip().lower()
        if not cats_str:
            transactions.append([])
            continue
        
        cats = [c.strip() for c in cats_str.split(',') if c.strip()]
        transactions.append(cats)
    
    return transactions


def _prepare_combined_transactions(
    skill_txs: List[List[str]],
    cat_txs: List[List[str]]
) -> List[List[str]]:
    """Combine skill and category transactions."""
    combined = []
    for skills, cats in zip(skill_txs, cat_txs):
        combined.append(skills + cats)
    return combined


def _train_model_a1(
    transactions: List[List[str]],
    min_support: float,
    min_confidence: float,
    min_occurrences: int
) -> pd.DataFrame:
    """Train Model A1: Skill-level association rules."""
    if not transactions:
        return pd.DataFrame()
    
    # Filter rare skills
    n_transactions = len(transactions)
    min_occ = max(min_occurrences, int(min_support * n_transactions))
    
    skill_counts = Counter(skill for tx in transactions for skill in tx)
    valid_skills = {skill for skill, cnt in skill_counts.items() if cnt >= min_occ}
    
    filtered_tx = [[s for s in tx if s in valid_skills] for tx in transactions]
    
    # Encode and mine
    te = TransactionEncoder()
    te_ary = te.fit(filtered_tx).transform(filtered_tx, sparse=True)
    df_sparse = pd.DataFrame.sparse.from_spmatrix(te_ary, columns=te.columns_)
    
    freq_itemsets = fpgrowth(df_sparse, min_support=min_support, use_colnames=True)
    
    if len(freq_itemsets) == 0:
        return pd.DataFrame()
    
    rules = association_rules(freq_itemsets, metric="confidence", min_threshold=min_confidence)
    return rules


def _train_model_a2(
    transactions: List[List[str]],
    min_support: float,
    min_confidence: float
) -> pd.DataFrame:
    """Train Model A2: Category-level association rules."""
    if not transactions:
        return pd.DataFrame()
    
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    
    freq_itemsets = apriori(df, min_support=min_support, use_colnames=True)
    
    if len(freq_itemsets) == 0:
        return pd.DataFrame()
    
    rules = association_rules(freq_itemsets, metric="confidence", min_threshold=min_confidence)
    return rules


def _train_model_a3(
    transactions: List[List[str]],
    min_support: float,
    min_confidence: float,
    min_occurrences: int
) -> pd.DataFrame:
    """Train Model A3: Combined (skills + categories) rules."""
    if not transactions:
        return pd.DataFrame()
    
    # Filter rare items
    n_transactions = len(transactions)
    min_occ = max(min_occurrences, int(min_support * n_transactions))
    
    item_counts = Counter(item for tx in transactions for item in tx)
    valid_items = {item for item, cnt in item_counts.items() if cnt >= min_occ}
    
    filtered_tx = [[i for i in tx if i in valid_items] for tx in transactions]
    
    te = TransactionEncoder()
    te_ary = te.fit(filtered_tx).transform(filtered_tx, sparse=True)
    df_sparse = pd.DataFrame.sparse.from_spmatrix(te_ary, columns=te.columns_)
    
    freq_itemsets = fpgrowth(df_sparse, min_support=min_support, use_colnames=True)
    
    if len(freq_itemsets) == 0:
        return pd.DataFrame()
    
    rules = association_rules(freq_itemsets, metric="confidence", min_threshold=min_confidence)
    return rules


def load_models_from_csv(data_dir: str = 'data/processed') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load pre-trained association rules from CSV files.
    
    Args:
        data_dir: Directory containing association_rules_*.csv files
        
    Returns:
        Tuple of (rules_A1, rules_A2, rules_A3) DataFrames
    """
    data_path = Path(data_dir)
    
    try:
        rules_a1 = pd.read_csv(data_path / 'association_rules_skills.csv')
    except:
        rules_a1 = pd.DataFrame()
    
    try:
        rules_a2 = pd.read_csv(data_path / 'association_rules_categories.csv')
    except:
        rules_a2 = pd.DataFrame()
    
    try:
        rules_a3 = pd.read_csv(data_path / 'association_rules_combined.csv')
    except:
        rules_a3 = pd.DataFrame()
    
    return rules_a1, rules_a2, rules_a3


def save_models_to_csv(
    rules_a1: pd.DataFrame,
    rules_a2: pd.DataFrame,
    rules_a3: pd.DataFrame,
    output_dir: str = 'data/processed'
) -> None:
    """Save association rules to CSV files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if not rules_a1.empty:
        rules_a1.to_csv(f'{output_dir}/association_rules_skills.csv', index=False)
    
    if not rules_a2.empty:
        rules_a2.to_csv(f'{output_dir}/association_rules_categories.csv', index=False)
    
    if not rules_a3.empty:
        rules_a3.to_csv(f'{output_dir}/association_rules_combined.csv', index=False)


class AssociationMiner:
    def __init__(self, min_support=0.01, min_confidence=0.4, algorithm='fpgrowth'):
        """
        Initialize Association Rules Miner
        
        Args:
            min_support: Minimum support threshold
            min_confidence: Minimum confidence threshold
            algorithm: 'apriori' or 'fpgrowth'
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.algorithm = algorithm
        self.frequent_itemsets = None
        self.rules = None
        self.transaction_encoder = TransactionEncoder()
    
    def fit(self, transactions: List[List[str]]):
        """
        Fit the model on transaction data
        
        Args:
            transactions: List of transactions, each transaction is a list of items (skills)
        """
        # Encode transactions
        te_ary = self.transaction_encoder.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=self.transaction_encoder.columns_)
        
        # Find frequent itemsets
        if self.algorithm == 'fpgrowth':
            self.frequent_itemsets = fpgrowth(df, min_support=self.min_support, use_colnames=True)
        else:
            self.frequent_itemsets = apriori(df, min_support=self.min_support, use_colnames=True)
        
        # Generate association rules
        if len(self.frequent_itemsets) > 0:
            self.rules = association_rules(
                self.frequent_itemsets,
                metric="confidence",
                min_threshold=self.min_confidence
            )
            
            # Add lift metric if not present
            if 'lift' not in self.rules.columns and len(self.rules) > 0:
                # Calculate lift manually if needed
                self.rules['lift'] = self.rules['confidence'] / self.rules['consequent support']
        else:
            self.rules = pd.DataFrame()
        
        return self
    
    def get_rules_for_skill(self, target_skill: str) -> pd.DataFrame:
        """
        Get rules that have target_skill as consequent
        
        Args:
            target_skill: The skill to find rules for
        
        Returns:
            DataFrame with rules having target_skill as consequent
        """
        if self.rules is None or len(self.rules) == 0:
            return pd.DataFrame()
        
        target_lower = target_skill.lower().strip()
        
        def skill_in_consequents(consequents):
            if isinstance(consequents, (set, frozenset)):
                return any(s.lower().strip() == target_lower for s in consequents)
            elif isinstance(consequents, str):
                return target_lower in consequents.lower()
            return False
        
        mask = self.rules['consequents'].apply(skill_in_consequents)
        return self.rules[mask].sort_values('confidence', ascending=False)
    
    def get_recommendations(self, user_skills: List[str], top_n: int = 10) -> pd.DataFrame:
        """
        Get skill recommendations based on user's current skills
        
        Args:
            user_skills: List of skills the user has
            top_n: Number of recommendations to return
        
        Returns:
            DataFrame with recommended skills and their metrics
        """
        if self.rules is None or len(self.rules) == 0:
            return pd.DataFrame()
        
        if not user_skills:
            return pd.DataFrame()
        
        user_skills_set = set(s.lower().strip() for s in user_skills if s)
        if not user_skills_set:
            return pd.DataFrame()

        # Try to enrich user_skills_set with category mappings from the skills taxonomy
        try:
            from src.data.loader import DataLoader
            dl = DataLoader()
            skills_tax = dl.load_skills_taxonomy()
            if isinstance(skills_tax, pd.DataFrame) and 'skill_group_name' in skills_tax.columns and 'skill_group_category' in skills_tax.columns:
                for s in list(user_skills_set):
                    for _, r in skills_tax.iterrows():
                        name = str(r['skill_group_name']).lower().strip()
                        cat = str(r['skill_group_category']).lower().strip()
                        if not name or not cat:
                            continue
                        # If user skill is a substring of taxonomy name or vice-versa, map to category
                        if s in name or name in s:
                            user_skills_set.add(cat)
        except Exception:
            # If taxonomy not available, continue without enrichment
            pass
        # Heuristic keyword-to-category mapping for common skills (helps when taxonomy lacks exact matches)
        try:
            keyword_map = {
                'tech skills': ['python', 'java', 'c++', 'c#', 'javascript', 'node', 'react', 'django', 'flask', 'sql', 'spark', 'hadoop', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'docker', 'kubernetes', 'aws', 'azure', 'gcp'],
                'soft skills': ['communication', 'leadership', 'teamwork', 'time management', 'problem solving', 'presentation', 'negotiation'],
                'business skills': ['management', 'finance', 'accounting', 'sales', 'marketing', 'strategy', 'project management'],
                'disruptive tech skills': ['ai', 'machine learning', 'data science', 'robotics', 'blockchain', 'artificial intelligence'],
                'specialized industry skills': ['healthcare', 'pharmaceutical', 'engineering', 'law', 'aerospace', 'manufacturing']
            }
            for s in list(user_skills_set):
                for cat, kws in keyword_map.items():
                    for kw in kws:
                        if kw in s:
                            user_skills_set.add(cat)
                            break
        except Exception:
            pass
        
        recommendations = []
        
        # Find rules where user skills are in antecedents
        for idx, rule in self.rules.iterrows():
            try:
                # Handle different formats of antecedents/consequents
                antecedents = rule.get('antecedents', set())
                consequents = rule.get('consequents', set())
                
                # Convert to sets if needed
                if isinstance(antecedents, (frozenset, set)):
                    antecedents = set(antecedents)
                elif isinstance(antecedents, str):
                    antecedents = {antecedents}
                else:
                    antecedents = set(antecedents) if antecedents else set()
                
                if isinstance(consequents, (frozenset, set)):
                    consequents = set(consequents)
                elif isinstance(consequents, str):
                    consequents = {consequents}
                else:
                    consequents = set(consequents) if consequents else set()
                
                # Normalize
                antecedents = set(s.lower().strip() if isinstance(s, str) else str(s).lower().strip() for s in antecedents if s)
                consequents = set(s.lower().strip() if isinstance(s, str) else str(s).lower().strip() for s in consequents if s)
                
                # Relaxed matching: consider rules where antecedents are a subset OR overlap with user skills
                if antecedents and (antecedents.issubset(user_skills_set) or len(antecedents & user_skills_set) > 0):
                    match_count = len(antecedents & user_skills_set)
                    match_fraction = match_count / max(1, len(antecedents))
                    # Get skills in consequents that user doesn't have
                    new_skills = consequents - user_skills_set
                    
                    for skill in new_skills:
                        if skill and isinstance(skill, str):  # Ensure skill is valid
                            recommendations.append({
                                'skill': skill,
                                'based_on': ', '.join(sorted(antecedents)),
                                'confidence': float(rule.get('confidence', 0)),
                                'lift': float(rule.get('lift', 0)),
                                'support': float(rule.get('support', 0)),
                                'antecedent_match_fraction': match_fraction
                            })
            except Exception as e:
                # Skip rules that cause errors
                continue
        
        if not recommendations:
            return pd.DataFrame()

        # Convert to DataFrame and sort by match fraction then confidence
        rec_df = pd.DataFrame(recommendations)
        if 'antecedent_match_fraction' in rec_df.columns:
            rec_df = rec_df.sort_values(['antecedent_match_fraction', 'confidence'], ascending=[False, False])
        else:
            rec_df = rec_df.sort_values('confidence', ascending=False)
        rec_df = rec_df.drop_duplicates(subset=['skill'])

        return rec_df.head(top_n)
    
    def save(self, path: str):
        """Save the model to disk"""
        model_data = {
            'min_support': self.min_support,
            'min_confidence': self.min_confidence,
            'algorithm': self.algorithm,
            'frequent_itemsets': self.frequent_itemsets,
            'rules': self.rules,
            'transaction_encoder': self.transaction_encoder
        }
        joblib.dump(model_data, path)
    
    @classmethod
    def load(cls, path: str) -> 'AssociationMiner':
        """Load model from disk"""
        model_data = joblib.load(path)
        miner = cls(
            min_support=model_data.get('min_support', 0.01),
            min_confidence=model_data.get('min_confidence', 0.4),
            algorithm=model_data.get('algorithm', 'fpgrowth')
        )
        miner.frequent_itemsets = model_data.get('frequent_itemsets')
        miner.rules = model_data.get('rules')
        miner.transaction_encoder = model_data.get('transaction_encoder', TransactionEncoder())
        return miner
    
    def fit_from_dataframe(self, df: pd.DataFrame, skill_column: str = 'skill_list'):
        """
        Fit model from DataFrame with skill lists
        
        Args:
            df: DataFrame containing skill lists
            skill_column: Name of column containing skill lists
        """
        # Extract skill lists
        transactions = []
        for skills in df[skill_column]:
            if isinstance(skills, str):
                try:
                    import ast
                    skills = ast.literal_eval(skills)
                except:
                    skills = [s.strip() for s in skills.split(',')]
            
            if isinstance(skills, list):
                # Convert to lowercase for consistency
                transactions.append([s.lower().strip() for s in skills if s])
            else:
                transactions.append([])
        
        return self.fit(transactions)


class AssociationEnsemble:
    """Load multiple AssociationMiner models (pickles) and CSV fallbacks,
    query them and merge recommendations with provenance and a combined score.
    """
    def __init__(self):
        self.models: List[Dict[str, Any]] = []  # list of {'name':str, 'miner':AssociationMiner}

    def _load_csv_as_miner(self, path: str, name: str) -> AssociationMiner:
        df = pd.read_csv(path)
        # Expect columns like antecedents, consequents, confidence, lift, support
        # Normalize columns and parse antecedents/consequents
        for col in ['antecedents', 'consequents']:
            if col in df.columns:
                def _parse_cell(v):
                    if pd.isna(v):
                        return set()
                    if isinstance(v, (set, frozenset)):
                        return set(v)
                    if isinstance(v, (list, tuple)):
                        return set(str(x).lower().strip() for x in v if x)
                    if isinstance(v, str):
                        try:
                            val = ast.literal_eval(v)
                            if isinstance(val, (list, tuple, set, frozenset)):
                                return set(str(x).lower().strip() for x in val if x)
                        except Exception:
                            # fallback split by comma
                            parts = [p.strip().lower() for p in v.split(',') if p.strip()]
                            return set(parts)
                    return set()
                df[col] = df[col].apply(_parse_cell)

        # Ensure numeric cols exist
        for num in ['confidence', 'lift', 'support']:
            if num not in df.columns:
                df[num] = 0.0

        miner = AssociationMiner()
        miner.rules = df.rename(columns={
            'antecedents': 'antecedents',
            'consequents': 'consequents'
        })
        return miner

    def load_paths(self, paths: List[str]):
        """Load any number of model files (joblib pickles) and CSV rule exports.

        Args:
            paths: list of filesystem paths to model artifacts. File extension determines loader.
        """
        self.models = []
        for p in paths:
            pstr = str(p)
            if not pstr:
                continue
            if not os.path.exists(pstr):
                continue
            name = Path(pstr).stem
            try:
                if pstr.lower().endswith(('.pkl', '.joblib')):
                    miner = AssociationMiner.load(pstr)
                    self.models.append({'name': name, 'miner': miner, 'path': pstr})
                elif pstr.lower().endswith('.csv'):
                    miner = self._load_csv_as_miner(pstr, name)
                    self.models.append({'name': name, 'miner': miner, 'path': pstr})
            except Exception:
                # ignore problematic files
                continue

    def get_recommendations(self, user_skills: List[str], top_n: int = 10) -> pd.DataFrame:
        """Query each loaded model and merge recommendations.

        Returns a DataFrame with columns: skill, score, sources, top_source, details
        """
        if not self.models:
            return pd.DataFrame()
        all_recs = []
        # Gather recommendations from each model
        for entry in self.models:
            name = entry.get('name')
            miner: AssociationMiner = entry.get('miner')
            try:
                # Ask each miner for more than top_n to allow merging
                rec_df = miner.get_recommendations(user_skills, top_n=top_n * 3)
            except Exception:
                rec_df = pd.DataFrame()

            if rec_df is None or rec_df.empty:
                continue

            # normalize confidence per-model
            max_conf = rec_df['confidence'].max() if 'confidence' in rec_df.columns else 0.0
            for _, r in rec_df.iterrows():
                conf = float(r.get('confidence', 0.0))
                norm = (conf / max_conf) if max_conf and max_conf > 0 else 0.0
                all_recs.append({
                    'skill': str(r.get('skill')).lower().strip(),
                    'orig_confidence': conf,
                    'normalized_confidence': norm,
                    'lift': float(r.get('lift', 0.0)) if 'lift' in r and pd.notna(r.get('lift')) else 0.0,
                    'support': float(r.get('support', 0.0)) if 'support' in r and pd.notna(r.get('support')) else 0.0,
                    'based_on': r.get('based_on', None) if 'based_on' in r else None,
                    'antecedent_match_fraction': float(r.get('antecedent_match_fraction', 0.0)) if 'antecedent_match_fraction' in r else 0.0,
                    'source': name,
                    'path': entry.get('path')
                })

        if not all_recs:
            return pd.DataFrame()

        df = pd.DataFrame(all_recs)

        # Group by skill and combine confidences using noisy-or: 1 - prod(1 - c_i)
        grouped = {}
        for _, row in df.iterrows():
            skill = row['skill']
            grouped.setdefault(skill, []).append(row)

        combined = []
        for skill, rows in grouped.items():
            probs = [float(r['normalized_confidence']) for r in rows]
            prod_term = 1.0
            for p in probs:
                prod_term *= (1.0 - p)
            combined_score = 1.0 - prod_term
            sources = [r['source'] for r in rows]
            top_row = max(rows, key=lambda r: r['normalized_confidence'])
            details = [{'source': r['source'], 'orig_confidence': r['orig_confidence'], 'lift': r.get('lift', 0.0), 'based_on': r.get('based_on')} for r in rows]
            combined.append({
                'skill': skill,
                'score': combined_score,
                'sources': ','.join(sorted(set(sources))),
                'top_source': top_row['source'],
                'top_norm_confidence': float(top_row['normalized_confidence']),
                'details': details
            })

        out_df = pd.DataFrame(combined)
        out_df = out_df.sort_values('score', ascending=False).reset_index(drop=True)
        return out_df.head(top_n)


