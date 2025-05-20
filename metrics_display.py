"""
Module for displaying metrics in dashboard and reference views.

This module contains functions to display metrics in both the dashboard view (simplified)
and the reference view (detailed with explanation and download options).
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple

from dashboard_components import (
    display_metric_card, 
    divider,
    display_reporting_period_banner
)
from metric_definitions import get_metric_definitions


def display_dashboard_metrics(metrics_data: Dict[str, Dict[str, Any]]):
    """
    Display simplified metric cards for dashboard view.
    
    Args:
        metrics_data: Dictionary with metric IDs as keys and values containing:
                     - value: The numeric value of the metric
                     - name: The full name/title of the metric
    """
    # Display total veterans served at the top
    divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.reporting_period:
            reporting_period_start, reporting_period_end = st.session_state.reporting_period
            display_reporting_period_banner(reporting_period_start, reporting_period_end)
        
    
    with col2:
        display_metric_card(
            "Total Number of Veterans Served",
            f"{metrics_data['Vets_Served']['value']}"
        )

    divider()

    # Section A: Chronic homelessness
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 12px; color: #1f77b4;">
          A. Have you ended chronic and long-term homelessness among Veterans in your community?
        </div>
        <p><strong>Target:</strong> <span style="color: #1f77b4;">Zero chronic and long-term homeless Veterans as of the date of review.</span></p>
        <ul style="list-style-type: none; padding-left: 0; color: #FFFFFF;">
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">A1:</span> Number of chronic & long-term Homeless Veterans who are not in permanent housing</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">A2:</span> Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">A3:</span> Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">A4:</span> Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for &lt;90 Days Who Are Looking for Housing</li>
        </ul>
        <p style="font-weight: bold; color: #ff6b6b; margin-top: 12px;">
          Note: A1 - A2 - A3 - A4 should = 0
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    # A1-A4 metrics in a grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        display_metric_card(
            "A1: Number of chronic & long-term Homeless Veterans who are not in permanent housing",
            f"{metrics_data['A1']['value']}"
        )
    
    with col2:
        display_metric_card(
            "A2: Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted",
            f"{metrics_data['A2']['value']}"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_metric_card(
            "A3: Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need",
            f"{metrics_data['A3']['value']}"
        )
    
    with col2:
        display_metric_card(
            "A4: Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for <90 Days Who Are Looking for Housing",
            f"{metrics_data['A4']['value']}"
        )
    
    divider()
    
    # Section B: Quick access to housing
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 12px; color: #1f77b4;">
          B. Do Veterans have quick access to permanent housing?
        </div>
        <p><strong>Target:</strong> <span style="color: #1f77b4;">For homeless Veterans placed in permanent housing (PH) in the last 90 days, the average time from date of identification to date of PH move-in is less than or equal to 90 days.</span></p>
        <ul style="list-style-type: none; padding-left: 0; color: #FFFFFF;">
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">B1:</span> Number of Veterans Exited to or Moved Into Permanent Housing</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">B2:</span> Average Days to Permanent Housing for Veterans (Goal 90 Days)</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">B3:</span> Median Days to Permanent Housing for Veterans (Goal 90 Days)</li>
        </ul>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_metric_card(
            "B1: Number of Veterans Exited to or Moved Into Permanent Housing",
            f"{metrics_data['B1']['value']}"
        )
    
    with col2:
        display_metric_card(
            "B2: Average Days to Permanent Housing for Veterans (Goal 90 Days)",
            f"{metrics_data['B2']['value']:.1f}"
        )
    
    col1, col2 = st.columns(2)
    
    with col2:
        display_metric_card(
            "B3: Median Days to Permanent Housing for Veterans (Goal 90 Days)",
            f"{metrics_data['B3']['value']:.1f}"
        )
    
    divider()
    
    # Section C: Sufficient housing capacity
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 12px; color: #1f77b4;">
          C. Does the community have sufficient permanent housing capacity?
        </div>
        <p><strong>Target:</strong> <span style="color: #1f77b4;">In the last 90 days, the total number of homeless Veterans moving into permanent housing is greater than or equal to the total number of newly identified homeless Veterans.</span></p>
        <ul style="list-style-type: none; padding-left: 0; color: #FFFFFF;">
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">C1:</span> Number of Veterans Exited to or Moved Into Permanent Housing</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">C2:</span> Number of Newly Identified Homeless Veterans</li>
        </ul>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_metric_card(
            "C1: Number of Veterans Exited to or Moved Into Permanent Housing",
            f"{metrics_data['C1']['value']}"
        )
    
    with col2:
        display_metric_card(
            "C2: Number of Newly Identified Homeless Veterans",
            f"{metrics_data['C2']['value']}"
        )
    
    divider()
    
    # Section D: Housing First commitment
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 12px; color: #1f77b4;">
          D. Is the community committed to Housing First and provides service-intensive transitional housing to Veterans experiencing homelessness only in limited instances?
        </div>
        <p><strong>Target:</strong> <span style="color: #1f77b4;">In the last 90 days, the total number of homeless Veterans entering service-intensive transitional housing is less than the total number of newly identified homeless Veterans.</span></p>
        <ul style="list-style-type: none; padding-left: 0; color: #FFFFFF;">
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">D1:</span> Number of Newly Identified Homeless Veterans Entering Transitional Housing</li>
          <li style="margin: 8px 0;"><span style="font-weight: bold; color: #1f77b4;">D2:</span> Number of Newly Identified Homeless Veterans</li>
        </ul>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_metric_card(
            "D1: Number of Newly Identified Homeless Veterans Entering Transitional Housing",
            f"{metrics_data['D1']['value']}"
        )
    
    with col2:
        display_metric_card(
            "D2: Number of Newly Identified Homeless Veterans",
            f"{metrics_data['D2']['value']}"
        )


def display_reference_metrics(
    metrics_data: Dict[str, Dict[str, Any]],
    dataframes: Dict[str, pd.DataFrame]
):
    """
    Display detailed metric cards with explanations and download buttons for reference view.
    
    Args:
        metrics_data: Dictionary with metric IDs as keys and values containing value and name
        dataframes: Dictionary with metric IDs as keys and DataFrames as values
    """
    metric_definitions = get_metric_definitions()
    
    # Custom implementation for Veterans Served metric
    metric_def = metric_definitions["Vets_Served"]
    metric_value = metrics_data["Vets_Served"]["value"]
    df = dataframes["Vets_Served"]
    
    c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
    
    with c1:
        st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>Veterans Served</span>", unsafe_allow_html=True)
    
    with c2:
        # Add a proper label and use CSS to hide it visually if needed
        st.metric(
            label="Veterans Served", 
            value=metric_value,
            label_visibility="collapsed"  # Hide the label but keep it accessible
        )
    
    with c3:
        with st.expander("Calculation Details", expanded=False):
            st.write(metric_def["details"])
    
    with c4:
        # Create download button with unique key
        csv_data = df.to_csv(index=False)
        st.download_button(
            label=f"⬇️ Download Data",
            data=csv_data,
            file_name=metric_def["filename"],
            mime="text/csv",
            key="download_veterans_served"
        )
    
    
    # Section A: Chronic Homelessness Metrics
    st.header("A. Have you ended chronic and long-term homelessness among Veterans in your community?")
    st.markdown("**Target:** Zero chronic and long-term homeless Veterans as of the date of review.")
    
    # Use custom detailed metric card to avoid dependence on dashboard_components
    section_counter = 0
    for metric_id in ["A1", "A2", "A3", "A4"]:
        section_counter += 1
        metric_def = metric_definitions[metric_id]
        metric_value = metrics_data[metric_id]["value"]
        df = dataframes[metric_id]
        
        value_display = f"{metric_value}" if not isinstance(metric_value, float) else f"{metric_value:.1f}"
        
        # Custom implementation of detailed metric card
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        
        with c1:
            # Extract the metric ID from the title (e.g., "A1: Number of..." -> "A1")
            title_parts = metric_def["title"].split(":", 1)
            display_id = title_parts[0].strip() if len(title_parts) > 0 else metric_def["title"]
            st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>{display_id}</span>", unsafe_allow_html=True)
        
        with c2:
            # Add a proper label that will be visually hidden
            st.metric(
                label=display_id, 
                value=value_display,
                label_visibility="collapsed"  # Hide the label but keep it accessible
            )
        
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(metric_def["details"])
        
        with c4:
            # Create download button with unique key
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download Data",
                data=csv_data,
                file_name=metric_def["filename"],
                mime="text/csv",
                key=f"download_A_{section_counter}_{metric_id}"
            )
        
        # Safely get description, handling cases where title doesn't contain a colon
        title_parts = metric_def["title"].split(":", 1)
        description = title_parts[1].strip() if len(title_parts) > 1 else metric_def["title"]
        
        # Display the full metric title after the card for clarity
        st.markdown(f"<p style='margin-top: -15px; color: #AAAAAA;'>{description}</p>", unsafe_allow_html=True)
        
        divider()
    
    # Section B: Quick access to housing
    st.header("B. Do Veterans have quick access to permanent housing?")
    st.markdown("**Target:** For homeless Veterans placed in permanent housing (PH) in the last 90 days, the average time from date of identification to date of PH move-in is less than or equal to 90 days.")
    
    section_counter = 0
    for metric_id in ["B1", "B2", "B3"]:
        section_counter += 1
        metric_def = metric_definitions[metric_id]
        metric_value = metrics_data[metric_id]["value"]
        df = dataframes[metric_id]
        
        value_display = f"{metric_value}" if not isinstance(metric_value, float) else f"{metric_value:.1f}"
        
        # Custom implementation of detailed metric card
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        
        with c1:
            # Extract the metric ID from the title (e.g., "B1: Number of..." -> "B1")
            title_parts = metric_def["title"].split(":", 1)
            display_id = title_parts[0].strip() if len(title_parts) > 0 else metric_def["title"]
            st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>{display_id}</span>", unsafe_allow_html=True)
        
        with c2:
            # Add a proper label that will be visually hidden
            st.metric(
                label=display_id, 
                value=value_display,
                label_visibility="collapsed"  # Hide the label but keep it accessible
            )
        
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(metric_def["details"])
        
        with c4:
            # Create download button with unique key
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download Data",
                data=csv_data,
                file_name=metric_def["filename"],
                mime="text/csv",
                key=f"download_B_{section_counter}_{metric_id}"
            )
        
        # Safely get description
        title_parts = metric_def["title"].split(":", 1)
        description = title_parts[1].strip() if len(title_parts) > 1 else metric_def["title"]
        
        # Display the full metric title after the card for clarity
        st.markdown(f"<p style='margin-top: -15px; color: #AAAAAA;'>{description}</p>", unsafe_allow_html=True)
        
        divider()
    
    # Section C: Sufficient housing capacity
    st.header("C. Does the community have sufficient permanent housing capacity?")
    st.markdown("**Target:** In the last 90 days, the total number of homeless Veterans moving into permanent housing is greater than or equal to the total number of newly identified homeless Veterans.")
    
    section_counter = 0
    for metric_id in ["C1", "C2"]:
        section_counter += 1
        metric_def = metric_definitions[metric_id]
        metric_value = metrics_data[metric_id]["value"]
        df = dataframes[metric_id]
        
        value_display = f"{metric_value}" if not isinstance(metric_value, float) else f"{metric_value:.1f}"
        
        # Custom implementation of detailed metric card
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        
        with c1:
            # Extract the metric ID from the title (e.g., "C1: Number of..." -> "C1")
            title_parts = metric_def["title"].split(":", 1)
            display_id = title_parts[0].strip() if len(title_parts) > 0 else metric_def["title"]
            st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>{display_id}</span>", unsafe_allow_html=True)
        
        with c2:
            # Add a proper label that will be visually hidden
            st.metric(
                label=display_id, 
                value=value_display,
                label_visibility="collapsed"  # Hide the label but keep it accessible
            )
        
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(metric_def["details"])
        
        with c4:
            # Create download button with unique key
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download Data",
                data=csv_data,
                file_name=metric_def["filename"],
                mime="text/csv",
                key=f"download_C_{section_counter}_{metric_id}"
            )
        
        # Safely get description
        title_parts = metric_def["title"].split(":", 1)
        description = title_parts[1].strip() if len(title_parts) > 1 else metric_def["title"]
        
        # Display the full metric title after the card for clarity
        st.markdown(f"<p style='margin-top: -15px; color: #AAAAAA;'>{description}</p>", unsafe_allow_html=True)
        
        divider()
    
    # Section D: Housing First commitment
    st.header("D. Is the community committed to Housing First and provides service-intensive transitional housing to Veterans experiencing homelessness only in limited instances?")
    st.markdown("**Target:** In the last 90 days, the total number of homeless Veterans entering service-intensive transitional housing is less than the total number of newly identified homeless Veterans.")
    
    section_counter = 0
    for metric_id in ["D1", "D2"]:
        section_counter += 1
        metric_def = metric_definitions[metric_id]
        metric_value = metrics_data[metric_id]["value"]
        df = dataframes[metric_id]
        
        value_display = f"{metric_value}" if not isinstance(metric_value, float) else f"{metric_value:.1f}"
        
        # Custom implementation of detailed metric card
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        
        with c1:
            # Extract the metric ID from the title (e.g., "D1: Number of..." -> "D1")
            title_parts = metric_def["title"].split(":", 1)
            display_id = title_parts[0].strip() if len(title_parts) > 0 else metric_def["title"]
            st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>{display_id}</span>", unsafe_allow_html=True)
        
        with c2:
            # Add a proper label that will be visually hidden
            st.metric(
                label=display_id, 
                value=value_display,
                label_visibility="collapsed"  # Hide the label but keep it accessible
            )
        
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(metric_def["details"])
        
        with c4:
            # Create download button with unique key
            csv_data = df.to_csv(index=False)
            st.download_button(
                label=f"⬇️ Download Data",
                data=csv_data,
                file_name=metric_def["filename"],
                mime="text/csv",
                key=f"download_D_{section_counter}_{metric_id}"
            )
        
        # Safely get description
        title_parts = metric_def["title"].split(":", 1)
        description = title_parts[1].strip() if len(title_parts) > 1 else metric_def["title"]
        
        # Display the full metric title after the card for clarity
        st.markdown(f"<p style='margin-top: -15px; color: #AAAAAA;'>{description}</p>", unsafe_allow_html=True)
        
        if metric_id != "D2":
            divider()