# Personalized Learning Path Integration Guide

This document explains how to integrate the new model-driven personalized learning path system into the Streamlit app.

## Overview

The new learning path system uses:

1. **Gap Analysis** (from `SkillMatcher`): Identifies missing skills
2. **Association Rule Models** (A1, A2, A3): Provides ranking signals via confidence and lift
3. **Personalized Ranking**: Combines gap importance with model signals to create ranked learning path

## Architecture

### Three-Layer Approach

```
┌─────────────────────────────────────────────────────────────┐
│ Gap Analysis Layer                                          │
│ - User skills vs Target job skills                          │
│ - Identifies missing skills                                │
│ - Provides base importance scores (0-1)                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Association Rule Models Layer (A1, A2, A3)                 │
│ - Loads 3 pre-trained models from CSVs                      │
│ - Queries rules for each missing skill                      │
│ - Returns confidence scores and lift values                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Personalized Ranking Layer                                 │
│ - Combines gap importance + model scores                    │
│ - Creates ranked list of missing skills                     │
│ - Groups into phases (Foundation → Expert)                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ UI Display Layer                                            │
│ - Shows phases with skills and explanations                │
│ - Displays model sources and confidence scores             │
│ - Graceful fallback if models unavailable                  │
└─────────────────────────────────────────────────────────────┘
```

## Core Functions

### 1. `prioritize_missing_skills_with_models()`

**Purpose**: Rank missing skills using gap analysis + association rules

**Location**: `src/models/personalized_path.py`

**Function Signature**:

```python
def prioritize_missing_skills_with_models(
    missing_skills: List[str],
    user_skills: List[str],
    target_job_skills: List[str],
    gap_scores: Dict[str, float],
    ensemble: AssociationEnsemble,
    weight_importance: float = 0.5,
    weight_model: float = 0.5,
) -> List[SkillRecommendation]
```

**Returns**: List of `SkillRecommendation` objects (one per missing skill), sorted by `final_score`

**Key Fields**:

- `skill`: Skill name
- `base_importance`: Gap-based importance (0-1)
- `model_score`: Association rules signal (0-1)
- `final_score`: Combined score (0-1) = `weight_importance * base + weight_model * model`
- `sources`: Which models (A1, A2, A3) recommended this skill
- `confidence`: Average confidence from matching rules
- `lift`: Average lift from matching rules
- `explanation`: Human-readable reason

**How It Works**:

1. For each missing skill, queries AssociationEnsemble
2. Finds all rules where user's current skills are in antecedents
3. Collects confidence scores where target skill is in consequents
4. Combines with gap importance using weighted average
5. Sorts by final_score descending

**Example**:

```python
from src.models.personalized_path import prioritize_missing_skills_with_models
from src.models.association_miner import get_association_rules_from_csv
from src.models.skill_matcher import SkillMatcher

# Load models
ensemble = get_association_rules_from_csv('data/processed')
matcher = SkillMatcher()

# Run gap analysis
gap_result = matcher.analyze_gap(['python', 'sql'], ['python', 'sql', 'spark', 'ml', 'aws'])
missing_skills = gap_result['missing']
gap_scores = gap_result['gap_priority']

# Rank with models
recommendations = prioritize_missing_skills_with_models(
    missing_skills=missing_skills,
    user_skills=['python', 'sql'],
    target_job_skills=['python', 'sql', 'spark', 'ml', 'aws'],
    gap_scores=gap_scores,
    ensemble=ensemble,
    weight_importance=0.5,
    weight_model=0.5,
)

# Print ranked skills
for rec in recommendations:
    print(f"{rec.skill}: {rec.final_score:.2%} (base: {rec.base_importance:.0%}, model: {rec.model_score:.0%})")
    print(f"  Sources: {', '.join(rec.sources)}")
    print(f"  {rec.explanation}\n")
```

### 2. `build_personalized_learning_path()`

**Purpose**: Create complete learning path with phases, durations, and explanations

**Location**: `src/models/personalized_path.py`

**Function Signature**:

```python
def build_personalized_learning_path(
    user_skills: List[str],
    target_job_skills: List[str],
    ensemble: AssociationEnsemble,
    gap_analyzer: SkillMatcher,
    max_phases: int = 5,
    skills_per_phase: int = 3,
    weight_importance: float = 0.5,
    weight_model: float = 0.5,
) -> Dict[str, Any]
```

**Returns**: Dict with structure:

```python
{
    'phases': [
        {
            'phase_number': 1,
            'title': '🎯 Foundation Skills',
            'skills': [
                {
                    'name': 'Sql',
                    'score': 0.87,
                    'importance': 0.8,
                    'model_score': 0.9,
                    'sources': ['A1', 'A3'],
                    'confidence': 0.78,
                    'lift': 1.4,
                    'explanation': '...'
                },
                # ... more skills
            ],
            'duration_weeks': 4,
            'difficulty': 'Easy'
        },
        # ... more phases
    ],
    'total_weeks': 20,
    'summary': '...',
    'model_coverage': 0.85,  # % of skills with model signals
    'ranking_algorithm': 'Association Rules + Gap Analysis'
}
```

**How It Works**:

1. Runs SkillMatcher gap analysis
2. Calls prioritize_missing_skills_with_models() to rank
3. Groups ranked skills into phases by score (high → low)
4. Assigns difficulty levels and duration estimates
5. Creates explanations with model sources

**Example**:

```python
from src.models.personalized_path import build_personalized_learning_path
from src.models.association_miner import get_association_rules_from_csv
from src.models.skill_matcher import SkillMatcher

# Load models
ensemble = get_association_rules_from_csv('data/processed')
matcher = SkillMatcher()

# Build path
path = build_personalized_learning_path(
    user_skills=['python', 'pandas'],
    target_job_skills=['python', 'sql', 'spark', 'ml', 'aws'],
    ensemble=ensemble,
    gap_analyzer=matcher,
    max_phases=4,
)

# Display
print(f"Summary: {path['summary']}")
print(f"Total Duration: {path['total_weeks']} weeks")
print(f"Model Coverage: {path['model_coverage']:.0%}\n")

for phase in path['phases']:
    print(f"{phase['title']} ({phase['difficulty']}, {phase['duration_weeks']} weeks)")
    for skill in phase['skills']:
        print(f"  • {skill['name']}: {skill['score']:.0%} (model: {skill['model_score']:.0%})")
    print()
```

### 3. `AssociationEnsemble.get_skill_model_scores()`

**Purpose**: Get detailed model scores for specific skills (for advanced integration)

**Location**: `src/models/association_miner.py`

**Function Signature**:

```python
def get_skill_model_scores(
    self,
    user_skills: List[str],
    target_skills: List[str]
) -> Dict[str, Dict[str, Any]]
```

**Returns**: Dict mapping skill name to model signals:

```python
{
    'spark': {
        'model_scores': {
            'A1': {'confidence': 0.75, 'lift': 1.2, 'rule_count': 5},
            'A3': {'confidence': 0.82, 'lift': 1.3, 'rule_count': 8},
        },
        'best_confidence': 0.82,
        'best_model': 'A3',
        'total_signals': 13,
    },
    # ... more skills
}
```

**When to Use**: When you need raw model signals without gap analysis weighting

## Streamlit App Integration

### Complete Example: Replace Learning Path Section

Replace the old learning path section in `app/main.py` with:

```python
# ============================================================================
# SECTION 3: PERSONALIZED LEARNING PATH (NEW - Model-Driven)
# ============================================================================

if st.checkbox("📚 **View Personalized Learning Path** (Powered by Association Rules)", value=False):
    st.markdown("---")

    # Load models and gap analyzer
    try:
        from src.models.personalized_path import build_personalized_learning_path
        from src.models.association_miner import get_association_rules_from_csv
        from src.models.skill_matcher import SkillMatcher

        # Initialize
        ensemble = get_association_rules_from_csv('data/processed')
        matcher = SkillMatcher()

        # Build path
        path = build_personalized_learning_path(
            user_skills=user_skills,
            target_job_skills=job_skills,
            ensemble=ensemble,
            gap_analyzer=matcher,
            max_phases=4,
            weight_importance=0.5,
            weight_model=0.5,
        )

        # Display summary
        st.info(f"**Learning Path Summary**: {path['summary']}")
        st.metric("Model Coverage", f"{path['model_coverage']:.0%} of skills recommended by association rules")

        # Display phases
        if path['phases']:
            for phase in path['phases']:
                with st.expander(
                    f"**{phase['title']}** ({phase['difficulty']}) — {phase['duration_weeks']} weeks",
                    expanded=(phase['phase_number'] == 1)
                ):
                    # Create skills table
                    skills_data = []
                    for skill in phase['skills']:
                        skills_data.append({
                            'Skill': skill['name'].title(),
                            'Score': f"{skill['score']:.0%}",
                            'Importance': f"{skill['importance']:.0%}",
                            'Model Signal': f"{skill['model_score']:.0%}",
                            'Confidence': f"{skill['confidence']:.0%}" if skill['confidence'] > 0 else "—",
                            'Sources': ', '.join(skill['sources']) if skill['sources'] else "Gap-only",
                        })

                    skills_df = pd.DataFrame(skills_data)
                    st.table(skills_df)

                    # Show explanations
                    st.markdown("**Why these skills?**")
                    for skill in phase['skills']:
                        st.caption(f"• **{skill['name'].title()}**: {skill['explanation']}")
        else:
            st.success("✅ You already have all required skills for this job!")

    except Exception as e:
        st.error(f"❌ Error generating learning path: {str(e)}")
        st.info("Make sure association rule CSV files are in `data/processed/` directory")
```

### Key Features

1. **Model-Driven Ranking**: Each skill shows:

   - Final score (gap + model weighted)
   - Base importance (from gap analysis)
   - Model signal strength (from association rules)
   - Which models recommended it (A1/A2/A3)

2. **Human-Readable Explanations**: Each skill includes:

   - Why it's important (job requirement)
   - Model signals (confidence, lift, sources)
   - Which association rule models found it

3. **Phased Learning**: Skills grouped by difficulty:

   - Phase 1: Foundation (easiest, most fundamental)
   - Phase 2: Core competencies
   - Phase 3: Intermediate
   - Phase 4: Advanced
   - Phase 5: Expert (hardest, most specialized)

4. **Duration Estimates**: Each phase shows estimated weeks (~1.5 weeks per skill)

5. **Graceful Fallback**: If models unavailable, falls back to gap-only importance ordering

## Customization

### Adjust Model vs Gap Importance Weight

Control how much association rules influence ranking:

```python
# More weight on association rules (80% model, 20% gap)
path = build_personalized_learning_path(
    ...,
    weight_importance=0.2,  # Gap importance
    weight_model=0.8,        # Association rules
)
```

### Change Number of Phases

```python
# Create 6 phases instead of 4
path = build_personalized_learning_path(
    ...,
    max_phases=6,
)
```

### Adjust Skills Per Phase

```python
# Manually control grouping
# This groups skills by their score difference
path = build_personalized_learning_path(
    ...,
    skills_per_phase=5,  # Larger phases
)
```

## Data Flow Diagram

```
User Input (Skills)
    │
    ├─→ Gap Analysis (SkillMatcher)
    │   └─→ missing_skills, gap_scores
    │
    ├─→ Association Rules (AssociationEnsemble)
    │   ├─→ Query A1 (Skills model, 308 rules)
    │   ├─→ Query A2 (Categories model, 22 rules)
    │   └─→ Query A3 (Combined model, 7,147 rules)
    │
    ├─→ Ranking Function (prioritize_missing_skills_with_models)
    │   ├─→ Combine: base_importance + model_score
    │   ├─→ For each missing skill:
    │   │   └─→ final_score = 0.5 * base + 0.5 * model
    │   └─→ Return: Ranked list [SkillRecommendation, ...]
    │
    ├─→ Grouping Function (build_personalized_learning_path)
    │   ├─→ Group ranked skills into phases
    │   ├─→ Assign difficulty and duration
    │   └─→ Build explanations
    │
    └─→ Streamlit Display
        └─→ Show phases with skills, scores, and model sources
```

## Testing the Integration

### Quick Test

```python
# test_learning_path.py
from src.models.personalized_path import build_personalized_learning_path
from src.models.association_miner import get_association_rules_from_csv
from src.models.skill_matcher import SkillMatcher

# Test data
user_skills = ['python', 'sql', 'data analysis']
target_job_skills = ['python', 'sql', 'machine learning', 'spark', 'aws', 'docker']

# Load models
ensemble = get_association_rules_from_csv('data/processed')
matcher = SkillMatcher()

# Build path
path = build_personalized_learning_path(
    user_skills=user_skills,
    target_job_skills=target_job_skills,
    ensemble=ensemble,
    gap_analyzer=matcher,
)

# Verify results
assert len(path['phases']) > 0, "Should have at least one phase"
assert path['total_weeks'] > 0, "Should have duration estimate"
assert path['model_coverage'] > 0, "Should have model signals"

print("✅ Learning path test passed!")
for phase in path['phases']:
    print(f"{phase['title']}: {len(phase['skills'])} skills")
```

## Edge Cases Handled

1. **User already has all skills**: Returns empty phases with success message
2. **No models loaded**: Falls back to gap-based ordering
3. **Model CSV files missing**: Graceful error message in Streamlit
4. **Malformed rule data**: Safely skipped with debug logging
5. **No matching rules for a skill**: Shows gap-only importance in explanation
6. **Empty user/job skill lists**: Returns empty path with error message

## Performance Considerations

- **Gap Analysis**: ~50ms (fast)
- **Model Queries**: ~200-500ms (depends on CSV file size)
- **Ranking**: ~100ms (linear in number of missing skills)
- **Total**: ~500ms-1s for complete path generation

For 50+ skills, consider caching results or lazy-loading models.

## Future Enhancements

1. **User Preference Weighting**: Allow users to adjust importance vs model weight
2. **Skill Difficulty Estimation**: Use model lift as difficulty proxy
3. **Prerequisite Chains**: Order phases to respect skill dependencies
4. **Learning Time Estimation**: Use job market data to estimate actual weeks needed
5. **Resource Recommendations**: Show courses/certifications for each skill
6. **Progress Tracking**: Allow users to mark skills as learned
