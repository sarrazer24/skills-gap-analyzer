#!/usr/bin/env python
"""Test skill gap analysis functionality"""

from src.data.loader import DataLoader
from src.models.skill_matcher import SkillMatcher

def test_gap_analysis():
    """Test the skill gap analysis matching"""
    print("\n" + "="*60)
    print("🧪 Testing Skill Gap Analysis")
    print("="*60)
    
    # Initialize
    loader = DataLoader()
    skill_to_cat = loader.get_skill_to_category_map()
    matcher = SkillMatcher(skill_to_cat)
    
    # Test case 1: Basic matching
    print("\n📋 Test 1: Basic Matching")
    user_skills = ['python', 'sql', 'tableau']
    job_skills = ['python', 'sql', 'aws', 'docker', 'kubernetes']
    
    gap = matcher.analyze_gap(user_skills, job_skills)
    
    print(f"User skills: {user_skills}")
    print(f"Job skills: {job_skills}")
    print(f"✅ Matching: {gap['matching']}")
    print(f"❌ Missing: {gap['missing']}")
    print(f"📊 Extra: {gap['extra']}")
    print(f"📈 Coverage: {gap['coverage_percentage']}%")
    
    # Verify correctness
    assert gap['matching'] == ['python', 'sql'], f"Matching mismatch: {gap['matching']}"
    assert set(gap['missing']) == {'aws', 'docker', 'kubernetes'}, f"Missing mismatch: {gap['missing']}"
    assert gap['extra'] == ['tableau'], f"Extra mismatch: {gap['extra']}"
    print("✅ Test 1 passed!")
    
    # Test case 2: Case-insensitive matching
    print("\n📋 Test 2: Case-Insensitive Matching")
    user_skills2 = ['Python', 'SQL', 'TABLEAU']
    job_skills2 = ['python', 'sql', 'AWS', 'DOCKER']
    
    gap2 = matcher.analyze_gap(user_skills2, job_skills2)
    
    print(f"User skills (mixed case): {user_skills2}")
    print(f"Job skills (mixed case): {job_skills2}")
    print(f"✅ Matching: {gap2['matching']}")
    print(f"❌ Missing: {gap2['missing']}")
    print(f"📈 Coverage: {gap2['coverage_percentage']}%")
    
    assert gap2['matching'] == ['python', 'sql'], f"Case-insensitive matching failed: {gap2['matching']}"
    print("✅ Test 2 passed!")
    
    # Test case 3: No matching skills
    print("\n📋 Test 3: No Matching Skills")
    user_skills3 = ['excel', 'word']
    job_skills3 = ['python', 'java', 'javascript']
    
    gap3 = matcher.analyze_gap(user_skills3, job_skills3)
    
    print(f"User skills: {user_skills3}")
    print(f"Job skills: {job_skills3}")
    print(f"✅ Matching: {gap3['matching']}")
    print(f"❌ Missing: {gap3['missing']}")
    print(f"📈 Coverage: {gap3['coverage_percentage']}%")
    
    assert gap3['matching'] == [], f"Should have no matching skills: {gap3['matching']}"
    assert gap3['coverage_percentage'] == 0, f"Coverage should be 0%: {gap3['coverage_percentage']}"
    print("✅ Test 3 passed!")
    
    # Test case 4: Perfect match
    print("\n📋 Test 4: Perfect Match")
    user_skills4 = ['python', 'java', 'sql']
    job_skills4 = ['python', 'java', 'sql']
    
    gap4 = matcher.analyze_gap(user_skills4, job_skills4)
    
    print(f"User skills: {user_skills4}")
    print(f"Job skills: {job_skills4}")
    print(f"✅ Matching: {gap4['matching']}")
    print(f"❌ Missing: {gap4['missing']}")
    print(f"📈 Coverage: {gap4['coverage_percentage']}%")
    
    assert gap4['matching'] == sorted(user_skills4), f"Should match all skills: {gap4['matching']}"
    assert gap4['coverage_percentage'] == 100, f"Coverage should be 100%: {gap4['coverage_percentage']}"
    print("✅ Test 4 passed!")
    
    print("\n" + "="*60)
    print("✅ All tests passed successfully!")
    print("="*60)

if __name__ == '__main__':
    test_gap_analysis()
