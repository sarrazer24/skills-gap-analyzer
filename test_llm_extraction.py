"""Test LLM skill extraction to verify it works with OPEN_API_KEY from environment."""

import os
import sys
sys.path.insert(0, '.')

from src.models.skill_extractor import SkillExtractor

print("=" * 60)
print("Testing LLM Skill Extraction")
print("=" * 60)

# Sample skills to extract
test_skills = [
    "python", "sql", "machine learning", "excel", "tableau", 
    "aws", "pandas", "scikit-learn", "tensorflow", "pytorch",
    "docker", "git", "java", "javascript", "react",
    "deep learning", "data analysis", "statistics", "r", "scala"
]

# Sample CV/description text
test_text = """
I am a Senior Data Scientist with 5 years of experience. 

Technical Skills:
- Python programming (NumPy, Pandas, Scikit-learn)
- Machine learning and deep learning (TensorFlow, PyTorch)
- SQL database design and optimization
- Data visualization with Tableau and Matplotlib
- Statistical analysis and R programming
- AWS cloud services (S3, EC2, SageMaker)
- Docker containerization
- Version control with Git

Experience:
- Built predictive models using Python and scikit-learn
- Developed deep learning models with TensorFlow
- Created data pipelines with Pandas
- Designed Tableau dashboards for business intelligence
- Managed AWS infrastructure for ML projects
- Collaborated using Git for version control

Education:
- MS in Statistics
- BS in Mathematics
"""

print("\nTest Text Sample (first 300 chars):")
print(test_text[:300] + "...\n")

# Test 1: Pattern matching (fallback)
print("[1] Pattern Matching Extraction (Fallback)...")
extractor_pattern = SkillExtractor(test_skills, use_llm=False)
pattern_results = extractor_pattern.extract_from_text(test_text, return_confidence=True)
print(f"    Found {len(pattern_results)} skills")
if pattern_results:
    print(f"    Top 5: {[s for s, c in pattern_results[:5]]}")

# Test 2: LLM extraction
print("\n[2] LLM Extraction (using OPEN_API_KEY from environment)...")

# Check for API key
api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY")
if api_key:
    print(f"    API Key found ({len(api_key)} chars)")
    try:
        extractor_llm = SkillExtractor(test_skills, use_llm=True, api_key=api_key)
        llm_results = extractor_llm.extract_from_text(test_text, return_confidence=True)
        print(f"    Found {len(llm_results)} skills via LLM")
        if llm_results:
            print(f"    Top 5: {[s for s, c in llm_results[:5]]}")
        
        # Comparison
        pattern_skills = {s for s, c in pattern_results}
        llm_skills = {s for s, c in llm_results}
        
        print("\n[3] Comparison:")
        print(f"    Pattern matching found: {len(pattern_skills)} skills")
        print(f"    LLM extraction found: {len(llm_skills)} skills")
        print(f"    Both methods agree on: {len(pattern_skills & llm_skills)} skills")
        print(f"    LLM found additional: {len(llm_skills - pattern_skills)} skills")
        
        if llm_skills - pattern_skills:
            print(f"    Additional LLM skills: {list(llm_skills - pattern_skills)[:5]}")
            
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}")
        print("    (This is expected if API key is invalid or no network access)")
else:
    print("    ERROR: No API key found in OPENAI_API_KEY or OPEN_API_KEY environment variables")
    print("    Set the key first, then run this test again")

print("\n" + "=" * 60)
