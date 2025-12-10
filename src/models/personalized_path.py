"""Personalized Learning Path with Association Rule Integration

This module builds personalized learning paths that combine:
1. Gap analysis (what skills are missing)
2. Association rule models (which skills are frequently learned together)
3. Skill importance (from job requirements)

Result: A ranked, phased learning plan driven by ML models + gap analysis.
"""

import pandas as pd
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillRecommendation:
    """Single skill recommendation with model signals."""
    skill: str
    base_importance: float  # From gap analysis (0-1)
    model_score: float      # From association rules (0-1)
    final_score: float      # Combined score (0-1)
    sources: List[str]      # Which models recommended this ["A1", "A2", "A3"]
    confidence: float       # Average confidence from rules
    lift: float             # Average lift from rules
    explanation: str        # Human-readable reason


def prioritize_missing_skills_with_models(
    missing_skills: List[str],
    user_skills: List[str],
    target_job_skills: List[str],
    gap_scores: Dict[str, float],
    ensemble: 'AssociationEnsemble',
    weight_importance: float = 0.5,
    weight_model: float = 0.5,
) -> List[SkillRecommendation]:
    """
    Rank missing skills using BOTH gap analysis and association rule models.
    
    This is the core function that combines:
    - base_importance: How critical is this skill for the target job?
    - model_score: How often does this skill appear in association rules for user's current skills?
    
    Args:
        missing_skills: Skills needed for job but user doesn't have
        user_skills: Skills user currently has
        target_job_skills: Skills required for target job
        gap_scores: Dict mapping skill -> importance score from SkillMatcher
        ensemble: AssociationEnsemble with loaded A1/A2/A3 models
        weight_importance: Weight for gap-based importance (0-1)
        weight_model: Weight for model-based recommendations (0-1)
        
    Returns:
        List of SkillRecommendation sorted by final_score (highest first)
        
    Example:
        >>> recommendations = prioritize_missing_skills_with_models(
        ...     missing_skills=['sql', 'spark', 'machine learning'],
        ...     user_skills=['python', 'pandas'],
        ...     target_job_skills=['python', 'sql', 'spark', 'ml', 'aws'],
        ...     gap_scores={'sql': 0.8, 'spark': 0.7, 'machine learning': 0.9},
        ...     ensemble=ensemble,
        ... )
        >>> for rec in recommendations:
        ...     print(f"{rec.skill}: {rec.final_score:.2%} (sources: {rec.sources})")
    """
    
    recommendations = []
    user_skills_set = set(s.lower().strip() for s in user_skills if s)
    target_skills_set = set(s.lower().strip() for s in target_job_skills if s)
    missing_set = set(s.lower().strip() for s in missing_skills if s)
    
    # For each missing skill, compute model score
    for skill in missing_set:
        # 1. BASE IMPORTANCE from gap analysis
        base_importance = gap_scores.get(skill, 0.5)
        
        # 2. MODEL SCORE from association rules
        # Query all models to see if this skill is recommended
        model_scores = []
        model_sources = []
        confidence_scores = []
        lift_scores = []
        
        # Query each model in the ensemble
        for model_entry in ensemble.models:
            model_name = model_entry.get('name', 'unknown')
            miner = model_entry.get('miner')
            
            if miner is None or miner.rules is None or len(miner.rules) == 0:
                continue
            
            try:
                # Find rules where:
                # - antecedents overlap with user_skills
                # - consequents include this skill
                for idx, rule in miner.rules.iterrows():
                    try:
                        # Parse antecedents/consequents
                        ants = _parse_itemset(rule.get('antecedents'))
                        cons = _parse_itemset(rule.get('consequents'))
                        
                        # Check if user has some antecedents AND skill is a consequent
                        if ants and cons and (ants & user_skills_set) and (skill in cons):
                            conf = float(rule.get('confidence', 0.0))
                            lift = float(rule.get('lift', 1.0))
                            
                            model_scores.append(conf)
                            confidence_scores.append(conf)
                            lift_scores.append(lift)
                            model_sources.append(model_name)
                    except Exception as e:
                        logger.debug(f"Error processing rule for {skill}: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Error querying model {model_name} for {skill}: {e}")
                continue
        
        # Aggregate model scores
        if model_scores:
            # Average confidence across all matching rules
            model_score = max(model_scores)  # Take highest confidence
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            avg_lift = sum(lift_scores) / len(lift_scores)
        else:
            # No model signals - fall back to pure gap importance
            model_score = 0.0
            avg_confidence = 0.0
            avg_lift = 0.0
        
        # 3. COMBINE SCORES
        # If no model signals, rely entirely on gap importance
        if model_score == 0.0:
            final_score = base_importance
        else:
            # Weighted average: importance + model signal
            final_score = (weight_importance * base_importance + 
                          weight_model * model_score)
        
        # 4. BUILD EXPLANATION
        if model_scores:
            sources_str = ", ".join(set(model_sources))
            explanation = (
                f"Job requires this skill (importance: {base_importance:.0%}). "
                f"Association rules show it frequently appears with your skills "
                f"(confidence: {avg_confidence:.0%}, lift: {avg_lift:.1f}x). "
                f"Recommended by: {sources_str}."
            )
        else:
            explanation = (
                f"Job requires this skill (importance: {base_importance:.0%}). "
                f"No association rule signals available for this skill. "
                f"Showing gap-based priority."
            )
        
        rec = SkillRecommendation(
            skill=skill,
            base_importance=base_importance,
            model_score=model_score,
            final_score=final_score,
            sources=list(set(model_sources)) if model_sources else [],
            confidence=avg_confidence if model_scores else 0.0,
            lift=avg_lift if model_scores else 0.0,
            explanation=explanation,
        )
        recommendations.append(rec)
    
    # Sort by final_score (highest first)
    recommendations.sort(key=lambda x: x.final_score, reverse=True)
    return recommendations


def build_personalized_learning_path(
    user_skills: List[str],
    target_job_skills: List[str],
    ensemble: 'AssociationEnsemble',
    gap_analyzer: 'SkillMatcher',
    max_phases: int = 5,
    skills_per_phase: int = 3,
    weight_importance: float = 0.5,
    weight_model: float = 0.5,
) -> Dict[str, Any]:
    """
    Build a complete personalized learning path using association rules + gap analysis.
    
    This is the main entry point. It:
    1. Runs gap analysis to identify missing skills
    2. Scores missing skills using both gap importance and model signals
    3. Groups skills into phases (Foundation → Advanced)
    4. Attaches explanations from association rules
    
    Args:
        user_skills: Skills user currently has
        target_job_skills: Skills required for target job
        ensemble: AssociationEnsemble with loaded A1/A2/A3 models
        gap_analyzer: SkillMatcher instance for gap analysis
        max_phases: Maximum number of learning phases to create
        skills_per_phase: Approximate skills per phase
        weight_importance: Weight for gap importance in scoring
        weight_model: Weight for model signals in scoring
        
    Returns:
        Dict with structure:
        {
            "phases": [
                {
                    "phase_number": 1,
                    "title": "Foundation Skills",
                    "skills": [
                        {
                            "name": "sql",
                            "score": 0.87,
                            "importance": 0.8,
                            "model_score": 0.9,
                            "sources": ["A1", "A3"],
                            "confidence": 0.78,
                            "lift": 1.4,
                            "explanation": "..."
                        },
                        ...
                    ],
                    "duration_weeks": 4,
                    "difficulty": "Easy"
                },
                ...
            ],
            "total_weeks": 20,
            "summary": "...",
            "model_coverage": 0.85,  # % of skills with model signals
        }
        
    Example:
        >>> path = build_personalized_learning_path(
        ...     user_skills=['python', 'basic sql'],
        ...     target_job_skills=['python', 'sql', 'spark', 'ml', 'aws'],
        ...     ensemble=ensemble,
        ...     gap_analyzer=gap_analyzer,
        ... )
        >>> for phase in path['phases']:
        ...     print(f"{phase['title']}: {len(phase['skills'])} skills, {phase['duration_weeks']} weeks")
    """
    
    try:
        # 1. RUN GAP ANALYSIS
        gap_result = gap_analyzer.analyze_gap(user_skills, target_job_skills)
        missing_skills = gap_result.get('missing', [])
        gap_scores = gap_result.get('gap_priority', {})
        
        if not missing_skills:
            return {
                "phases": [],
                "total_weeks": 0,
                "summary": "You already have all required skills for this job! 🎉",
                "model_coverage": 1.0,
            }
        
        # 2. SCORE MISSING SKILLS with models + gap analysis
        ranked_skills = prioritize_missing_skills_with_models(
            missing_skills=missing_skills,
            user_skills=user_skills,
            target_job_skills=target_job_skills,
            gap_scores=gap_scores,
            ensemble=ensemble,
            weight_importance=weight_importance,
            weight_model=weight_model,
        )
        
        # 3. GROUP INTO PHASES
        phases = _group_into_phases(
            ranked_skills,
            max_phases=max_phases,
            skills_per_phase=skills_per_phase,
        )
        
        # 4. CALCULATE METADATA
        total_weeks = sum(p['duration_weeks'] for p in phases)
        skills_with_model_signals = sum(1 for r in ranked_skills if r.sources)
        model_coverage = (
            skills_with_model_signals / len(ranked_skills) 
            if ranked_skills else 0.0
        )
        
        summary = (
            f"Personalized learning path: {len(ranked_skills)} missing skills "
            f"organized into {len(phases)} phases (~{total_weeks} weeks). "
            f"{model_coverage:.0%} of skills recommended by association-rule models. "
            f"Focus on Foundation skills first, then advance to Expert level."
        )
        
        return {
            "phases": phases,
            "total_weeks": total_weeks,
            "summary": summary,
            "model_coverage": model_coverage,
            "ranking_algorithm": "Association Rules + Gap Analysis",
        }
    
    except Exception as e:
        logger.error(f"Error building personalized learning path: {e}")
        return {
            "phases": [],
            "total_weeks": 0,
            "summary": f"Error building learning path: {str(e)}",
            "model_coverage": 0.0,
        }


def _group_into_phases(
    ranked_skills: List[SkillRecommendation],
    max_phases: int = 5,
    skills_per_phase: int = 3,
) -> List[Dict[str, Any]]:
    """
    Group ranked skills into learning phases with metadata.
    
    Phases:
    - Phase 1 (Foundation): Easiest, most fundamental skills
    - Phase 2-4 (Intermediate): Progressive difficulty
    - Phase 5 (Advanced): Hardest, most specialized skills
    """
    
    phase_titles = [
        "🎯 Foundation Skills",
        "📚 Core Competencies",
        "⚡ Intermediate Skills",
        "🚀 Advanced Techniques",
        "🏆 Expert Level",
    ]
    
    phase_difficulties = [
        "Easy",
        "Easy-Medium",
        "Medium",
        "Medium-Hard",
        "Hard",
    ]
    
    duration_per_skill = 1.5  # weeks
    
    phases = []
    skills_per_phase_actual = max(
        1, 
        len(ranked_skills) // max_phases
    )
    
    for phase_idx in range(min(max_phases, max(1, len(ranked_skills)))):
        start_idx = phase_idx * skills_per_phase_actual
        end_idx = (
            (phase_idx + 1) * skills_per_phase_actual 
            if phase_idx < max_phases - 1 
            else len(ranked_skills)
        )
        
        phase_skills = ranked_skills[start_idx:end_idx]
        
        if not phase_skills:
            continue
        
        skills_data = [
            {
                "name": rec.skill.title(),
                "score": rec.final_score,
                "importance": rec.base_importance,
                "model_score": rec.model_score,
                "sources": rec.sources,
                "confidence": rec.confidence,
                "lift": rec.lift,
                "explanation": rec.explanation,
            }
            for rec in phase_skills
        ]
        
        phase = {
            "phase_number": phase_idx + 1,
            "title": phase_titles[phase_idx] if phase_idx < len(phase_titles) else f"Phase {phase_idx + 1}",
            "skills": skills_data,
            "duration_weeks": int(len(phase_skills) * duration_per_skill),
            "difficulty": phase_difficulties[phase_idx] if phase_idx < len(phase_difficulties) else "Hard",
        }
        
        phases.append(phase)
    
    return phases


def _parse_itemset(itemset_str: Any) -> set:
    """
    Parse antecedents/consequents from various formats.
    Handles: frozenset strings, sets, lists, etc.
    """
    if not itemset_str or (isinstance(itemset_str, float) and pd.isna(itemset_str)):
        return set()
    
    if isinstance(itemset_str, (set, frozenset)):
        return set(str(x).lower().strip() for x in itemset_str if x)
    
    itemset_str = str(itemset_str).strip()
    
    # Try literal_eval first
    try:
        parsed = ast.literal_eval(itemset_str)
        if isinstance(parsed, (set, frozenset, list, tuple)):
            return set(str(x).lower().strip() for x in parsed if x)
    except Exception:
        pass
    
    # Try frozenset() extraction
    if itemset_str.startswith('frozenset('):
        try:
            inner = itemset_str[10:-1]  # Remove 'frozenset(' and ')'
            parsed = ast.literal_eval(inner)
            if isinstance(parsed, (set, frozenset, list, tuple, dict)):
                return set(str(x).lower().strip() for x in parsed if x)
        except Exception:
            pass
    
    # Fallback: split by comma
    return set(
        x.strip().lower() 
        for x in itemset_str.split(',') 
        if x.strip()
    )
