"""
CSS Styles for Enhanced Filter System
"""

def get_filter_css() -> str:
    """Return the complete CSS for the filter system"""
    return """
    <style>
    .filter-hover-menu {
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .filter-trigger {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        border: none;
        text-decoration: none;
        user-select: none;
    }
    
    .filter-trigger:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4);
        background: linear-gradient(90deg, #ee5a24, #ff6b6b);
    }
    
    .filter-trigger:active {
        transform: translateY(0);
        box-shadow: 0 2px 10px rgba(238, 90, 36, 0.3);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .filter-hover-menu {
            position: relative;
            top: auto;
            right: auto;
            margin-bottom: 20px;
            width: 100%;
        }
        
        .filter-trigger {
            justify-content: center;
            width: 100%;
        }
    }
    
    /* Enhanced expander styling */
    div[data-testid="expander"] {
        border: 1px solid #e1e5e9;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    div[data-testid="expander"] > div:first-child {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 12px 12px 0 0;
        padding: 16px 20px;
    }
    
    div[data-testid="expander"] summary {
        font-weight: 600;
        color: #2c3e50;
        cursor: pointer;
    }
    
    /* Filter section styling */
    .filter-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #f1f3f4;
    }
    
    .filter-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    
    /* Success and info message styling */
    .stSuccess, .stInfo {
        border-radius: 8px;
        margin-top: 15px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Selectbox and input styling improvements */
    .stSelectbox > div > div {
        border-radius: 6px;
    }
    
    .stTextInput > div > div > input {
        border-radius: 6px;
    }
    
    .stDateInput > div > div > input {
        border-radius: 6px;
    }
    
    .stCheckbox > label {
        font-weight: 500;
    }
    </style>
    """
