import streamlit as st

HTML_HEADER_LOGO = """
    <div style="font-style: italic; color: #808080; text-align: left; padding: 10px 0;">
        <a href="https://icalliances.org/" target="_blank">
            <img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/eb7da336-e61c-4e0b-bbb5-1a7b9d45bff6/Dash+Logo+2.png?format=750w" 
                 width="250" 
                 style="max-width: 100%; height: auto;">
        </a>
    </div>
"""

HTML_FOOTER = """
    <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e2efe8;">
        <div style="font-style: italic; color: #808080; text-align: center; margin-bottom: 1rem;">
            <a href="https://icalliances.org/" target="_blank">
                <img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/eb7da336-e61c-4e0b-bbb5-1a7b9d45bff6/Dash+Logo+2.png?format=750w" 
                     width="99" 
                     style="max-width: 100%; height: auto;">
            </a>
            <br>
            <span style="font-size: 0.9rem;">DASH™ is a trademark of Institute for Community Alliances.</span>
        </div>
        <div style="font-style: italic; color: #808080; text-align: center;">
            <a href="https://icalliances.org/" target="_blank">
                <img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/1475614371395-KFTYP42QLJN0VD5V9VB1/ICA+Official+Logo+PNG+%28transparent%29.png?format=1500w" 
                     width="99" 
                     style="max-width: 100%; height: auto;">
            </a>
            <br>
            <span style="font-size: 0.9rem;">© 2024 Institute for Community Alliances (ICA). All rights reserved.</span>
        </div>
    </div>
"""

HTML_HEADER_TITLE = """
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #00629b; font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; line-height: 1.2;">
            Veterans USICH Benchmarks Supplemental
        </h1>
    </div>
"""

def setup_header():
    """Set up the header of the Streamlit page with improved layout and spacing."""
    # Create header container with better spacing
    st.markdown('<div style="margin-bottom: 2rem;">', unsafe_allow_html=True)
    
    # Logo and title layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(HTML_HEADER_LOGO, unsafe_allow_html=True)
    
    with col2:
        st.markdown(HTML_HEADER_TITLE, unsafe_allow_html=True)
    
    # Close header container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a subtle divider
    st.markdown(
        '<hr style="border: 0; border-top: 2px solid #e2efe8; margin: 1rem 0 2rem 0;">',
        unsafe_allow_html=True
    )