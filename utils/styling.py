# utils/styling.py
import streamlit as st
from config.constants import COLORS

def apply_custom_styles():
    """Apply custom CSS styling that works in both light and dark mode"""
    st.markdown(f"""
    <style>
        /* Main theme colors - compatible with dark mode */
        :root {{
            --primary-blue: {COLORS['primary_blue']};
            --secondary-blue: {COLORS['secondary_blue']};
            --light-blue: {COLORS['light_blue']};
            --dark-blue: {COLORS['dark_blue']};
            --success-green: {COLORS['success_green']};
            --warning-orange: {COLORS['warning_orange']};
            --error-red: {COLORS['error_red']};
        }}
        
        /* Dark mode compatibility */
        .main {{
            color: var(--text-color);
        }}
        
        /* Skill badges - fixed for dark mode */
        .skill-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary-blue), var(--secondary-blue));
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            margin: 6px 6px 6px 0;
            font-weight: 600;
            font-size: 0.9em;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .skill-badge-owned {{
            background: linear-gradient(135deg, var(--success-green), #34d399);
        }}
        
        .skill-badge-missing {{
            background: linear-gradient(135deg, var(--warning-orange), #fbbf24);
        }}
        
        /* Card styling - dark mode compatible */
        .custom-card {{
            background: var(--background-color);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
            color: var(--text-color);
        }}
        
        /* Header styling */
        .main-header {{
            background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 1rem;
        }}
        
        /* Dark mode specific fixes */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --background-color: #0e1117;
                --text-color: #fafafa;
                --border-color: #262730;
            }}
            
            .custom-card {{
                background: #262730;
                border: 1px solid #444;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                background-color: #262730;
                color: #fafafa;
            }}
            
            .stTabs [aria-selected="true"] {{
                background-color: var(--primary-blue);
                color: white;
            }}
        }}
        
        /* Light mode */
        @media (prefers-color-scheme: light) {{
            :root {{
                --background-color: white;
                --text-color: #31333F;
                --border-color: #e0e0e0;
            }}
        }}
        
        /* Progress bar customization */
        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, var(--primary-blue), var(--secondary-blue));
        }}
        
        /* Ensure text is readable in both modes */
        .stMarkdown, .stText, .stDataFrame {{
            color: var(--text-color) !important;
        }}
        
        /* Fix dataframe styling for dark mode */
        .dataframe {{
            color: var(--text-color) !important;
            background: var(--background-color) !important;
        }}
        
        .dataframe th {{
            background: var(--primary-blue) !important;
            color: white !important;
        }}
        
        .dataframe td {{
            background: var(--background-color) !important;
            color: var(--text-color) !important;
            border-color: var(--border-color) !important;
        }}
    </style>
    """, unsafe_allow_html=True)