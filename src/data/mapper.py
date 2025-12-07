class SkillMapper:
    """Class for mapping skills to categories"""

    def __init__(self):
        # Define skill categories
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
            'devops': ['jenkins', 'gitlab', 'github actions', 'ansible', 'puppet', 'chef'],
            'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'time management'],
            'data_science': ['machine learning', 'statistics', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
            'web_development': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask']
        }

    def map_to_category(self, skill):
        """Map a skill to its category"""
        if not skill or not isinstance(skill, str):
            return 'other'

        skill_lower = skill.lower().strip()

        for category, skills in self.skill_categories.items():
            if skill_lower in skills:
                return category

        # Check for partial matches
        for category, skills in self.skill_categories.items():
            for cat_skill in skills:
                if cat_skill in skill_lower or skill_lower in cat_skill:
                    return category

        return 'other'

    def get_category_stats(self, skills):
        """Get statistics about skill categories"""
        if not skills:
            return {}

        category_counts = {}
        for skill in skills:
            category = self.map_to_category(skill)
            category_counts[category] = category_counts.get(category, 0) + 1

        return category_counts
