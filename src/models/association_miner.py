"""Association Rules Mining Model"""
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder
from typing import List, Dict, Any, Optional
import joblib
import warnings
warnings.filterwarnings('ignore')


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
                
                # Check if user has all antecedents
                if antecedents and antecedents.issubset(user_skills_set):
                    # Get skills in consequents that user doesn't have
                    new_skills = consequents - user_skills_set
                    
                    for skill in new_skills:
                        if skill and isinstance(skill, str):  # Ensure skill is valid
                            recommendations.append({
                                'skill': skill,
                                'based_on': ', '.join(sorted(antecedents)),
                                'confidence': float(rule.get('confidence', 0)),
                                'lift': float(rule.get('lift', 0)),
                                'support': float(rule.get('support', 0))
                            })
            except Exception as e:
                # Skip rules that cause errors
                continue
        
        if not recommendations:
            return pd.DataFrame()
        
        # Convert to DataFrame and sort by confidence
        rec_df = pd.DataFrame(recommendations)
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

