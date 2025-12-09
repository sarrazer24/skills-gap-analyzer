"""
Model Validator - Association Rules Quality Assessment

Validates and reports metrics for trained association rule models.
"""

import pandas as pd
from typing import Dict, Optional, Tuple, List
import numpy as np


class ModelValidator:
    """
    Validate and assess quality of association rule models.
    
    Provides:
    - Rule quality metrics (support, confidence, lift)
    - Coverage analysis
    - Rule strength distribution
    - Model comparison
    """
    
    def __init__(self):
        """Initialize validator."""
        pass
    
    def validate_rules(self, rules_df: pd.DataFrame) -> Dict:
        """
        Validate association rules and return quality metrics.
        
        Args:
            rules_df: DataFrame with columns: antecedents, consequents, support, confidence, lift
            
        Returns:
            Dict with validation metrics
        """
        if rules_df.empty:
            return {
                'status': 'empty',
                'message': 'No rules to validate',
                'total_rules': 0
            }
        
        metrics = {
            'total_rules': len(rules_df),
            'support': self._analyze_metric(rules_df, 'support'),
            'confidence': self._analyze_metric(rules_df, 'confidence'),
            'lift': self._analyze_metric(rules_df, 'lift'),
            'rule_quality_distribution': self._get_quality_distribution(rules_df),
            'strong_rules_count': self._count_strong_rules(rules_df),
            'coverage': self._calculate_coverage(rules_df),
            'status': 'valid'
        }
        
        return metrics
    
    def compare_models(
        self,
        rules_a1: Optional[pd.DataFrame] = None,
        rules_a2: Optional[pd.DataFrame] = None,
        rules_a3: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Compare three association rule models (A1, A2, A3).
        
        Args:
            rules_a1: Skill-level rules
            rules_a2: Category-level rules
            rules_a3: Combined rules
            
        Returns:
            Dict with comparison metrics
        """
        comparison = {}
        
        for name, rules in [('A1_skills', rules_a1), ('A2_categories', rules_a2), ('A3_combined', rules_a3)]:
            if rules is not None and not rules.empty:
                comparison[name] = self.validate_rules(rules)
        
        return comparison
    
    def get_rule_summary(self, rules_df: pd.DataFrame) -> str:
        """
        Get human-readable summary of rules.
        
        Args:
            rules_df: Association rules DataFrame
            
        Returns:
            Formatted summary string
        """
        if rules_df.empty:
            return "No rules available"
        
        metrics = self.validate_rules(rules_df)
        
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║           ASSOCIATION RULES VALIDATION SUMMARY                 ║
╠════════════════════════════════════════════════════════════════╣
║ Total Rules:           {metrics['total_rules']:>40}║
║ Strong Rules (conf>0.5): {metrics['strong_rules_count']:>36}║
║                                                                ║
║ SUPPORT (Item Frequency):                                      ║
║   Min:  {metrics['support']['min']:<40.4f}║
║   Avg:  {metrics['support']['mean']:<40.4f}║
║   Max:  {metrics['support']['max']:<40.4f}║
║                                                                ║
║ CONFIDENCE (Rule Strength):                                    ║
║   Min:  {metrics['confidence']['min']:<40.4f}║
║   Avg:  {metrics['confidence']['mean']:<40.4f}║
║   Max:  {metrics['confidence']['max']:<40.4f}║
║                                                                ║
║ LIFT (Rule Importance):                                        ║
║   Min:  {metrics['lift']['min']:<40.4f}║
║   Avg:  {metrics['lift']['mean']:<40.4f}║
║   Max:  {metrics['lift']['max']:<40.4f}║
║                                                                ║
║ QUALITY DISTRIBUTION:                                          ║
"""
        
        dist = metrics['rule_quality_distribution']
        summary += f"║   High Quality (conf>0.7): {dist['high']:<24} ({dist['high']/len(rules_df)*100:>5.1f}%)║\n"
        summary += f"║   Medium Quality (0.5-0.7): {dist['medium']:<21} ({dist['medium']/len(rules_df)*100:>5.1f}%)║\n"
        summary += f"║   Low Quality (conf<0.5):   {dist['low']:<24} ({dist['low']/len(rules_df)*100:>5.1f}%)║\n"
        
        summary += f"""║                                                                ║
║ OVERALL STATUS:       {metrics['status']:<42}║
╚════════════════════════════════════════════════════════════════╝
"""
        
        return summary
    
    def get_top_rules(
        self,
        rules_df: pd.DataFrame,
        n: int = 10,
        metric: str = 'confidence'
    ) -> pd.DataFrame:
        """
        Get top N rules by specified metric.
        
        Args:
            rules_df: Association rules DataFrame
            n: Number of rules to return
            metric: Metric to sort by ('confidence', 'support', 'lift')
            
        Returns:
            DataFrame with top rules
        """
        if rules_df.empty or metric not in rules_df.columns:
            return pd.DataFrame()
        
        return rules_df.nlargest(n, metric)[
            ['antecedents', 'consequents', 'support', 'confidence', 'lift']
        ]
    
    def validate_model_for_production(self, rules_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Check if model is ready for production.
        
        Args:
            rules_df: Association rules DataFrame
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check if rules exist
        if rules_df.empty:
            warnings.append("No rules found")
            return False, warnings
        
        # Check minimum rules
        if len(rules_df) < 100:
            warnings.append(f"Only {len(rules_df)} rules - consider more training data")
        
        # Check confidence
        avg_confidence = rules_df['confidence'].mean()
        if avg_confidence < 0.4:
            warnings.append(f"Average confidence is low ({avg_confidence:.2f})")
        
        # Check support
        avg_support = rules_df['support'].mean()
        if avg_support < 0.01:
            warnings.append(f"Average support is very low ({avg_support:.4f})")
        
        # Check for required columns
        required_cols = ['antecedents', 'consequents', 'support', 'confidence', 'lift']
        missing_cols = [col for col in required_cols if col not in rules_df.columns]
        if missing_cols:
            warnings.append(f"Missing columns: {missing_cols}")
            return False, warnings
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    # ============= Helper Methods =============
    
    def _analyze_metric(self, rules_df: pd.DataFrame, metric: str) -> Dict:
        """Analyze a metric column."""
        if metric not in rules_df.columns:
            return {'min': 0, 'mean': 0, 'max': 0, 'std': 0}
        
        series = rules_df[metric]
        return {
            'min': float(series.min()),
            'mean': float(series.mean()),
            'median': float(series.median()),
            'max': float(series.max()),
            'std': float(series.std()),
            'q25': float(series.quantile(0.25)),
            'q75': float(series.quantile(0.75)),
        }
    
    def _get_quality_distribution(self, rules_df: pd.DataFrame) -> Dict[str, int]:
        """Get distribution of rule quality levels."""
        if 'confidence' not in rules_df.columns:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        confidences = rules_df['confidence']
        
        return {
            'high': int((confidences > 0.7).sum()),
            'medium': int(((confidences > 0.5) & (confidences <= 0.7)).sum()),
            'low': int((confidences <= 0.5).sum()),
        }
    
    def _count_strong_rules(self, rules_df: pd.DataFrame) -> int:
        """Count rules with confidence > 0.5 (strong rules)."""
        if 'confidence' not in rules_df.columns:
            return 0
        
        return int((rules_df['confidence'] > 0.5).sum())
    
    def _calculate_coverage(self, rules_df: pd.DataFrame) -> Dict:
        """Calculate rule coverage statistics."""
        if 'antecedents' not in rules_df.columns:
            return {'unique_antecedents': 0, 'unique_consequents': 0}
        
        all_antecedents = set()
        all_consequents = set()
        
        for idx, row in rules_df.iterrows():
            try:
                antecedents = self._parse_frozenset(row['antecedents'])
                consequents = self._parse_frozenset(row['consequents'])
                
                all_antecedents.update(antecedents)
                all_consequents.update(consequents)
            except:
                pass
        
        return {
            'unique_antecedents': len(all_antecedents),
            'unique_consequents': len(all_consequents),
            'total_unique_items': len(all_antecedents | all_consequents),
        }
    
    def _parse_frozenset(self, s) -> list:
        """Parse frozenset string."""
        if pd.isna(s) or not s:
            return []
        
        s = str(s).strip()
        try:
            if s.startswith("frozenset("):
                s = s.replace("frozenset(", "").rstrip(")")
            
            import ast
            items = ast.literal_eval(s)
            return list(items) if isinstance(items, (set, frozenset)) else [items]
        except:
            return []
