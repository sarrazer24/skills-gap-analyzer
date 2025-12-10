"""
Learning Path Generator - Smart Learning Recommendations

Uses association rules to create optimal learning paths with prerequisites.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict, deque


class LearningPathGenerator:
    """
    Generate smart learning paths using association rules.
    
    Features:
    - Respects prerequisites based on rules
    - Suggests optimal learning order
    - Provides time estimates
    - Identifies common learning patterns
    """
    
    def __init__(self, rules_df: Optional[pd.DataFrame] = None):
        """
        Initialize generator with optional rules.
        
        Args:
            rules_df: Association rules DataFrame (from data/processed/)
        """
        self.rules_df = rules_df if rules_df is not None else pd.DataFrame()
        self._prerequisite_cache = {}
    
    def generate_learning_path(
        self,
        target_skills: List[str],
        user_current_skills: List[str] = None,
        max_skills_per_phase: int = 3
    ) -> Dict:
        """
        Generate a complete learning roadmap.
        
        Args:
            target_skills: Skills user needs to learn
            user_current_skills: User's current skills (used for prerequisites)
            max_skills_per_phase: Max skills to learn in each phase
            
        Returns:
            Dict with learning phases, timeline, and metrics
        """
        if not target_skills:
            return {
                'phases': [],
                'total_weeks': 0,
                'total_skills': 0,
                'prerequisites': {}
            }
        
        current = set(s.lower().strip() for s in (user_current_skills or []) if s)
        target = set(s.lower().strip() for s in target_skills if s)
        
        # Build prerequisite graph
        prerequisites = self._build_prerequisite_graph(target)
        
        # Generate phases
        phases = []
        learned = current.copy()
        remaining = target - current
        
        while remaining:
            # Find skills that have all prerequisites met
            ready_skills = [
                skill for skill in remaining
                if all(prereq in learned for prereq in prerequisites.get(skill, []))
            ]
            
            if not ready_skills:
                # No prerequisites satisfied, just take next skills
                ready_skills = sorted(list(remaining))[:max_skills_per_phase]
            else:
                # Take up to max_skills_per_phase
                ready_skills = sorted(ready_skills)[:max_skills_per_phase]
            
            if not ready_skills:
                break
            
            phase = self._create_phase(ready_skills, learned, prerequisites)
            phases.append(phase)
            
            learned.update(ready_skills)
            remaining -= set(ready_skills)
        
        return {
            'phases': phases,
            'total_weeks': sum(p['weeks'] for p in phases),
            'total_skills': len(target),
            'prerequisites': prerequisites,
            'phase_count': len(phases)
        }
    
    def suggest_learning_sequence(
        self,
        skills: List[str]
    ) -> List[str]:
        """
        Suggest optimal order to learn a set of skills.
        
        Uses association rules to identify common learning sequences.
        
        Args:
            skills: Skills to order
            
        Returns:
            List of skills in recommended learning order
        """
        if not skills:
            return []
        
        skills_set = set(s.lower().strip() for s in skills if s)
        
        # Build graph of "what teaches what"
        graph = defaultdict(list)
        
        if not self.rules_df.empty:
            for idx, row in self.rules_df.iterrows():
                try:
                    antecedents = self._parse_frozenset(row.get('antecedents', ''))
                    consequents = self._parse_frozenset(row.get('consequents', ''))
                    confidence = float(row.get('confidence', 0))
                    
                    # High confidence rules indicate strong learning paths
                    if confidence > 0.6:
                        for ant in antecedents:
                            if ant in skills_set:
                                for cons in consequents:
                                    if cons in skills_set and ant != cons:
                                        graph[ant].append(cons)
                except:
                    pass
        
        # Topological sort
        return self._topological_sort(graph, skills_set)
    
    def identify_skill_clusters(
        self,
        skills: List[str]
    ) -> Dict[str, List[str]]:
        """
        Identify clusters of related skills using association rules.
        
        Skills in same cluster should be learned together.
        
        Args:
            skills: List of skills to cluster
            
        Returns:
            Dict mapping cluster name to skills in that cluster
        """
        clusters = defaultdict(list)
        
        if not self.rules_df.empty:
            for skill in skills:
                skill_lower = skill.lower().strip()
                cluster_id = 0
                
                # Find rules mentioning this skill
                for idx, row in self.rules_df.iterrows():
                    try:
                        antecedents = self._parse_frozenset(row.get('antecedents', ''))
                        consequents = self._parse_frozenset(row.get('consequents', ''))
                        
                        if skill_lower in antecedents or skill_lower in consequents:
                            related = (set(antecedents) | set(consequents)) - {skill_lower}
                            related_in_input = related & set(s.lower().strip() for s in skills)
                            
                            if related_in_input:
                                cluster_id = id(frozenset(antecedents | consequents))
                                clusters[f"cluster_{cluster_id}"].append(skill_lower)
                    except:
                        pass
        
        # If no clusters found, return skills grouped by first letter
        if not clusters:
            for skill in skills:
                skill_lower = skill.lower().strip()
                cluster = f"cluster_{skill_lower[0].upper()}"
                clusters[cluster].append(skill_lower)
        
        return {k: sorted(list(set(v))) for k, v in clusters.items()}
    
    def estimate_learning_time(
        self,
        skills: List[str]
    ) -> Tuple[int, Dict[str, int]]:
        """
        Estimate total learning time for a set of skills.
        
        Args:
            skills: Skills to learn
            
        Returns:
            Tuple of (total_weeks, dict_of_individual_weeks)
        """
        skill_times = {}
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            
            # Base estimates
            if any(hard in skill_lower for hard in ['machine learning', 'kubernetes', 'hadoop', 'spark']):
                weeks = 12
            elif any(med in skill_lower for med in ['aws', 'docker', 'react', 'angular', 'django']):
                weeks = 6
            else:
                weeks = 3
            
            skill_times[skill_lower] = weeks
        
        total_weeks = sum(skill_times.values())
        
        return total_weeks, skill_times
    
    def enrich_learning_path_with_associations(
        self,
        learning_path: Dict,
        user_current_skills: List[str] = None
    ) -> Dict:
        """
        Enrich a learning path with association rule explanations.
        
        For each skill in the learning path, add explanations of which rules
        suggest learning this skill (e.g., "recommended because users with
        Python and SQL often learn Spark").
        
        This makes the association rules used for recommendations explicit
        and justifiable to the user.
        
        Args:
            learning_path: Dict from generate_learning_path()
            user_current_skills: User's current skills (for context)
            
        Returns:
            Enhanced learning path with 'rule_explanations' for each phase
        
        Example:
            >>> path = generator.generate_learning_path(['spark', 'scala'])
            >>> enriched = generator.enrich_learning_path_with_associations(
            ...     path, user_current_skills=['python', 'sql']
            ... )
            >>> for phase in enriched['phases']:
            ...     for skill, explanation in phase.get('rule_explanations', {}).items():
            ...         print(f"  {skill}: {explanation}")
        """
        if 'phases' not in learning_path:
            return learning_path
        
        user_skills_set = set(
            s.lower().strip() for s in (user_current_skills or []) if s
        )
        
        # Enrich each phase
        for phase in learning_path.get('phases', []):
            phase['rule_explanations'] = {}
            
            for skill in phase.get('skills', []):
                skill_lower = skill.lower().strip()
                explanations = []
                
                if not self.rules_df.empty:
                    # Find rules where this skill is consequent and user skills are antecedents
                    for idx, row in self.rules_df.iterrows():
                        try:
                            antecedents = self._parse_frozenset(row.get('antecedents', ''))
                            consequents = self._parse_frozenset(row.get('consequents', ''))
                            confidence = float(row.get('confidence', 0))
                            lift = float(row.get('lift', 1.0))
                            
                            # Check if skill is in consequents
                            if not any(skill_lower in str(c).lower() for c in consequents):
                                continue
                            
                            # Check if any antecedent is in user skills or previously learned
                            matching_antecedents = [
                                a for a in antecedents
                                if a.lower().strip() in user_skills_set
                            ]
                            
                            if matching_antecedents and confidence > 0.3:
                                antec_str = ', '.join(matching_antecedents)
                                explanation = (
                                    f"Users with {antec_str} frequently need {skill} "
                                    f"(confidence: {confidence:.0%}, lift: {lift:.2f})"
                                )
                                explanations.append(explanation)
                        except:
                            pass
                
                # Use top explanation if available
                if explanations:
                    phase['rule_explanations'][skill] = explanations[0]
        
        return learning_path
    
    # ============= Helper Methods =============
    
    def _build_prerequisite_graph(self, target_skills: set) -> Dict[str, List[str]]:
        """Build prerequisite relationships from association rules."""
        prerequisites = defaultdict(list)
        
        if self.rules_df.empty:
            return dict(prerequisites)
        
        for skill in target_skills:
            skill_lower = skill.lower().strip()
            
            for idx, row in self.rules_df.iterrows():
                try:
                    antecedents = self._parse_frozenset(row.get('antecedents', ''))
                    consequents = self._parse_frozenset(row.get('consequents', ''))
                    confidence = float(row.get('confidence', 0))
                    
                    # If target skill is consequent, antecedents are prerequisites
                    if skill_lower in consequents and confidence > 0.5:
                        prerequisites[skill_lower].extend(antecedents)
                except:
                    pass
        
        # Remove duplicates and filter by target skills
        for skill in prerequisites:
            prerequisites[skill] = sorted(
                list(set(p for p in prerequisites[skill] if p in target_skills))
            )
        
        return dict(prerequisites)
    
    def _create_phase(
        self,
        skills: List[str],
        learned: set,
        prerequisites: Dict
    ) -> Dict:
        """Create a learning phase."""
        weeks, skill_times = self.estimate_learning_time(skills)
        
        phase_info = {
            'skills': sorted(skills),
            'weeks': weeks,
            'skill_breakdown': {skill: skill_times.get(skill.lower().strip(), 3) for skill in skills},
            'prerequisites_met': all(
                all(p in learned for p in prerequisites.get(s.lower().strip(), []))
                for s in skills
            )
        }
        
        return phase_info
    
    def _parse_frozenset(self, s) -> List[str]:
        """Parse frozenset string representation."""
        if pd.isna(s) or not s:
            return []
        
        s = str(s).strip()
        try:
            if s.startswith("frozenset("):
                s = s.replace("frozenset(", "").rstrip(")")
            
            import ast
            items = ast.literal_eval(s)
            return list(items) if isinstance(items, (set, frozenset)) else [items]
        except:
            return []
    
    def _topological_sort(
        self,
        graph: Dict[str, List[str]],
        skills: set
    ) -> List[str]:
        """Topological sort of skills based on prerequisites."""
        # Find in-degrees
        in_degree = {skill: 0 for skill in skills}
        
        for skill in skills:
            for neighbor in graph.get(skill, []):
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        # Start with skills with no prerequisites
        queue = deque([s for s in skills if in_degree[s] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph.get(current, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Add any remaining skills (cycles or isolated)
        result.extend([s for s in skills if s not in result])
        
        return result


# ============================================================================
# MODEL-DRIVEN LEARNING PATH GENERATION (NEW)
# ============================================================================

def build_personalized_learning_path(
    user_skills: List[str],
    job_skills: List[str],
    ensemble: Optional[object] = None,
    max_phases: int = 5,
) -> Dict[str, Any]:
    """
    Build a personalized learning path using gap analysis + association rule models.
    
    This function combines:
    1. Gap analysis to identify missing skills and base importance
    2. Association rule models (A1/A2/A3) to score skills based on what other people
       with similar skills commonly learn
    3. Phasing to organize skills into digestible learning phases
    
    Args:
        user_skills: List of skills the user currently has
        job_skills: List of skills required for the target job
        ensemble: Optional AssociationEnsemble instance (if None, uses gap-only approach)
        max_phases: Maximum number of learning phases to create (2-5 recommended)
    
    Returns:
        Dict with guaranteed structure (NEVER returns None):
        {
            "phases": [               # List of learning phases (may be empty)
                {
                    "phase_number": 1,
                    "title": "Foundation Skills",
                    "skills": [
                        {
                            "name": "skill_name",
                            "final_score": 0.85,        # Combined score (gap + model)
                            "base_importance": 0.80,    # Gap importance
                            "model_score": 0.90,        # Model confidence
                            "sources": ["A1", "A3"],    # Which models suggested it
                            "explanation": "..."        # Why this skill is recommended
                        },
                        ...
                    ],
                    "duration_weeks": 4,
                    "difficulty": "Easy"
                },
                ...
            ],
            "total_weeks": 20,                          # Sum of all phase durations
            "model_available": True,                    # Was ensemble provided?
            "missing_count": 5,                         # Number of missing skills
            "message": None                             # Optional message if phases empty
        }
    
    IMPORTANT: This function ALWAYS returns a valid dict. It never returns None.
    If skill scoring fails, it returns empty phases with a message.
    If there are no missing skills, it returns empty phases with a success message.
    """
    from src.models.skill_matcher import SkillMatcher
    
    # Step 1: Run gap analysis
    matcher = SkillMatcher(skill_to_category={})
    gap_result = matcher.analyze_gap(user_skills, job_skills)
    
    missing_skills = gap_result.get('missing', [])
    if not missing_skills:
        return {
            "phases": [],
            "total_weeks": 0.0,
            "model_available": ensemble is not None,
            "missing_count": 0,
            "message": "You already have all required skills! 🎉"
        }
    
    # Step 2: Score skills using models (if available) + gap analysis
    skill_scores = _score_missing_skills(
        missing_skills,
        user_skills,
        gap_result['skill_importance'],
        ensemble,
        job_skills
    )

    # Always build phases if we have skill_scores (which we should, since gap analysis provides base_importance)
    if not skill_scores or not isinstance(skill_scores, dict):
        return {
            "phases": [],
            "total_weeks": 0.0,
            "model_available": ensemble is not None,
            "missing_count": len(missing_skills),
            "message": "Could not score missing skills. Showing skills by job requirement instead."
        }

    # Step 3: Sort by final score
    sorted_skills = sorted(
        skill_scores.items(),
        key=lambda x: x[1]['final_score'],
        reverse=True
    )

    # Step 4: Group into phases
    phases = _create_learning_phases(sorted_skills, max_phases)

    # Calculate totals
    total_weeks = float(sum(p.get('duration_weeks', 0) for p in phases))

    return {
        "phases": phases,
        "total_weeks": total_weeks,
        "model_available": ensemble is not None,
        "missing_count": len(missing_skills),
        "message": None
    }


def _score_missing_skills(
    missing_skills: List[str],
    user_skills: List[str],
    gap_importance: Dict[str, float],
    ensemble: Optional[object] = None,
    job_skills: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
    """
    Score each missing skill using gap analysis + association rule models.
    
    For each skill, computes:
    - base_importance: How critical is it for the job? (0-1, from gap analysis)
    - model_score: How commonly do people with user's skills learn this? (0-1, from models)
    - final_score: Weighted combination (default 0.6 * gap + 0.4 * model)
    - sources: Which models recommended it (A1, A2, A3)
    - explanation: Human-readable reason for recommendation
    
    Returns:
        Dict mapping skill name -> {base_importance, model_score, final_score, sources, details, explanation}
        Always returns a dict (never None), even if empty.
    """
    skill_scores = {}
    
    if not missing_skills:
        return skill_scores
    
    for skill in missing_skills:
        try:
            base_importance = gap_importance.get(skill, 0.5)
            model_score = 0.0
            sources = []
            details = {}

            # Use job_skills for job-aware boost
            job_skills_set = set(s.lower().strip() for s in (job_skills or []))
            if ensemble is not None:
                try:
                    # Query all rules for this skill and user/job context
                    recs_df = None
                    if hasattr(ensemble, 'get_recommendations'):
                        recs_df = ensemble.get_recommendations(user_skills, top_n=50, target_job_skills=job_skills)
                    if recs_df is not None and not recs_df.empty:
                        # Find the row for this skill
                        skill_row = recs_df[recs_df['skill'].str.lower().str.strip() == skill.lower().strip()]
                        if not skill_row.empty:
                            # Use max(confidence * lift * job_boost) as model_score
                            skill_row = skill_row.iloc[0]
                            model_score = float(skill_row.get('confidence', 0.0)) * float(skill_row.get('lift', 1.0)) * float(skill_row.get('job_boost', 1.0))
                            sources = ["A1/A2/A3"]
                            details = {
                                'confidence': float(skill_row.get('confidence', 0.0)),
                                'lift': float(skill_row.get('lift', 1.0)),
                                'job_boost': float(skill_row.get('job_boost', 1.0)),
                            }
                except Exception:
                    model_score = 0.0
                    sources = []
                    details = {}

            final_score = 0.6 * base_importance + 0.4 * model_score if model_score > 0 else base_importance

            if sources:
                sources_str = ", ".join(sources)
                explanation = (
                    f"Important for the job ({base_importance:.0%}). "
                    f"Model signals: People with your skills and this job often learn this "
                    f"(confidence: {details.get('confidence', 0):.0%}, "
                    f"lift: {details.get('lift', 0):.1f}x, job boost: {details.get('job_boost', 1.0):.2f}). "
                    f"Sources: {sources_str}."
                )
            else:
                explanation = (
                    f"Important for the job ({base_importance:.0%}). "
                    f"No model signals available for this skill."
                )

            skill_scores[skill] = {
                'base_importance': base_importance,
                'model_score': model_score,
                'final_score': final_score,
                'sources': sources,
                'details': details,
                'explanation': explanation
            }
        except Exception:
            base_importance = gap_importance.get(skill, 0.5)
            skill_scores[skill] = {
                'base_importance': base_importance,
                'model_score': 0.0,
                'final_score': base_importance,
                'sources': [],
                'details': {},
                'explanation': f"Important for the job ({base_importance:.0%}). (Scoring failed, using gap analysis)"
            }
    
    return skill_scores


def _create_learning_phases(
    sorted_skills: List[Tuple[str, Dict]],
    max_phases: int = 5
) -> List[Dict]:
    """
    Group sorted skills into learning phases.
    
    Phases are named:
    - Phase 1: Foundation Skills
    - Phase 2: Core Competencies
    - Phase 3: Intermediate Skills
    - Phase 4: Advanced Techniques
    - Phase 5: Expert Level
    
    Each skill takes ~1.5 weeks per estimated complexity.
    """
    phase_names = [
        "Foundation Skills",
        "Core Competencies",
        "Intermediate Skills",
        "Advanced Techniques",
        "Expert Level"
    ]
    
    phase_difficulties = [
        "Easy",
        "Easy-Medium",
        "Medium",
        "Medium-Hard",
        "Hard"
    ]
    
    phases = []
    if not sorted_skills:
        return phases
    
    # Distribute skills across phases
    skills_per_phase = max(1, len(sorted_skills) // max_phases)
    
    for phase_idx in range(min(max_phases, len(sorted_skills))):
        start_idx = phase_idx * skills_per_phase
        end_idx = (
            (phase_idx + 1) * skills_per_phase
            if phase_idx < max_phases - 1
            else len(sorted_skills)
        )
        
        phase_skills_list = sorted_skills[start_idx:end_idx]
        
        if not phase_skills_list:
            continue
        
        # Format skill data for this phase
        skills_data = []
        for skill_name, skill_info in phase_skills_list:
            skills_data.append({
                'name': skill_name.title(),
                'final_score': skill_info['final_score'],
                'base_importance': skill_info['base_importance'],
                'model_score': skill_info['model_score'],
                'sources': skill_info['sources'],
                'explanation': skill_info['explanation']
            })
        
        phase = {
            'phase_number': phase_idx + 1,
            'title': phase_names[phase_idx] if phase_idx < len(phase_names) else f"Phase {phase_idx + 1}",
            'difficulty': phase_difficulties[phase_idx] if phase_idx < len(phase_difficulties) else "Hard",
            'skills': skills_data,
            'duration_weeks': int(len(phase_skills_list) * 1.5),  # ~1.5 weeks per skill
        }
        
        phases.append(phase)
    
    return phases
