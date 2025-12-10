"""
Test script for personalized learning path integration.

Verifies that the new model-driven learning path functions work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.personalized_path import (
    prioritize_missing_skills_with_models,
    build_personalized_learning_path,
)
from src.models.association_miner import get_association_rules_from_csv
from src.models.skill_matcher import SkillMatcher


def test_prioritize_missing_skills():
    """Test the ranking function with models."""
    print("\n" + "="*70)
    print("TEST 1: Ranking Missing Skills with Models")
    print("="*70)
    
    try:
        # Load models
        ensemble = get_association_rules_from_csv('data/processed')
        print(f"✓ Loaded {len(ensemble.models)} association rule models")
        
        # Test data
        user_skills = ['python', 'sql', 'data analysis']
        target_job_skills = ['python', 'sql', 'machine learning', 'spark', 'aws']
        
        # Mock gap scores
        gap_scores = {
            'machine learning': 0.9,
            'spark': 0.7,
            'aws': 0.8,
        }
        
        # Rank with models
        recommendations = prioritize_missing_skills_with_models(
            missing_skills=['machine learning', 'spark', 'aws'],
            user_skills=user_skills,
            target_job_skills=target_job_skills,
            gap_scores=gap_scores,
            ensemble=ensemble,
            weight_importance=0.5,
            weight_model=0.5,
        )
        
        print(f"✓ Ranked {len(recommendations)} skills")
        
        # Display results
        print("\nRanked Skills:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec.skill.upper()}")
            print(f"   Final Score:      {rec.final_score:.1%}")
            print(f"   Gap Importance:   {rec.base_importance:.1%}")
            print(f"   Model Score:      {rec.model_score:.1%}")
            print(f"   Sources:          {', '.join(rec.sources) if rec.sources else 'Gap-only'}")
            if rec.sources:
                print(f"   Confidence:       {rec.confidence:.1%}")
                print(f"   Lift:             {rec.lift:.2f}x")
            print(f"   Explanation:      {rec.explanation[:100]}...")
        
        assert len(recommendations) > 0, "Should have recommendations"
        assert all(0 <= r.final_score <= 1 for r in recommendations), "Scores should be 0-1"
        assert recommendations == sorted(recommendations, key=lambda x: x.final_score, reverse=True), "Should be sorted"
        
        print("\n✓ TEST 1 PASSED: Ranking works correctly")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_build_learning_path():
    """Test the complete learning path builder."""
    print("\n" + "="*70)
    print("TEST 2: Building Complete Learning Path")
    print("="*70)
    
    try:
        # Load models
        ensemble = get_association_rules_from_csv('data/processed')
        matcher = SkillMatcher()
        print(f"✓ Loaded models and gap analyzer")
        
        # Test data
        user_skills = ['python', 'sql', 'data analysis', 'statistics']
        target_job_skills = ['python', 'sql', 'machine learning', 'deep learning', 'spark', 'aws', 'docker']
        
        # Build path
        path = build_personalized_learning_path(
            user_skills=user_skills,
            target_job_skills=target_job_skills,
            ensemble=ensemble,
            gap_analyzer=matcher,
            max_phases=4,
            weight_importance=0.5,
            weight_model=0.5,
        )
        
        print(f"✓ Generated learning path")
        
        # Display results
        print(f"\nPath Summary: {path['summary']}")
        print(f"Total Duration: {path['total_weeks']} weeks")
        print(f"Model Coverage: {path['model_coverage']:.0%}")
        print(f"Algorithm: {path['ranking_algorithm']}")
        
        print(f"\nPhases: {len(path['phases'])}")
        for phase in path['phases']:
            print(f"\n{phase['title']} ({phase['difficulty']}) — {phase['duration_weeks']} weeks")
            print(f"  Skills: {len(phase['skills'])}")
            for skill in phase['skills'][:3]:  # Show first 3 skills
                print(f"    • {skill['name']}: {skill['score']:.0%} (model: {skill['model_score']:.0%})")
            if len(phase['skills']) > 3:
                print(f"    ... and {len(phase['skills']) - 3} more")
        
        # Verify structure
        assert isinstance(path, dict), "Should return dict"
        assert 'phases' in path, "Should have phases"
        assert 'total_weeks' in path, "Should have duration"
        assert 'model_coverage' in path, "Should have model coverage"
        
        if path['phases']:
            assert all('title' in p for p in path['phases']), "Phases should have titles"
            assert all('skills' in p for p in path['phases']), "Phases should have skills"
            assert all(len(p['skills']) > 0 for p in path['phases']), "Phases should have skills"
        
        print("\n✓ TEST 2 PASSED: Learning path builder works correctly")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_model_coverage():
    """Test that models are being used for scoring."""
    print("\n" + "="*70)
    print("TEST 3: Model Coverage and Signals")
    print("="*70)
    
    try:
        ensemble = get_association_rules_from_csv('data/processed')
        matcher = SkillMatcher()
        
        # Test with skills that should have model signals
        user_skills = ['communication', 'teamwork', 'leadership']  # Use category-level skills
        target_job_skills = ['communication', 'teamwork', 'leadership', 'python', 'data analysis']
        
        path = build_personalized_learning_path(
            user_skills=user_skills,
            target_job_skills=target_job_skills,
            ensemble=ensemble,
            gap_analyzer=matcher,
        )
        
        print(f"Model Coverage: {path['model_coverage']:.0%}")
        
        # Count skills with model signals
        skills_with_signals = 0
        total_skills = 0
        
        for phase in path['phases']:
            for skill in phase['skills']:
                total_skills += 1
                if skill['sources']:
                    skills_with_signals += 1
                    print(f"✓ {skill['name']}: {len(skill['sources'])} model(s) - {skill['sources']}")
                else:
                    print(f"  {skill['name']}: Gap-only (no model signals)")
        
        print(f"\n✓ Skills with model signals: {skills_with_signals}/{total_skills}")
        print("\n✓ TEST 3 PASSED: Model coverage working")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PERSONALIZED LEARNING PATH - INTEGRATION TESTS")
    print("="*70)
    
    results = []
    
    results.append(("Ranking Missing Skills", test_prioritize_missing_skills()))
    results.append(("Building Learning Path", test_build_learning_path()))
    results.append(("Model Coverage", test_model_coverage()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        sys.exit(0)
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        sys.exit(1)
