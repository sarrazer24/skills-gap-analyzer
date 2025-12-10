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
                            # First try ast.literal_eval
                            val = ast.literal_eval(v)
                            if isinstance(val, (list, tuple, set, frozenset)):
                                return set(str(x).lower().strip() for x in val if x)
                        except Exception:
                            pass
                        # Try converting frozenset() call to a set literal
                        # e.g., frozenset({'item1', 'item2'}) -> extract the dict/set part
                        if v.startswith('frozenset('):
                            try:
                                # Extract content between frozenset( and )
                                inner = v[10:-1]  # Remove 'frozenset(' and ')'
                                val = ast.literal_eval(inner)
                                if isinstance(val, (list, tuple, set, frozenset, dict)):
                                    return set(str(x).lower().strip() for x in val if x)
                            except Exception:
                                pass
                        # Fallback: split by comma
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
        """
        Query each loaded association rule model and merge recommendations.
        
        This is the core method for extracting skill recommendations from association rules.
        It operates on multiple models (A1, A2, A3) and combines their predictions using
        a noisy-or aggregation approach to produce a unified ranking.
        
        **Important:** This method implements unsupervised association rule mining where:
        - Each model independently identifies rules where antecedents match user skills
        - Confidence scores measure how likely a consequent skill appears with user's skills
        - Lift indicates whether the association is stronger than random chance
        
        Args:
            user_skills: List of skills the user currently has (case-insensitive)
            top_n: Maximum number of top recommendations to return (default: 10)
        
        Returns:
            DataFrame with columns:
            - skill: Recommended skill name
            - score: Combined recommendation score (0-1, normalized)
            - sources: Comma-separated list of models that recommended this skill
            - top_source: Primary model recommending this skill (highest confidence)
            - top_norm_confidence: Normalized confidence from top source
            - details: List of dicts with per-model details (confidence, lift, antecedents)
        
        Edge Cases Handled:
        - No models loaded: returns empty DataFrame
        - User has no skills: returns empty DataFrame
        - No rules match user skills: returns empty DataFrame
        - Rules have malformed antecedents/consequents: gracefully skipped
        
        Examples:
            >>> ensemble = AssociationEnsemble()
            >>> ensemble.load_paths(['data/processed/association_rules_categories.csv'])
            >>> recs = ensemble.get_recommendations(['python', 'sql'], top_n=5)
            >>> print(recs[['skill', 'score', 'sources']])
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

    def get_skill_model_scores(
        self, 
        user_skills: List[str], 
        target_skills: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed model scores for specific target skills based on user's current skills.
        
        This method is designed for the personalized learning path generator. It analyzes
        how strongly each target skill is recommended by association rules, given the user's
        current skills.
        
        For each target skill, it:
        1. Searches all loaded models (A1, A2, A3) for rules where:
           - antecedents overlap with user_skills
           - consequents include this target skill
        2. Returns the strongest signals (confidence, lift) from each model
        3. Provides source information for explanation building
        
        Args:
            user_skills: Skills the user currently has (case-insensitive)
            target_skills: Skills to score (e.g., missing skills from gap analysis)
        
        Returns:
            Dict mapping skill -> {
                'model_scores': {
                    'A1': {'confidence': float, 'lift': float, 'rule_count': int},
                    'A2': {'confidence': float, 'lift': float, 'rule_count': int},
                    'A3': {'confidence': float, 'lift': float, 'rule_count': int},
                },
                'best_confidence': float (max across all models),
                'best_model': str (e.g., 'A1' or None),
                'total_signals': int (how many rules found this skill),
            }
        
        Example:
            >>> ensemble = AssociationEnsemble()
            >>> ensemble.load_paths(['data/processed/association_rules_categories.csv'])
            >>> scores = ensemble.get_skill_model_scores(
            ...     user_skills=['python', 'sql'],
            ...     target_skills=['machine learning', 'spark', 'aws']
            ... )
            >>> for skill, signals in scores.items():
            ...     print(f"{skill}: {signals['best_confidence']:.2%} (model: {signals['best_model']})")
        """
        
        if not self.models or not user_skills or not target_skills:
            return {}
        
        user_skills_set = set(s.lower().strip() for s in user_skills if s)
        target_skills_set = set(s.lower().strip() for s in target_skills if s)
        
        results = {}
        
        # For each target skill, find model signals
        for target_skill in target_skills_set:
            skill_scores = {
                'model_scores': {},
                'best_confidence': 0.0,
                'best_model': None,
                'total_signals': 0,
            }
            
            # Query each loaded model
            for model_entry in self.models:
                model_name = model_entry.get('name', 'unknown')
                miner = model_entry.get('miner')
                
                if miner is None or miner.rules is None or len(miner.rules) == 0:
                    continue
                
                # Find all rules matching this target skill
                matching_rules = []
                for idx, rule in miner.rules.iterrows():
                    try:
                        # Parse antecedents and consequents
                        ants = self._parse_itemset(rule.get('antecedents'))
                        cons = self._parse_itemset(rule.get('consequents'))
                        
                        # Check: user has some antecedents AND target skill is in consequents
                        if ants and cons and (ants & user_skills_set) and (target_skill in cons):
                            conf = float(rule.get('confidence', 0.0))
                            lift = float(rule.get('lift', 1.0))
                            matching_rules.append({'confidence': conf, 'lift': lift})
                    except Exception:
                        continue
                
                # Aggregate scores from matching rules
                if matching_rules:
                    best_conf = max(r['confidence'] for r in matching_rules)
                    avg_lift = sum(r['lift'] for r in matching_rules) / len(matching_rules)
                    
                    skill_scores['model_scores'][model_name] = {
                        'confidence': best_conf,
                        'lift': avg_lift,
                        'rule_count': len(matching_rules),
                    }
                    
                    skill_scores['total_signals'] += len(matching_rules)
                    
                    # Track best overall confidence
                    if best_conf > skill_scores['best_confidence']:
                        skill_scores['best_confidence'] = best_conf
                        skill_scores['best_model'] = model_name
            
            if skill_scores['model_scores']:  # Only include if we found signals
                results[target_skill] = skill_scores
        
        return results
    
    def score_skill_for_user(
        self,
        skill: str,
        user_skills: List[str],
        job_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Score a single skill for a user based on association rule models.
        
        This method is used by the personalized learning path generator to score
        individual skills. It looks up rules where:
        - The antecedents overlap with user_skills
        - The consequents include the target skill
        
        It aggregates confidence and lift across all matching rules from all models.
        
        Args:
            skill: The skill to score (e.g., 'spark')
            user_skills: List of skills the user currently has
            job_skills: Optional list of job skills (not currently used)
        
        Returns:
            Dict with:
            {
                "model_score": 0.0-1.0 (normalized),
                "sources": ["A1", "A2", "A3"] (which models recommended),
                "details": {
                    "confidence": 0.75,  # avg confidence across models
                    "lift": 1.3,         # avg lift across models
                    "rule_count": 8,     # how many rules matched
                    "per_model": {       # breakdown by model
                        "A1": {"confidence": 0.7, "lift": 1.2, "rules": 3},
                        "A3": {"confidence": 0.75, "lift": 1.3, "rules": 5}
                    }
                }
            }
        """
        if not self.models or not user_skills:
            return {
                "model_score": 0.0,
                "sources": [],
                "details": {"confidence": 0.0, "lift": 0.0, "rule_count": 0, "per_model": {}}
            }
        
        user_skills_set = set(s.lower().strip() for s in user_skills if s)
        skill_lower = skill.lower().strip()
        
        # Collect all matching rules across models
        all_confidences = []
        all_lifts = []
        per_model_details = {}
        matched_models = []
        
        for model_entry in self.models:
            model_name = model_entry.get('name', 'unknown')
            miner = model_entry.get('miner')
            
            if miner is None or not hasattr(miner, 'rules') or miner.rules is None or len(miner.rules) == 0:
                continue
            
            model_confidences = []
            model_lifts = []
            rule_count = 0
            
            try:
                for idx, rule in miner.rules.iterrows():
                    try:
                        # Parse antecedents and consequents
                        ants = self._parse_itemset(rule.get('antecedents'))
                        cons = self._parse_itemset(rule.get('consequents'))
                        
                        # Check: user has antecedents AND skill is in consequents
                        if ants and cons and (ants & user_skills_set) and (skill_lower in cons):
                            conf = float(rule.get('confidence', 0.0))
                            lift = float(rule.get('lift', 1.0))
                            
                            model_confidences.append(conf)
                            model_lifts.append(lift)
                            all_confidences.append(conf)
                            all_lifts.append(lift)
                            rule_count += 1
                    except Exception:
                        continue
            except Exception:
                continue
            
            # Store per-model details if we found matching rules
            if model_confidences:
                matched_models.append(model_name)
                per_model_details[model_name] = {
                    "confidence": max(model_confidences),  # max confidence from this model
                    "lift": sum(model_lifts) / len(model_lifts),  # avg lift
                    "rules": rule_count
                }
        
        # Aggregate across all models
        if all_confidences:
            avg_confidence = sum(all_confidences) / len(all_confidences)
            avg_lift = sum(all_lifts) / len(all_lifts) if all_lifts else 1.0
            # Normalize model score to 0-1 range using confidence
            model_score = min(1.0, avg_confidence)
        else:
            avg_confidence = 0.0
            avg_lift = 0.0
            model_score = 0.0
        
        return {
            "model_score": model_score,
            "sources": matched_models,
            "details": {
                "confidence": avg_confidence,
                "lift": avg_lift,
                "rule_count": len(all_confidences),
                "per_model": per_model_details
            }
        }
    
    @staticmethod
    def _parse_itemset(itemset_str: Any) -> set:
        """
        Parse antecedents/consequents from various formats.
        Handles: frozenset strings, sets, lists, etc.
        """
        if not itemset_str or (isinstance(itemset_str, float) and pd.isna(itemset_str)):
            return set()
        
        if isinstance(itemset_str, (set, frozenset)):
            return set(str(x).lower().strip() for x in itemset_str if x)
        
        itemset_str = str(itemset_str).strip()
        
        # Try literal_eval first
        try:
            parsed = ast.literal_eval(itemset_str)
            if isinstance(parsed, (set, frozenset, list, tuple)):
                return set(str(x).lower().strip() for x in parsed if x)
        except Exception:
            pass
        
        # Try frozenset() extraction
        if itemset_str.startswith('frozenset('):
            try:
                inner = itemset_str[10:-1]
                parsed = ast.literal_eval(inner)
                if isinstance(parsed, (set, frozenset, list, tuple, dict)):
                    return set(str(x).lower().strip() for x in parsed if x)
            except Exception:
                pass
        
        # Fallback: split by comma
        return set(
            x.strip().lower() 
            for x in itemset_str.split(',') 
            if x.strip()
        )


# ============================================================================
# PUBLIC HELPER FUNCTIONS FOR APP INTEGRATION
# ============================================================================

def get_association_rules_from_csv(
    data_dir: str = 'data/processed',
    use_models: List[str] = None
) -> AssociationEnsemble:
    """
    Load association rules from CSV files and return an ensemble.
    
    This is the main entry point for the Streamlit app to fetch association rules.
    It loads one or more CSV files (A1: skills, A2: categories, A3: combined)
    and wraps them in an AssociationEnsemble for unified recommendation generation.
    
    Args:
        data_dir: Directory containing association_rules_*.csv files
        use_models: List of models to load. Options: ['skills', 'categories', 'combined']
                   If None, tries to load all available models (categories first for priority).
    
    Returns:
        AssociationEnsemble instance with loaded rules, ready to call get_recommendations()
    
    Example:
        >>> ensemble = get_association_rules_from_csv('data/processed')
        >>> user_skills = ['python', 'sql', 'machine learning']
        >>> recommendations = ensemble.get_recommendations(user_skills, top_n=10)
        >>> print(recommendations[['skill', 'score', 'sources']])
    """
    data_path = Path(data_dir)
    ensemble = AssociationEnsemble()
    
    # Default: load categories first (best for interpretability), then skills
    if use_models is None:
        use_models = ['categories', 'skills', 'combined']
    
    model_files = {
        'skills': 'association_rules_skills.csv',
        'categories': 'association_rules_categories.csv',
        'combined': 'association_rules_combined.csv'
    }
    
    paths = []
    for model_name in use_models:
        if model_name in model_files:
            csv_file = data_path / model_files[model_name]
            if csv_file.exists():
                paths.append(str(csv_file))
    
    if paths:
        ensemble.load_paths(paths)
    
    return ensemble


def get_skill_recommendations_with_explanations(
    user_skills: List[str],
    target_job_skills: List[str] = None,
    data_dir: str = 'data/processed',
    top_n: int = 10,
    min_score: float = 0.0
) -> Dict[str, Any]:
    """
    Get skill recommendations from association rules WITH EXPLANATIONS.
    
    This is the highest-level function for the Streamlit app.
    It combines gap analysis with association rule recommendations,
    providing explanations for why each skill is recommended.
    
    Args:
        user_skills: Skills the user currently has
        target_job_skills: Skills required for the target job (optional, for context)
        data_dir: Directory containing association_rules_*.csv files
        top_n: Maximum number of recommendations to return
        min_score: Filter recommendations with score below this threshold
    
    Returns:
        Dict with keys:
        - 'success': bool indicating if recommendations were generated
        - 'recommendations': list of dicts with keys:
            * 'skill': skill name
            * 'score': recommendation score (0-1)
            * 'explanation': human-readable explanation
            * 'sources': which models recommended this skill
            * 'details': raw details for debugging
        - 'error_message': string if success=False
        - 'num_rules_loaded': count of rules loaded
    
    Example:
        >>> result = get_skill_recommendations_with_explanations(
        ...     user_skills=['python', 'sql'],
        ...     target_job_skills=['python', 'sql', 'spark', 'ml'],
        ...     data_dir='data/processed'
        ... )
        >>> if result['success']:
        ...     for rec in result['recommendations']:
        ...         print(f"📚 {rec['skill']}: {rec['explanation']}")
    """
    result = {
        'success': False,
        'recommendations': [],
        'error_message': None,
        'num_rules_loaded': 0
    }
    
    try:
        # Load ensemble
        ensemble = get_association_rules_from_csv(data_dir)
        
        # Count loaded rules
        total_rules = sum(
            len(m['miner'].rules) if m['miner'].rules is not None else 0
            for m in ensemble.models
        )
        result['num_rules_loaded'] = total_rules
        
        if total_rules == 0:
            result['error_message'] = (
                f"No association rules found in {data_dir}. "
                "Please run 02_association_rules.ipynb first to train the models."
            )
            return result
        
        # Normalize user skills
        user_skills_clean = [s.lower().strip() for s in (user_skills or []) if s]
        
        if not user_skills_clean:
            result['error_message'] = "User has no skills provided. Cannot generate recommendations."
            return result
        
        # Get recommendations from ensemble
        recs_df = ensemble.get_recommendations(user_skills_clean, top_n=top_n * 2)
        
        if recs_df is None or recs_df.empty:
            result['success'] = True  # Not an error, just no rules matched
            result['recommendations'] = []
            result['error_message'] = (
                "No recommendations found for these skills. "
                "Try building a broader skill profile."
            )
            return result
        
        # Filter by score and convert to output format
        for idx, row in recs_df.iterrows():
            score = float(row.get('score', 0.0))
            
            if score < min_score:
                continue
            
            skill = str(row.get('skill', '')).lower().strip()
            if not skill:
                continue
            
            # Build explanation
            sources = str(row.get('sources', '')).split(',')
            sources = [s.strip() for s in sources if s.strip()]
            
            # Translate model names to user-friendly descriptions
            source_descriptions = {
                'association_rules_skills': 'Skill-level patterns',
                'association_rules_categories': 'Category-level patterns',
                'association_rules_combined': 'Combined patterns',
                'skills': 'Skill-level patterns',
                'categories': 'Category-level patterns',
                'combined': 'Combined patterns'
            }
            
            friendly_sources = [
                source_descriptions.get(src, src) for src in sources
            ]
            
            explanation = (
                f"Based on {', '.join(friendly_sources)}: "
                f"users with your skills often need {skill} (confidence: {score:.1%})"
            )
            
            rec = {
                'skill': skill,
                'score': round(score, 4),
                'explanation': explanation,
                'sources': ','.join(sources),
                'details': {
                    'top_source': row.get('top_source'),
                    'top_norm_confidence': float(row.get('top_norm_confidence', 0.0)),
                    'raw_details': str(row.get('details', ''))
                }
            }
            
            result['recommendations'].append(rec)
        
        # Sort by score descending
        result['recommendations'].sort(key=lambda x: x['score'], reverse=True)
        result['recommendations'] = result['recommendations'][:top_n]
        result['success'] = True
        
        return result
    
    except Exception as e:
        result['error_message'] = f"Error loading recommendations: {str(e)}"
        return result

