"""
Example usage and test cases for association rules recommender.

Run this to test the recommender system with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
from src.models.association_rules_recommender import AssociationRulesRecommender
from src.models.enhanced_gap_analyzer import EnhancedGapAnalyzer


# ============================================================================
# SAMPLE DATA
# ============================================================================

def create_sample_rules():
    """Create sample association rules for testing."""
    rules_data = {
        'antecedents': [
            frozenset({'python'}),
            frozenset({'python', 'linux'}),
            frozenset({'c++', 'linux'}),
            frozenset({'communication', 'teamwork'}),
            frozenset({'sql'}),
            frozenset({'python', 'sql'}),
        ],
        'consequents': [
            frozenset({'data analysis'}),
            frozenset({'backend development'}),
            frozenset({'systems programming'}),
            frozenset({'project management'}),
            frozenset({'database design'}),
            frozenset({'data science'}),
        ],
        'confidence': [0.85, 0.78, 0.92, 0.68, 0.75, 0.88],
        'lift': [2.1, 1.95, 2.8, 1.5, 1.8, 2.3],
        'support': [0.05, 0.03, 0.02, 0.04, 0.06, 0.04]
    }
    return pd.DataFrame(rules_data)


def create_sample_job_profiles():
    """Create sample job profiles for testing."""
    return {
        'Python Developer': {
            'required_skills': ['python', 'linux', 'git', 'sql', 'html/css'],
            'skill_prevalence': {'python': 0.99, 'linux': 0.85, 'git': 0.90}
        },
        'Backend Developer': {
            'required_skills': ['python', 'linux', 'backend development', 'sql', 'docker'],
            'skill_prevalence': {'python': 0.95, 'linux': 0.88}
        },
        'Data Scientist': {
            'required_skills': ['python', 'sql', 'data analysis', 'data science', 'machine learning'],
            'skill_prevalence': {'python': 0.98, 'data analysis': 0.92}
        },
        'Database Administrator': {
            'required_skills': ['sql', 'linux', 'database design', 'networking'],
            'skill_prevalence': {'sql': 0.99}
        },
        'Systems Engineer': {
            'required_skills': ['c++', 'linux', 'systems programming', 'networking', 'assembly'],
            'skill_prevalence': {'c++': 0.95, 'linux': 0.92}
        }
    }


def create_sample_skill_categories():
    """Create sample skill-to-category mapping."""
    return {
        'python': 'programming languages',
        'c++': 'programming languages',
        'sql': 'databases',
        'linux': 'systems',
        'git': 'devops',
        'docker': 'devops',
        'html/css': 'frontend',
        'communication': 'soft skills',
        'teamwork': 'soft skills',
        'project management': 'soft skills',
        'data analysis': 'data science',
        'data science': 'data science',
        'backend development': 'development',
        'systems programming': 'systems',
        'database design': 'databases',
        'networking': 'systems',
        'machine learning': 'data science',
        'assembly': 'systems'
    }


# ============================================================================
# TEST CASES
# ============================================================================

def test_learning_paths():
    """Test smart learning path generation."""
    print("\n" + "="*70)
    print("TEST 1: SMART LEARNING PATH GENERATION")
    print("="*70)
    
    rules = create_sample_rules()
    recommender = AssociationRulesRecommender(rules_a1=rules)
    
    user_skills = ['python', 'linux']
    missing_skills = ['data analysis', 'backend development', 'systems programming']
    
    print(f"\nUser Skills: {user_skills}")
    print(f"Missing Skills: {missing_skills}")
    
    paths = recommender.generate_learning_paths(user_skills, missing_skills, top_n=3)
    
    if not paths:
        print("⚠️ No learning paths found")
        return
    
    print(f"\n✅ Found {len(paths)} learning paths:\n")
    
    for i, path in enumerate(paths, 1):
        print(f"Path {i}: Learn '{path['target_skill']}'")
        print(f"  Confidence: {path['confidence']*100:.1f}%")
        print(f"  Prerequisites needed: {path['prerequisites']}")
        print(f"  You already have: {path['existing_prereqs']}")
        print(f"  You need to learn: {path['missing_prereqs']}")
        print(f"  Learning order: {' → '.join(path['optimal_order'])}")
        print()


def test_skill_alternatives():
    """Test skill substitution suggestions."""
    print("\n" + "="*70)
    print("TEST 2: SKILL SUBSTITUTION SUGGESTIONS")
    print("="*70)
    
    rules = create_sample_rules()
    recommender = AssociationRulesRecommender(rules_a1=rules)
    
    user_skills = ['python', 'sql', 'communication']
    missing_skill = 'data science'
    
    print(f"\nUser Skills: {user_skills}")
    print(f"Missing Skill: {missing_skill}")
    
    alternatives = recommender.suggest_skill_alternatives(user_skills, missing_skill, top_n=2)
    
    if not alternatives:
        print("⚠️ No alternatives found")
        return
    
    print(f"\n✅ Found {len(alternatives)} alternatives:\n")
    
    for i, alt in enumerate(alternatives, 1):
        print(f"Alternative {i}:")
        print(f"  Skills: {alt['user_skills_involved']} → {alt['alternative_skill']}")
        print(f"  Confidence: {alt['confidence']*100:.1f}%")
        print(f"  Note: {alt['reasoning']}")
        print()


def test_related_jobs():
    """Test related job recommendations."""
    print("\n" + "="*70)
    print("TEST 3: RELATED JOB RECOMMENDATIONS")
    print("="*70)
    
    recommender = AssociationRulesRecommender(
        skill_to_category=create_sample_skill_categories()
    )
    
    user_skills = ['python', 'sql', 'linux']
    current_job = 'Python Developer'
    job_profiles = create_sample_job_profiles()
    
    print(f"\nUser Skills: {user_skills}")
    print(f"Current Job: {current_job}")
    
    related = recommender.suggest_related_jobs(user_skills, current_job, job_profiles, top_n=3)
    
    if not related:
        print("⚠️ No related jobs found")
        return
    
    print(f"\n✅ Found {len(related)} related jobs:\n")
    
    for i, job in enumerate(related, 1):
        print(f"Job {i}: {job['job_role']}")
        print(f"  Match Rate: {job['match_rate']*100:.1f}%")
        print(f"  Skills you have: {job['matched_skills_count']}")
        print(f"  Skills you need: {job['missing_skills_count']}")
        print(f"  Top skills to learn: {job['additional_skills_needed']}")
        print(f"  Category Similarity: {job['category_similarity']*100:.1f}%")
        print()


def test_rule_validation():
    """Test association rule validation."""
    print("\n" + "="*70)
    print("TEST 4: ASSOCIATION RULE VALIDATION")
    print("="*70)
    
    rules = create_sample_rules()
    recommender = AssociationRulesRecommender(rules_a1=rules)
    
    metrics = recommender.validate_rules()
    
    print(f"\n✅ Rule Validation Metrics:\n")
    print(f"  Total Rules: {metrics['total_rules']}")
    print(f"  Average Confidence: {metrics['avg_confidence']:.3f}")
    print(f"  Average Lift: {metrics['avg_lift']:.3f}")
    print(f"  Average Support: {metrics['avg_support']:.4f}")
    print(f"  Confidence Range: {metrics['confidence_range'][0]:.2f} - {metrics['confidence_range'][1]:.2f}")
    print(f"  Lift Range: {metrics['lift_range'][0]:.2f} - {metrics['lift_range'][1]:.2f}")
    print(f"  Trivial Rules: {metrics['trivial_rules']} ({metrics['trivial_percentage']:.1f}%)")
    print(f"  High-Quality Rules: {metrics['high_quality_rules']} ({metrics['high_quality_percentage']:.1f}%)")
    
    print(f"\n  Sample Rules ({len(metrics['sample_rules'])}):")
    for i, rule in enumerate(metrics['sample_rules'], 1):
        print(f"    {i}. {rule['antecedents']} → {rule['consequents']}")
        print(f"       Confidence: {rule['confidence']:.2f}, Lift: {rule['lift']:.2f}")


def test_enhanced_analyzer():
    """Test enhanced gap analyzer."""
    print("\n" + "="*70)
    print("TEST 5: ENHANCED GAP ANALYSIS")
    print("="*70)
    
    rules = create_sample_rules()
    skill_categories = create_sample_skill_categories()
    job_profiles = create_sample_job_profiles()
    
    recommender = AssociationRulesRecommender(
        rules_a1=rules,
        skill_to_category=skill_categories
    )
    analyzer = EnhancedGapAnalyzer(recommender, skill_categories)
    
    user_skills = ['python', 'linux']
    target_job = 'Data Scientist'
    
    print(f"\nUser Skills: {user_skills}")
    print(f"Target Job: {target_job}")
    
    gap_analysis = analyzer.analyze_gap(user_skills, target_job, job_profiles, enhanced=True)
    
    print(f"\n✅ Gap Analysis Results:\n")
    print(f"  Match Rate: {gap_analysis['match_percentage']:.1f}%")
    print(f"  Matched Skills: {gap_analysis['matched_skills']}")
    print(f"  Missing Skills: {gap_analysis['missing_skills']}")
    
    if gap_analysis.get('learning_paths'):
        print(f"\n  Learning Paths ({len(gap_analysis['learning_paths'])}):")
        for path in gap_analysis['learning_paths'][:2]:
            print(f"    → {path['target_skill']} ({path['confidence']*100:.0f}% confidence)")
    
    if gap_analysis.get('related_jobs'):
        print(f"\n  Related Jobs ({len(gap_analysis['related_jobs'])}):")
        for job in gap_analysis['related_jobs'][:3]:
            print(f"    → {job['job_role']} ({job['match_rate']*100:.0f}% match)")


def test_job_ranking():
    """Test job ranking functionality."""
    print("\n" + "="*70)
    print("TEST 6: JOB RANKING BY SKILL MATCH")
    print("="*70)
    
    recommender = AssociationRulesRecommender(
        skill_to_category=create_sample_skill_categories()
    )
    analyzer = EnhancedGapAnalyzer(recommender)
    
    user_skills = ['python', 'sql', 'linux']
    job_profiles = create_sample_job_profiles()
    
    print(f"\nUser Skills: {user_skills}\n")
    
    ranked_jobs = analyzer.rank_jobs_by_match(user_skills, job_profiles)
    
    print("✅ Jobs Ranked by Match Rate:\n")
    for idx, row in ranked_jobs.iterrows():
        match_pct = row['match_rate'] * 100
        print(f"  {idx+1}. {row['job_role']}")
        print(f"     Match: {match_pct:.1f}% | Matched: {int(row['matched_skills'])}/{int(row['required_skills'])} | Missing: {int(row['missing_skills'])}")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("ASSOCIATION RULES RECOMMENDER - TEST SUITE")
    print("="*70)
    
    try:
        test_learning_paths()
        test_skill_alternatives()
        test_related_jobs()
        test_rule_validation()
        test_enhanced_analyzer()
        test_job_ranking()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
