"""Skill-based filtering for similar job recommendations.

This module provides helper functions to filter similar jobs based on skill overlap
and dominant skill categories, ensuring high-quality recommendations for the Streamlit app.
"""

import pandas as pd
from typing import List, Tuple, Optional, Set


def get_skill_overlap(skills_a: List[str], skills_b: List[str]) -> Tuple[int, Set[str]]:
    """Compute skill overlap between two job skill lists.
    
    Args:
        skills_a: First job's skill list
        skills_b: Second job's skill list
    
    Returns:
        Tuple of (overlap_count, overlapping_skills_set)
    """
    set_a = set(skills_a) if skills_a else set()
    set_b = set(skills_b) if skills_b else set()
    overlap = set_a & set_b
    return len(overlap), overlap


def get_top_skills(skill_list: List[str], n_top: int = 5) -> List[str]:
    """Get top N skills from a skill list.
    
    Args:
        skill_list: List of skills (assumed already in priority order)
        n_top: Number of top skills to extract
    
    Returns:
        List of top N skills
    """
    return skill_list[:n_top] if skill_list else []


def extract_main_category(skill_categories_str: str) -> str:
    """Extract primary skill category from concatenated category string.
    
    Args:
        skill_categories_str: Skill categories as comma-separated string (e.g., "it,programming,software")
    
    Returns:
        Primary skill category or 'other' if not available
    """
    if not skill_categories_str or pd.isna(skill_categories_str):
        return 'other'
    
    categories = str(skill_categories_str).split(',')
    return categories[0].strip() if categories else 'other'


def have_matching_category(cat_a: str, cat_b: str) -> bool:
    """Check if two skill categories match (same primary category).
    
    Args:
        cat_a: First job's primary skill category
        cat_b: Second job's primary skill category
    
    Returns:
        True if categories match
    """
    return cat_a == cat_b and cat_a != 'other'


def filter_by_skill_overlap(
    target_job_id: str,
    target_skills: List[str],
    cluster_candidates: pd.DataFrame,
    min_overlap: int = 1
) -> Tuple[pd.DataFrame, str]:
    """Filter candidate jobs by skill overlap with target job.
    
    Args:
        target_job_id: ID of the target job
        target_skills: Skills of the target job
        cluster_candidates: DataFrame with candidate jobs (must have 'job_id' and 'skill_list' columns)
        min_overlap: Minimum number of overlapping skills required
    
    Returns:
        Tuple of (filtered_DataFrame, match_quality) where match_quality is 'high_quality' or 'loose_match'
    """
    filtered = []
    target_skills_set = set(target_skills) if target_skills else set()
    
    for _, candidate in cluster_candidates.iterrows():
        # Skip the target job itself
        if candidate['job_id'] == target_job_id:
            continue
        
        candidate_skills = candidate.get('skill_list', [])
        if not candidate_skills:
            continue
        
        # Compute overlap
        overlap, _ = get_skill_overlap(target_skills, candidate_skills)
        
        if overlap >= min_overlap:
            filtered.append(candidate)
    
    if filtered:
        return pd.DataFrame(filtered), 'high_quality'
    else:
        # Fallback: return unfiltered cluster (without target), marked as loose match
        unfiltered = cluster_candidates[cluster_candidates['job_id'] != target_job_id]
        return unfiltered, 'loose_match'


def filter_by_category(
    target_category: str,
    cluster_candidates: pd.DataFrame
) -> Tuple[pd.DataFrame, str]:
    """Filter candidate jobs by matching skill category.
    
    Args:
        target_category: Primary skill category of target job
        cluster_candidates: DataFrame with candidate jobs (must have 'skill_categories' column)
    
    Returns:
        Tuple of (filtered_DataFrame, match_quality)
    """
    if not target_category or target_category == 'other':
        return cluster_candidates, 'loose_match'
    
    def get_primary_cat(cat_str):
        if not cat_str or pd.isna(cat_str):
            return 'other'
        cats = str(cat_str).split(',')
        return cats[0].strip() if cats else 'other'
    
    cluster_candidates['primary_cat'] = cluster_candidates['skill_categories'].apply(get_primary_cat)
    
    # Filter by matching category (excluding target job)
    filtered = cluster_candidates[
        (cluster_candidates['primary_cat'] == target_category) &
        (cluster_candidates['job_id'] != cluster_candidates['job_id'].iloc[0])
    ]
    
    if not filtered.empty:
        return filtered.drop('primary_cat', axis=1), 'category_match'
    else:
        return cluster_candidates.drop('primary_cat', axis=1), 'loose_match'


def get_similar_jobs_with_filtering(
    target_job_id: str,
    target_skills: List[str],
    target_category: str,
    cluster_candidates: pd.DataFrame,
    top_n: int = 8,
    min_skill_overlap: int = 1
) -> Tuple[pd.DataFrame, str]:
    """Get similar jobs using multi-level filtering strategy.
    
    Filtering order:
    1. Same cluster (already applied before calling this)
    2. Same skill category OR >= min_skill_overlap skills
    3. Fallback to unfiltered cluster if no results
    
    Args:
        target_job_id: ID of the target job
        target_skills: Skills of the target job
        target_category: Primary skill category of target job
        cluster_candidates: DataFrame with candidate jobs in same cluster
        top_n: Number of similar jobs to return
        min_skill_overlap: Minimum overlapping skills for match
    
    Returns:
        Tuple of (similar_jobs_DataFrame, match_quality)
        match_quality: 'high_quality', 'category_match', or 'loose_match'
    """
    # Try skill overlap filter first
    filtered_by_skill, quality = filter_by_skill_overlap(
        target_job_id,
        target_skills,
        cluster_candidates,
        min_overlap=min_skill_overlap
    )
    
    if not filtered_by_skill.empty and quality == 'high_quality':
        return filtered_by_skill.head(top_n), 'high_quality'
    
    # Try category filter if skill filter failed
    if target_category != 'other':
        filtered_by_cat, cat_quality = filter_by_category(
            target_category,
            cluster_candidates
        )
        if not filtered_by_cat.empty and cat_quality == 'category_match':
            return filtered_by_cat.head(top_n), 'category_match'
    
    # Fallback to unfiltered cluster
    fallback = cluster_candidates[cluster_candidates['job_id'] != target_job_id]
    return fallback.head(top_n), 'loose_match'
