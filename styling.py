import streamlit as st

CUSTOM_CSS = """
<style>
/* Global styling */
html, body, [class*="css"] {
    font-family: 'Open Sans', sans-serif;
    background-color: #ffffff;
    color: #0a0a0a;
    margin: 0;
    padding: 0;
}

/* Container styling */
.block-container {
    padding: 1rem 2rem !important;
    background-color: #ffffff;
}

/* Headings */
h1, h2, h3, h4 {
    color: #0a0a0a;
    margin-bottom: 0.5rem;
}

/* DataFrame styling */
.dataframe thead {
    background-color: #e2efe8 !important;
    color: #0a0a0a !important;
}
.dataframe tbody tr:nth-child(even) {
    background-color: #f8fbf9 !important;
}
.dataframe tbody tr:nth-child(odd) {
    background-color: #ffffff !important;
}

/* Metric card styling */
div[data-testid="stMetric"],
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e2efe8;
    padding: 1rem;
    border-radius: 8px;
    border-left: 0.5rem solid #00629b !important;
}

/* Button styling for interactive elements */
button {
    background-color: #00629b;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    color: #ffffff;
    cursor: pointer;
    transition: opacity 0.2s ease-in-out;
}
button:hover {
    opacity: 0.8;
}

/* Expander header styling */
button[data-baseweb="expander"] {
    font-weight: bold;
    font-size: 1rem;
    color: #00629b;
}

/* Download button styling (Streamlit-specific) */
.stDownloadButton button {
    background-color: #00629b;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    color: #ffffff;
}

/* Custom divider style */
hr.custom-divider {
    border: 0;
    border-top: 1px solid #e2efe8;
    margin: 2em 0;
}
</style>
"""

def apply_custom_css():
    """
    Injects the custom CSS into the Streamlit app for consistent light styling.
    Ensures that both local and deployed versions share the same style.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def style_metric_cards(
    background_color: str = "#ffffff",
    border_size_px: int = 1,
    border_color: str = "#e2efe8",
    border_radius_px: int = 8,
    border_left_color: str = "#00629b",
    box_shadow: bool = True
) -> None:
    """
    Applies additional styling for metric cards with customizable options.
    
    Parameters:
        background_color (str): Background color of the cards.
        border_size_px (int): Border width in pixels.
        border_color (str): Border color.
        border_radius_px (int): Border radius in pixels.
        border_left_color (str): Left border accent color.
        box_shadow (bool): Whether to apply a shadow effect.
    """
    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(0, 0, 0, 0.1) !important;"
        if box_shadow else "box-shadow: none !important;"
    )
    st.markdown(f"""
    <style>
        div[data-testid="stMetric"],
        div[data-testid="metric-container"] {{
            background-color: {background_color};
            border: {border_size_px}px solid {border_color};
            padding: 1rem;
            border-radius: {border_radius_px}px;
            border-left: 0.5rem solid {border_left_color} !important;
            {box_shadow_str}
        }}
    </style>
    """, unsafe_allow_html=True)

def divider():
    """
    Inserts a styled horizontal divider to separate sections.
    """
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)