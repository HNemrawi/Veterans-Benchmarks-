"""
Main application file for Veterans Housing Dashboard.

This module provides the main streamlit application with multiple tabs for:
1. Dashboard View - simplified metric cards for at-a-glance information
2. Reference View - detailed explanations and data downloads

The application follows a modular design pattern, separating:
- Data processing (data_processing.py)
- UI components (dashboard_components.py)
- Metric definitions (metric_definitions.py)
- Metric display logic (metrics_display.py)
"""
import streamlit as st
import pandas as pd
import traceback
from typing import Dict, Any, Tuple

# Import from modules
from data_processing import (
    process_data, 
    calculate_newly_identified, 
    calculate_chronic_metrics,
    prepare_gpd_analysis,
    deduplicate_dataframe,
    load_csv,
    filter_data,
    get_constants
)
from dashboard_components import (
    display_reporting_period_banner, 
    create_metrics_summary_download,
    coc_filter_section
)
from metrics_display import (
    display_dashboard_metrics,
    display_reference_metrics
)
from logo import HTML_FOOTER, HTML_HEADER_LOGO, HTML_HEADER_TITLE, setup_header
from styling import apply_custom_css, style_metric_cards


def initialize_session_state():
    """
    Initialize the session state variables if they don't exist.
    """
    if "original_df" not in st.session_state:
        st.session_state.original_df = None
    
    if "df_filtered" not in st.session_state:
        st.session_state.df_filtered = None
    
    if "metrics_data" not in st.session_state:
        st.session_state.metrics_data = {}
    
    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {}
    
    if "reporting_period" not in st.session_state:
        st.session_state.reporting_period = None


def process_all_metrics(df_filtered: pd.DataFrame) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, pd.DataFrame]]:
    """
    Process all metrics from the filtered DataFrame.
    
    Args:
        df_filtered: The filtered DataFrame to process
        
    Returns:
        Tuple of (metrics_data, dataframes):
            - metrics_data: Dictionary of metric values and metadata
            - dataframes: Dictionary of DataFrames for each metric
    """
    try:
        # Process data for main metrics
        (
            veterans_served_df,
            measure1_df,
            measure2_df,
            summary_df,
            final_df,
            total_veterans_served,
            veterans_ph_placement_count,
            filtered_veterans_count,
            average_days_deduped,
            median_days_deduped,
            reporting_period_start,
            reporting_period_end,
            allowed_project_types
        ) = process_data(df_filtered)

        # Prepare reporting period DataFrame
        rp_df = df_filtered.copy()
        rp_df["Project Start Date"] = pd.to_datetime(rp_df["Project Start Date"], errors="coerce")
        rp_df["Project Exit Date"] = pd.to_datetime(rp_df["Project Exit Date"], errors="coerce")
        
        # Filter to only include entries within the reporting period
        rp_filter = (
            (rp_df["Project Start Date"] >= reporting_period_start) & 
            (rp_df["Project Start Date"] <= reporting_period_end) &
            (rp_df["Project Type Code"].isin(allowed_project_types))
        )
        rp_df = rp_df[rp_filter].copy()

        # Calculate newly identified veterans
        newly_identified_count, newly_identified_df = calculate_newly_identified(
            rp_df,
            st.session_state.original_df,
            allowed_project_types,
            reporting_period_start
        )

        # Calculate chronic homelessness metrics
        chronic_metrics = calculate_chronic_metrics(
            df_filtered, 
            reporting_period_start, 
            reporting_period_end
        )
        
        # Get GPD funding sources from constants
        constants = get_constants()
        gpd_sources = constants["GPD_FUNDING_SOURCES"]
        
        # Get newly identified veterans in GPD TH
        newly_identified_th_df, newly_identified_th_count = prepare_gpd_analysis(
            newly_identified_df,
            gpd_sources
        )

        # Deduplicate DataFrames for Download
        veterans_served_df = deduplicate_dataframe(veterans_served_df)
        measure1_df = deduplicate_dataframe(measure1_df)
        measure2_df = deduplicate_dataframe(measure2_df)
        summary_df = deduplicate_dataframe(summary_df)
        final_df = deduplicate_dataframe(final_df)
        newly_identified_df = deduplicate_dataframe(newly_identified_df)
        newly_identified_th_df = deduplicate_dataframe(newly_identified_th_df)
        
        # Deduplicate chronic metrics DataFrames
        chronic_a1_df = deduplicate_dataframe(chronic_metrics["A1"][1])
        chronic_a2_df = deduplicate_dataframe(chronic_metrics["A2"][1])
        chronic_a3_df = deduplicate_dataframe(chronic_metrics["A3"][1])
        chronic_a4_df = deduplicate_dataframe(chronic_metrics["A4"][1])

        # For Newly Identified Veterans, only keep the enrollment with the earliest Project Start Date per Client
        newly_identified_earliest_df = (
            newly_identified_df
            .sort_values("Project Start Date")
            .drop_duplicates("Client ID", keep="first")
        )

        # Collect metrics data for consolidated storage
        metrics_data = {
            "A1": {
                "name": "Number of chronic & long-term Homeless Veterans who are not in permanent housing", 
                "value": chronic_metrics['A1'][0]
            },
            "A2": {
                "name": "Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted", 
                "value": chronic_metrics['A2'][0]
            },
            "A3": {
                "name": "Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need", 
                "value": chronic_metrics['A3'][0]
            },
            "A4": {
                "name": "Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for <90 Days Who Are Looking for Housing", 
                "value": chronic_metrics['A4'][0]
            },
            "Vets_Served": {
                "name": "Total Number of Veterans Served", 
                "value": total_veterans_served
            },
            "B1": {
                "name": "Number of Veterans Exited to or Moved Into Permanent Housing", 
                "value": filtered_veterans_count
            },
            "B2": {
                "name": "Average Days to Permanent Housing for Veterans (Goal 90 Days)", 
                "value": round(average_days_deduped, 1)
            },
            "B3": {
                "name": "Median Days to Permanent Housing for Veterans (Goal 90 Days)", 
                "value": round(median_days_deduped, 1)
            },
            "C1": {
                "name": "Number of Veterans Exited to or Moved Into Permanent Housing", 
                "value": filtered_veterans_count
            },
            "C2": {
                "name": "Number of Newly Identified Homeless Veterans", 
                "value": newly_identified_count
            },
            "D1": {
                "name": "Number of Newly Identified Homeless Veterans Entering Transitional Housing", 
                "value": newly_identified_th_count
            },
            "D2": {
                "name": "Number of Newly Identified Homeless Veterans", 
                "value": newly_identified_count
            }
        }
        
        # Collect dataframes for downloads
        dataframes = {
            "A1": chronic_a1_df,
            "A2": chronic_a2_df,
            "A3": chronic_a3_df,
            "A4": chronic_a4_df,
            "Vets_Served": veterans_served_df,
            "B1": measure2_df,
            "B2": summary_df,
            "B3": final_df,
            "C1": measure2_df,
            "C2": newly_identified_earliest_df,
            "D1": newly_identified_th_df,
            "D2": newly_identified_earliest_df
        }
        
        # Store reporting period for later use
        reporting_period = (reporting_period_start, reporting_period_end)
        
        return metrics_data, dataframes, reporting_period
        
    except Exception as e:
        st.error(f"An error occurred during data processing: {str(e)}")
        st.error(traceback.format_exc())
        return {}, {}, (None, None)


def main():
    """Main application function"""
    # Page setup
    st.set_page_config(page_title="Veterans Benchmarks", layout="wide")
    apply_custom_css()
    style_metric_cards()

    # Initialize session state
    initialize_session_state()

    # Header & logo
    setup_header()
    st.write("This dashboard provides metrics on Veterans served in the past 90 days.")

    # -----------------------
    # CSV Upload
    # -----------------------
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    
    if uploaded_file is None:
        st.info("Please upload a CSV file to get started.")
        st.markdown(HTML_FOOTER, unsafe_allow_html=True)
        return
    
    # Load data if not already in session state or if a new file is uploaded
    if st.session_state.original_df is None or uploaded_file.name != st.session_state.get("last_uploaded_file", ""):
        st.session_state.original_df = load_csv(uploaded_file)
        st.session_state.last_uploaded_file = uploaded_file.name
        # Reset filtered data when a new file is uploaded
        st.session_state.df_filtered = st.session_state.original_df
    
    # -----------------------
    # Filter Form (Compact Layout)
    # -----------------------
    selected_program_coc, selected_local_coc, submitted = coc_filter_section(st.session_state.original_df)

    if submitted:
        st.session_state.df_filtered = filter_data(st.session_state.original_df, selected_program_coc, selected_local_coc)
        # Clear cached results when filters change
        st.session_state.metrics_data = {}
        st.session_state.dataframes = {}
    
    # -----------------------
    # Process Data if not already processed
    # -----------------------
    if not st.session_state.metrics_data or not st.session_state.dataframes:
        metrics_data, dataframes, reporting_period = process_all_metrics(st.session_state.df_filtered)
        if metrics_data and dataframes:
            st.session_state.metrics_data = metrics_data
            st.session_state.dataframes = dataframes
            st.session_state.reporting_period = reporting_period
    
    # Exit if data processing failed
    if not st.session_state.metrics_data or not st.session_state.dataframes:
        st.error("Data processing failed. Please check your CSV file and try again.")
        st.markdown(HTML_FOOTER, unsafe_allow_html=True)
        return
    
    # -----------------------
    # Create tabs for dashboard and reference views
    # -----------------------
    tab1, tab2 = st.tabs(["Dashboard", "Reference & Documentation"])
    
    with tab1:
        # Dashboard view with simplified metric cards
        st.markdown(
            """
            <h2 style='text-align: center; color: #00629b; font-weight: bold;'>
                Veterans USICH Benchmarks Supplemental
            </h2>
            """,
            unsafe_allow_html=True
        )
        display_dashboard_metrics(st.session_state.metrics_data)
        
        # Add summary download at the bottom of dashboard
        if st.session_state.reporting_period:
            st.write("")
            st.write("")
            create_metrics_summary_download(st.session_state.metrics_data, st.session_state.reporting_period)
    
    with tab2:
        # Reference view with detailed cards and downloads
        st.header("Metrics Reference & Documentation")
        st.write("""
        This page provides detailed information about each metric, including calculation methodology
        and the ability to download the underlying data for further analysis.
        """)
        
        display_reference_metrics(
            st.session_state.metrics_data,
            st.session_state.dataframes
        )

    # Display footer
    st.markdown(HTML_FOOTER, unsafe_allow_html=True)


if __name__ == "__main__":
    main()