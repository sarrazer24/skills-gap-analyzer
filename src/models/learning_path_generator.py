"""
Learning Path Generator - Smart Learning Recommendations

Uses association rules to create optimal learning paths with prerequisites.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
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
