# utils/ui.py
import streamlit as st

def apply_styling():
    """Apply custom CSS styling with dark mode support"""
    st.markdown("""
    <style>
        /* ========== DARK MODE SUPPORT ========== */
        
        /* Cards */
        .card {
            background: var(--background-color);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border-color);
            margin-bottom: 16px;
        }
        
        /* Headers */
        h1 {
            font-weight: 700;
        }
        h2 {
            font-weight: 600;
            font-size: 1.3rem;
        }
        h3 {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s;
            padding: 8px 20px;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
        
        /* Primary button */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4F46E5, #6366F1);
            border: none;
            color: white !important;
        }
        
        /* Dataframe */
        [data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #4F46E5, #818CF8);
            border-radius: 10px;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            border-radius: 8px;
        }
        
        /* Radio buttons */
        .stRadio > div {
            gap: 10px;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            font-weight: 500;
            font-size: 15px;
        }
        
        /* Status box */
        [data-testid="stStatus"] {
            border-radius: 10px;
        }
        
        /* Divider */
        hr {
            margin: 16px 0;
        }
        
        /* Alert boxes */
        .stAlert {
            border-radius: 10px;
            border: none;
        }
        
        /* Select box */
        .stSelectbox > div > div {
            border-radius: 8px;
        }
        
        /* Text input */
        .stTextInput > div > div > input {
            border-radius: 8px;
        }
        
        /* Text area */
        .stTextArea > div > div > textarea {
            border-radius: 8px;
        }
        
        /* Number input */
        .stNumberInput > div > div > input {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)


def show_header(title: str, subtitle: str = ""):
    """Display a styled page header"""
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="margin-bottom: 4px;">{title}</h1>
        <p style="color: #94A3B8; font-size: 14px; margin-top: 0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def card(content_func):
    """Wrap content in a card"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    content_func()
    st.markdown('</div>', unsafe_allow_html=True)