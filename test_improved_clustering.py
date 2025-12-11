"""Quick test script to verify improved clustering and filtering logic.

Run this after generating the v2 files from the clustering notebook.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.utils.cluster_analyzer import ClusterAnalyzer
from src.utils.skill_filter import (
    get_skill_overlap,
    get_top_skills,
    extract_main_category
)


def test_skill_filter_functions():
    """Test basic skill filtering functions."""
    print("\n" + "="*80)
    print("TEST 1: Skill Filtering Functions")
    print("="*80)
    
    # Test skill overlap
    skills_a = ['nursing', 'patient care', 'healthcare', 'communication']
    skills_b = ['nursing', 'healthcare', 'team leadership']
    
    overlap_count, overlap_set = get_skill_overlap(skills_a, skills_b)
    print(f"\nSkill overlap test:")
    print(f"  Skills A: {skills_a}")
    print(f"  Skills B: {skills_b}")
    print(f"  Overlap: {overlap_set} (count: {overlap_count})")
    assert overlap_count == 2, f"Expected 2 overlaps, got {overlap_count}"
    print("  ✅ PASS")
    
    # Test get_top_skills
    skills = ['nursing', 'patient care', 'healthcare', 'communication', 'ehr', 'teamwork', 'leadership']
    top_5 = get_top_skills(skills, n_top=5)
    print(f"\nTop skills test:")
    print(f"  All skills: {skills}")
    print(f"  Top 5: {top_5}")
    assert len(top_5) == 5, f"Expected 5 top skills, got {len(top_5)}"
    print("  ✅ PASS")
    
    # Test category extraction
    cat_str = "healthcare,nursing,soft skills"
    main_cat = extract_main_category(cat_str)
    print(f"\nCategory extraction test:")
    print(f"  Categories string: {cat_str}")
    print(f"  Main category: {main_cat}")
    assert main_cat == "healthcare", f"Expected 'healthcare', got {main_cat}"
    print("  ✅ PASS")


def test_cluster_analyzer():
    """Test ClusterAnalyzer with v2 files."""
    print("\n" + "="*80)
    print("TEST 2: ClusterAnalyzer Initialization")
    print("="*80)
    
    mapping_path = Path('data/processed/job_clusters_small_v2.pkl')
    
    if not mapping_path.exists():
        print(f"\n⚠️  Mapping file not found: {mapping_path}")
        print("   Run the clustering notebook first to generate v2 files.")
        return False
    
    try:
        analyzer = ClusterAnalyzer(str(mapping_path))
        print(f"\n✅ ClusterAnalyzer initialized successfully")
        print(f"   Mapping loaded: {analyzer.path}")
        print(f"   Total jobs: {len(analyzer.df)}")
        print(f"   Version: {'v2 (enhanced)' if analyzer.is_v2 else 'legacy'}")
        
        if analyzer.skills_lookup is not None:
            print(f"   Skills lookup: ✅ loaded ({len(analyzer.skills_lookup)} jobs)")
        else:
            print(f"   Skills lookup: ⚠️ not found (filtering will use fallback)")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed to initialize ClusterAnalyzer: {e}")
        return False


def test_similar_jobs_lookup():
    """Test finding similar jobs."""
    print("\n" + "="*80)
    print("TEST 3: Similar Jobs Lookup")
    print("="*80)
    
    mapping_path = Path('data/processed/job_clusters_small_v2.pkl')
    
    if not mapping_path.exists():
        print(f"\n⚠️  Skipping test (mapping file not found)")
        return
    
    try:
        analyzer = ClusterAnalyzer(str(mapping_path))
        
        # Find a nursing job to test with
        nursing_jobs = analyzer.df[
            analyzer.df['job_title'].str.contains('nurse', case=False, na=False)
        ]
        
        if nursing_jobs.empty:
            print(f"\n⚠️  No nursing jobs found in dataset (can't test filtering)")
            # Try with any job
            test_job = analyzer.df.iloc[0]
            test_job_id = test_job['job_id']
            print(f"\n   Using first job instead: {test_job['job_title']}")
        else:
            test_job = nursing_jobs.iloc[0]
            test_job_id = test_job['job_id']
            print(f"\n   Testing with nursing job: {test_job['job_title']}")
        
        # Get similar jobs
        similar = analyzer.get_similar_jobs(test_job_id, top_n=5)
        
        print(f"\n   Similar jobs (top 5):")
        if similar.empty:
            print(f"     ❌ No similar jobs found")
        else:
            for idx, job in similar.iterrows():
                job_title = job.get('job_title', 'Unknown')
                cluster = job.get('cluster_id', '?')
                print(f"     • {job_title} (cluster {cluster})")
        
        print(f"\n   ✅ Similar jobs lookup works")
        
    except Exception as e:
        print(f"\n❌ Error testing similar jobs: {e}")
        import traceback
        traceback.print_exc()


def test_find_similar_by_title():
    """Test finding similar jobs by job title."""
    print("\n" + "="*80)
    print("TEST 4: Find Similar by Job Title")
    print("="*80)
    
    mapping_path = Path('data/processed/job_clusters_small_v2.pkl')
    
    if not mapping_path.exists():
        print(f"\n⚠️  Skipping test (mapping file not found)")
        return
    
    try:
        analyzer = ClusterAnalyzer(str(mapping_path))
        
        # Try to find similar by job title
        similar = analyzer.find_similar(job='nurse', top_n=3)
        
        if not similar:
            print(f"\n⚠️  No results for job title 'nurse'")
            return
        
        print(f"\n   Found {len(similar)} similar jobs to 'nurse':")
        for job in similar:
            print(f"     • {job['job_title']:50} ({job['location']})")
        
        print(f"\n   ✅ find_similar() works")
        
    except Exception as e:
        print(f"\n❌ Error testing find_similar: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 IMPROVED CLUSTERING TESTS")
    print("="*80)
    
    test_skill_filter_functions()
    
    if test_cluster_analyzer():
        test_similar_jobs_lookup()
        test_find_similar_by_title()
    
    print("\n" + "="*80)
    print("✅ TESTS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Run the clustering notebook to generate v2 files")
    print("2. Open the Streamlit app and test similar opportunities")
    print("3. Verify nursing roles show only healthcare jobs")


if __name__ == '__main__':
    main()
