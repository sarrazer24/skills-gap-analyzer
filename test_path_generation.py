#!/usr/bin/env python
"""Quick test of learning path generation"""

from src.models.learning_path_generator import build_personalized_learning_path
from src.models.association_miner import get_association_rules_from_csv

ensemble = get_association_rules_from_csv('data/processed')
print(f"Ensemble loaded with {len(ensemble.models)} models")

user_skills = ['biology', 'education', 'microsoft office']
job_skills = ['biology', 'education', 'classroom management', 'curriculum development', 'student assessment', 'communication', 'problem solving', 'lesson planning', 'data analysis', 'microsoft office', 'google workspace', 'presentation skills', 'teamwork', 'time management', 'research', 'subject matter expertise', 'educational technology', 'assessment design', 'instructional design', 'student engagement']

path = build_personalized_learning_path(user_skills, job_skills, ensemble, max_phases=4)
print(f"Path phases: {len(path.get('phases', []))}")
print(f"Total weeks: {path.get('total_weeks', 0)}")
print(f"Missing count: {path.get('missing_count', 0)}")
if path.get('phases'):
    for phase in path['phases'][:2]:
        print(f"  Phase {phase['phase_number']}: {phase['title']} ({len(phase['skills'])} skills)")
        for skill in phase['skills'][:2]:
            print(f"    - {skill['name']}: final_score={skill['final_score']:.2f}")
else:
    print(f"Message: {path.get('message')}")
