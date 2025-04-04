import streamlit as st

CUSTOM_CSS = """
<style>
html, body, [class*="css"] {
    font-family: 'Open Sans', sans-serif;
    background-color: #2E2E2E;
    color: #FFFFFF;
    margin: 0;
    padding: 0;
}
.block-container {
    padding: 1rem 2rem !important;
    background-color: #2E2E2E;
}
h1, h2, h3, h4 {
    color: #FFFFFF;
    margin-bottom: 0.5rem;
}
.dataframe thead {
    background-color: #444444 !important;
    color: #FFFFFF !important;
}
.dataframe tbody tr:nth-child(even) {
    background-color: #3E3E3E !important;
}
.dataframe tbody tr:nth-child(odd) {
    background-color: #2E2E2E !important;
}
div[data-testid="stMetric"],
div[data-testid="metric-container"] {
    background-color: #2E2E2E;
    border: 1px solid #444444;
    padding: 1rem;
    border-radius: 8px;
    border-left: 0.5rem solid #1f77b4 !important;
}

/* Download button styling */
button[title="Download Data"],
button[aria-label="Download Data"] {
    background-color: #1f77b4;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    color: #FFFFFF;
    font-weight: bold;
    cursor: pointer;
}

/* Expander header styling */
button[data-baseweb="expander"] {
    font-weight: bold;
    font-size: 1rem;
    color: #1f77b4;
}

/* Custom divider styling */
hr.custom-divider {
    border: 0;
    border-top: 1px solid #444444;
    margin: 2em 0;
}
</style>
"""

def apply_custom_css():
    """
    Applies the custom CSS defined above to style the page background,
    fonts, tables, metrics, buttons, expanders, and dividers.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def style_metric_cards(
    background_color: str = "#2E2E2E",
    border_size_px: int = 1,
    border_color: str = "#444444",
    border_radius_px: int = 8,
    border_left_color: str = "#1f77b4",
    box_shadow: bool = True
) -> None:
    """
    Applies additional CSS styling specifically for Streamlit metric containers
    to match the dark background theme.
    """
    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(0, 0, 0, 0.3) !important;"
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
