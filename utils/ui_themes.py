"""Custom UI Styling Module - TalentScout Hiring Assistant

Provides custom CSS themes and styling options for the application.
"""

THEMES = {
    "professional": {
        "name": "Professional Blue",
        "primary_color": "#1E3A8A",
        "secondary_color": "#3B82F6",
        "background_color": "#F8FAFC",
        "text_color": "#1E293B",
        "accent_color": "#10B981"
    },
    "dark": {
        "name": "Dark Mode",
        "primary_color": "#1F2937",
        "secondary_color": "#374151",
        "background_color": "#111827",
        "text_color": "#F9FAFB",
        "accent_color": "#3B82F6"
    },
    "modern": {
        "name": "Modern Purple",
        "primary_color": "#7C3AED",
        "secondary_color": "#A78BFA",
        "background_color": "#FAF5FF",
        "text_color": "#1F2937",
        "accent_color": "#EC4899"
    },
    "corporate": {
        "name": "Corporate Gray",
        "primary_color": "#475569",
        "secondary_color": "#64748B",
        "background_color": "#F1F5F9",
        "text_color": "#0F172A",
        "accent_color": "#0EA5E9"
    }
}

def get_custom_css(theme="professional"):
    """Generate custom CSS based on selected theme"""
    theme_config = THEMES.get(theme, THEMES["professional"])
    
    css = f"""
    <style>
    /* Main App Styling */
    .stApp {{
        background-color: {theme_config['background_color']};
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: {theme_config['primary_color']} !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    
    /* Text */
    p, div, span, label {{
        color: {theme_config['text_color']};
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {theme_config['primary_color']};
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {theme_config['secondary_color']};
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {{
        background-color: {theme_config['background_color']};
        color: {theme_config['text_color']};
        border: 2px solid {theme_config['secondary_color']};
        border-radius: 6px;
        padding: 0.75rem;
        font-size: 1rem;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme_config['primary_color']};
        box-shadow: 0 0 0 3px {theme_config['secondary_color']}33;
    }}
    
    /* Cards and Containers */
    .element-container {{
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {theme_config['primary_color']};
    }}
    
    .sidebar .sidebar-content {{
        background-color: {theme_config['primary_color']};
        color: white;
    }}
    
    /* Progress Bar */
    .stProgress > div > div > div {{
        background-color: {theme_config['accent_color']};
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {theme_config['primary_color']};
        font-size: 2rem;
        font-weight: 700;
    }}
    
    /* Success/Info/Warning Messages */
    .stSuccess {{
        background-color: #D1FAE5;
        color: #065F46;
        border-left: 4px solid #10B981;
        border-radius: 6px;
        padding: 1rem;
    }}
    
    .stInfo {{
        background-color: #DBEAFE;
        color: #1E40AF;
        border-left: 4px solid #3B82F6;
        border-radius: 6px;
        padding: 1rem;
    }}
    
    .stWarning {{
        background-color: #FEF3C7;
        color: #92400E;
        border-left: 4px solid #F59E0B;
        border-radius: 6px;
        padding: 1rem;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {theme_config['secondary_color']}22;
        border-radius: 6px;
        font-weight: 600;
        color: {theme_config['primary_color']};
    }}
    
    /* File Uploader */
    .stFileUploader {{
        border: 2px dashed {theme_config['secondary_color']};
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
    }}
    
    /* Selectbox */
    .stSelectbox > div > div {{
        border: 2px solid {theme_config['secondary_color']};
        border-radius: 6px;
    }}
    
    /* Custom Sentiment Badge */
    .sentiment-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }}
    
    .sentiment-confident {{
        background-color: #D1FAE5;
        color: #065F46;
    }}
    
    .sentiment-moderate {{
        background-color: #FEF3C7;
        color: #92400E;
    }}
    
    .sentiment-uncertain {{
        background-color: #FEE2E2;
        color: #991B1B;
    }}
    
    /* Question Card */
    .question-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid {theme_config['accent_color']};
    }}
    
    /* Animation */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .element-container {{
        animation: fadeIn 0.3s ease-in;
    }}
    </style>
    """
    
    return css

def get_available_themes():
    """Get list of available themes"""
    return {key: value["name"] for key, value in THEMES.items()}
