# components/header.py
import streamlit as st

def render_header():
    """Render the main header section"""
    st.markdown('<h1 class="main-header">Job Skills Gap Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; font-size: 1.2em; margin-bottom: 2rem;'>
        Discover your skill gaps and create a personalized learning path using AI-powered insights
    </div>
    """, unsafe_allow_html=True)