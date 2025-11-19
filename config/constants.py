# config/constants.py

# Color scheme
COLORS = {
    'primary_blue': '#2563eb',
    'secondary_blue': '#3b82f6',
    'light_blue': '#dbeafe',
    'dark_blue': '#1e40af',
    'success_green': '#10b981',
    'warning_orange': '#f59e0b',
    'error_red': '#ef4444',
    'gray_50': '#f9fafb',
    'gray_100': '#f3f4f6',
    'gray_800': '#1f2937'
}

# Available skills pool
ALL_SKILLS = [
    "Python", "JavaScript", "SQL", "React", "Node.js", "AWS", "Docker", "Kubernetes", 
    "TensorFlow", "PyTorch", "Statistics", "Machine Learning", "Data Visualization", 
    "Git", "Linux", "Networking", "CSS", "HTML", "MongoDB", "PostgreSQL", 
    "REST APIs", "GraphQL", "Algorithms", "Data Structures", "CI/CD", "Terraform",
    "Java", "C++", "Go", "Rust", "TypeScript", "Angular", "Vue.js", "Spring Boot",
    "Flask", "Django", "FastAPI", "Redis", "Kafka", "Airflow", "Prometheus", "Grafana"
]

# Default session state values
DEFAULT_SESSION_STATE = {
    'analyzed': False,
    'current_skills': [],
    'required_skills': [],
    'selected_job': None,
    'job_data': {}
}

# Learning path constants
LEARNING_TIMES = {
    'Beginner': 20,
    'Intermediate': 40,
    'Advanced': 80
}

PRIORITY_LEVELS = {
    'High': '#ef4444',
    'Medium': '#f59e0b', 
    'Low': '#6b7280'
}