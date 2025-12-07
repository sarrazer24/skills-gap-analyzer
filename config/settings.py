"""Application settings and constants for Skills Gap Analyzer"""

from typing import Dict, Any

# Application Configuration
APP_CONFIG: Dict[str, Any] = {
    "APP_TITLE": "🎯 Skills Gap Analyzer",
    "APP_ICON": "🎯",
    "APP_DESCRIPTION": "Machine Learning project using Association Rules & Clustering to analyze skill gaps",
    "VERSION": "1.0.0",
    "AUTHOR": "Skills Gap Analyzer Team",
    "GITHUB_REPO": "https://github.com/sarrazer24/skills-gap-analyzer",
    "KAGGLE_PROFILE": "https://www.kaggle.com/",
    "STREAMLIT_CLOUD_URL": "",  # To be filled after deployment
}

# Data Configuration
DATA_CONFIG: Dict[str, Any] = {
    "SAMPLE_SIZE": 1000,
    "MIN_SKILL_OCCURRENCE": 10,
    "MIN_SUPPORT": 0.01,
    "MIN_CONFIDENCE": 0.4,
    "MAX_LIFT": 10.0,
}

# Model Configuration
MODEL_CONFIG: Dict[str, Any] = {
    "ASSOCIATION_RULES": {
        "MIN_SUPPORT": 0.01,
        "MIN_CONFIDENCE": 0.4,
        "MAX_LEN": 3,
    },
    "CLUSTERING": {
        "N_CLUSTERS_RANGE": (2, 10),
        "RANDOM_STATE": 42,
    },
}

# UI Configuration
UI_CONFIG: Dict[str, Any] = {
    "MAX_SKILLS_DISPLAY": 20,
    "MAX_RECOMMENDATIONS": 10,
    "CHART_HEIGHT": 400,
    "SIDEBAR_WIDTH": 300,
}

# File Paths
PATHS: Dict[str, str] = {
    "DATA_RAW": "data/raw/",
    "DATA_PROCESSED": "data/processed/",
    "MODELS": "app/models/",
    "ASSETS": "app/assets/",
    "NOTEBOOKS": "notebooks/",
    "REPORTS": "reports/",
}

# Skill Categories
SKILL_CATEGORIES: Dict[str, str] = {
    "programming": ["python", "java", "javascript", "c++", "ruby", "php", "go"],
    "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
    "ai_ml": ["machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn"],
    "web_dev": ["html", "css", "react", "angular", "vue.js", "node.js"],
    "devops": ["jenkins", "git", "linux", "bash", "terraform"],
    "soft_skills": ["communication", "teamwork", "leadership", "problem solving"],
    "tools": ["excel", "tableau", "power bi", "jira", "slack"],
}

# Job Categories
JOB_CATEGORIES: Dict[str, str] = {
    "data_science": ["Data Scientist", "Data Analyst", "Machine Learning Engineer"],
    "software_dev": ["Software Engineer", "Full Stack Developer", "Backend Developer", "Frontend Developer"],
    "devops": ["DevOps Engineer", "Site Reliability Engineer", "Cloud Architect"],
    "business": ["Business Analyst", "Product Manager", "Project Manager"],
    "design": ["UX Designer", "UI Designer", "Graphic Designer"],
}
