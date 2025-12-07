# data/sample_data.py
import streamlit as st
from src.data.loader import DataLoader

# Load jobs from CSV
loader = DataLoader()
try:
    SAMPLE_JOBS = loader.load_sample_jobs_from_csv('data/processed/all_jobs_mapped.csv', n_samples=10)
except Exception as e:
    # Fallback to hardcoded if CSV loading fails
    SAMPLE_JOBS = {
    "Senior Data Scientist": {
        "description": "We are looking for a Senior Data Scientist with 5+ years of experience in machine learning and statistical analysis. Required skills include Python, SQL, ML frameworks, and cloud platforms.",
        "required_skills": ["Python", "Machine Learning", "SQL", "Statistics", "AWS", "TensorFlow", "Data Visualization"],
        "experience_level": "Senior",
        "salary_range": "$120,000 - $160,000",
        "demand_level": "High"
    },
    "Full Stack Developer": {
        "description": "Seeking a Full Stack Developer to build and maintain web applications. Must have proficiency in React, Node.js, databases, and REST APIs.",
        "required_skills": ["JavaScript", "React", "Node.js", "SQL", "MongoDB", "REST APIs", "Git", "Docker"],
        "experience_level": "Mid-level",
        "salary_range": "$80,000 - $120,000",
        "demand_level": "Very High"
    },
    "DevOps Engineer": {
        "description": "Looking for a DevOps Engineer to manage infrastructure and deployment pipelines. Expertise in containerization, CI/CD, and cloud platforms required.",
        "required_skills": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Terraform", "Jenkins", "Monitoring"],
        "experience_level": "Mid-level",
        "salary_range": "$90,000 - $130,000",
        "demand_level": "High"
    },
    "Machine Learning Engineer": {
        "description": "Machine Learning Engineer needed to design and implement ML systems. Strong background in algorithms, distributed systems, and ML ops required.",
        "required_skills": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "Docker", "AWS", "MLOps", "Data Pipelines"],
        "experience_level": "Senior",
        "salary_range": "$130,000 - $180,000",
        "demand_level": "High"
    }
}

# Skill associations data
SKILL_ASSOCIATIONS = {
    "Python": {
        "requires": ["Algorithms", "Data Structures", "OOP"], 
        "confidence": 0.92,
        "market_demand": "Very High",
        "avg_salary_boost": "+15%"
    },
    "Machine Learning": {
        "requires": ["Python", "Statistics", "Linear Algebra", "Calculus"], 
        "confidence": 0.88,
        "market_demand": "High",
        "avg_salary_boost": "+25%"
    },
    "React": {
        "requires": ["JavaScript", "CSS", "HTML", "State Management"], 
        "confidence": 0.95,
        "market_demand": "Very High",
        "avg_salary_boost": "+12%"
    },
    "AWS": {
        "requires": ["Linux", "Networking", "Cloud Concepts", "Security"], 
        "confidence": 0.85,
        "market_demand": "High",
        "avg_salary_boost": "+18%"
    },
    "Docker": {
        "requires": ["Linux", "Networking", "DevOps Basics", "Containers"], 
        "confidence": 0.91,
        "market_demand": "High",
        "avg_salary_boost": "+14%"
    }
}

def render_welcome_content():
    """Render welcome screen content"""
    st.markdown("""
    <div class="custom-card">
        <h2 style='text-align: center; margin-bottom: 1rem;'>Welcome to Skills Gap Analyzer</h2>
        <p style='text-align: center; font-size: 1.2em; margin-bottom: 2rem;'>
            Discover your path to career success with AI-powered skill analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h4>Smart Analysis</h4>
            <p>AI-powered skill extraction and gap identification</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h4>Personalized Path</h4>
            <p>Custom learning roadmap based on your goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="custom-card">
            <h4>Career Growth</h4>
            <p>Data-driven insights for career advancement</p>
        </div>
        """, unsafe_allow_html=True)
    
    # How it works
    st.markdown("### How It Works")
    steps_col1, steps_col2, steps_col3, steps_col4 = st.columns(4)
    
    with steps_col1:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <div style='background: #3b82f6; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; font-weight: bold;'>1</div>
            <h4>Select Job</h4>
            <p>Choose your target role</p>
        </div>
        """, unsafe_allow_html=True)
    
    with steps_col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <div style='background: #3b82f6; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; font-weight: bold;'>2</div>
            <h4>Input Skills</h4>
            <p>Select your current skills</p>
        </div>
        """, unsafe_allow_html=True)
    
    with steps_col3:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <div style='background: #3b82f6; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; font-weight: bold;'>3</div>
            <h4>Get Analysis</h4>
            <p>Receive detailed gap analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with steps_col4:
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <div style='background: #3b82f6; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; font-weight: bold;'>4</div>
            <h4>Learn & Grow</h4>
            <p>Follow your learning path</p>
        </div>
        """, unsafe_allow_html=True)