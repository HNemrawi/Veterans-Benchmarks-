"""
Module for dashboard UI components.

This module contains all the components used to build the dashboard interface,
including metric cards, download buttons, and other UI elements.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

def display_reporting_period_banner(
    reporting_period_start: datetime,
    reporting_period_end: datetime,
    background_color: str = "#3E3E3E",
    border_left_color: str = "#1f77b4",
    text_color: str = "white",
    subtext_color: str = "#cccccc",
    border_radius_px: int = 5,
    padding_px: int = 15,
    margin_bottom_rem: float = 2.0
) -> None:
    """
    Displays a styled banner showing the reporting period range.
    
    Args:
        reporting_period_start (datetime): Start date of reporting period.
        reporting_period_end (datetime): End date of reporting period.
        background_color (str): Banner background color.
        border_left_color (str): Color of the left border accent.
        text_color (str): Main text (header) color.
        subtext_color (str): Subtext (date range) color.
        border_radius_px (int): Border radius in pixels.
        padding_px (int): Inner padding in pixels.
        margin_bottom_rem (float): Bottom margin in rem units.
    """
    try:
        formatted_start = reporting_period_start.strftime('%B %d, %Y')
        formatted_end = reporting_period_end.strftime('%B %d, %Y')
    except Exception as e:
        st.error("Invalid date input.")
        raise ValueError("Start and end dates must be datetime objects.") from e

    banner_html = f"""
    <div style='
        background-color: {background_color};
        padding: {padding_px}px;
        border-left: 5px solid {border_left_color};
        border-radius: {border_radius_px}px;
        margin-bottom: {margin_bottom_rem}rem;
    '>
        <h3 style='margin-top: 0; color: {text_color};'>📊 Reporting Period</h3>
        <p style='font-size: 1.2rem; margin-bottom: 0; color: {subtext_color};'>
            {formatted_start} to {formatted_end}
        </p>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def display_metric_card(
    title: str, 
    value: Any, 
    col_width: List[float] = [1.2, 0.6, 2, 1]
) -> None:
    """
    Create a simplified metric card with just title and value for the dashboard view.
    
    Args:
        title: Metric title
        value: Metric value to display
        col_width: Column width distribution
    """
    # Extract a short identifier from the title to use as an accessible label
    title_parts = title.split(":", 1)
    label = title_parts[0].strip() if len(title_parts) > 0 else title
    
    st.markdown(
        f"""
        <div style="padding: 10px; background-color: #3E3E3E; border: 1px solid #444444; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 10px; box-shadow: 0 0.15rem 1.75rem 0 rgba(0, 0, 0, 0.2);">
            <div style="font-weight: bold; color: #1f77b4; font-size: 1.1rem; margin-bottom: 8px;">{title}</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: #FFFFFF;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def display_detailed_metric_card(
    title: str, 
    value: Any, 
    calculation_details: str, 
    download_data: pd.DataFrame, 
    download_filename: str,
    col_width: List[float] = [1.2, 0.6, 2, 1]
) -> None:
    """
    Create a detailed metric card with title, value, details, and download button.
    
    Args:
        title: Metric title
        value: Metric value to display
        calculation_details: Details to show in expander
        download_data: DataFrame to make available for download
        download_filename: Filename for downloaded data
        col_width: Column width distribution
    """
    # Extract the metric ID from the title (e.g., "A1: Number of..." -> "A1")
    title_parts = title.split(":", 1)
    metric_id = title_parts[0].strip() if len(title_parts) > 0 else title
    
    c1, c2, c3, c4 = st.columns(col_width)
    
    with c1:
        st.markdown(f"<span style='font-weight: bold; color: #1f77b4; font-size: 1.1rem;'>{metric_id}</span>", unsafe_allow_html=True)
    
    with c2:
        # Use the metric ID as the label for accessibility, but collapse it visually
        st.metric(label=metric_id, value=value, label_visibility="collapsed")
    
    with c3:
        with st.expander("Calculation Details", expanded=False):
            st.write(calculation_details)
    
    with c4:
        create_download_button("Download Data", download_data, download_filename)


def create_download_button(label: str, data: pd.DataFrame, filename: str) -> None:
    """
    Create a download button for a DataFrame.
    
    Args:
        label: Button label
        data: DataFrame to download
        filename: Output filename
    """
    csv_data = data.to_csv(index=False)
    st.download_button(
        label=f"⬇️ {label}",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )


def create_metrics_summary_download(
    metrics_data: Dict[str, Any],
    reporting_period: Tuple[pd.Timestamp, pd.Timestamp]
) -> None:
    """
    Create a download button for a consolidated CSV with all metrics,
    including a timestamped filename safe for Windows.
    
    Args:
        metrics_data (Dict[str, Any]): Dictionary of metric entries.
        reporting_period (Tuple[pd.Timestamp, pd.Timestamp]): (start_date, end_date) of the reporting period.
    """
    # Prepare empty DataFrame
    metrics_df = pd.DataFrame(columns=[
        "Metric ID", "Metric Name", "Value",
        "Reporting Period Start", "Reporting Period End"
    ])

    # Populate the DataFrame
    for metric_id, metric_info in metrics_data.items():
        new_row = pd.DataFrame({
            "Metric ID": [metric_id],
            "Metric Name": [metric_info.get("name", "")],
            "Value": [metric_info.get("value", "")],
            "Reporting Period Start": [reporting_period[0].strftime('%Y-%m-%d')],
            "Reporting Period End": [reporting_period[1].strftime('%Y-%m-%d')]
        })
        metrics_df = pd.concat([metrics_df, new_row], ignore_index=True)

    # Generate safe timestamp for filename (Windows-safe)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"veterans_benchmarks_summary_{timestamp_str}.csv"

    # Create CSV and download button
    csv_data = metrics_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download All Metrics Summary",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )


def divider():
    """
    Display a visual divider between sections.
    """
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)


def coc_filter_section(original_df):
    """
    Create a filter form for CoC selection.
    
    Args:
        original_df: The original DataFrame to filter
    
    Returns:
        Tuple of (selected_program_coc, selected_local_coc, submitted)
    """
    with st.form("CoC_filter_form"):
        st.subheader("Filter by CoC")
        col1, col2 = st.columns(2)
        
        with col1:
            program_coc_options = ["None"]
            if "Program Setup CoC" in original_df.columns:
                program_coc_options += sorted(original_df["Program Setup CoC"].dropna().unique().tolist())
            selected_program_coc = st.selectbox("Program Setup CoC", program_coc_options, index=0)
        
        with col2:
            local_coc_options = ["None"]
            if "Local CoC Code" in original_df.columns:
                local_coc_options += sorted(original_df["Local CoC Code"].dropna().unique().tolist())
            selected_local_coc = st.selectbox("Local CoC Code", local_coc_options, index=0)
        
        submitted = st.form_submit_button("Apply Filters")
    
    return selected_program_coc, selected_local_coc, submitted