"""Small helper to show per-skill learning roadmap from SkillGapAnalyzer
Usage:
    python scripts/show_learning_roadmap.py python sql "machine learning"
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.models.gap_analyzer import SkillGapAnalyzer

skills = sys.argv[1:] if len(sys.argv) > 1 else ['python', 'sql', 'docker']

sga = SkillGapAnalyzer()

for skill in skills:
    plan = sga._get_learning_resources(skill)
    print('\n' + '='*80)
    print(f"Skill: {skill}")
    print('='*80)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
