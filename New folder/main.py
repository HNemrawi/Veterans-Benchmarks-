import streamlit as st 
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from styling import apply_custom_css, style_metric_cards, divider
from data_processing import process_data, calculate_newly_identified, calculate_chronic_metrics
from logo import HTML_FOOTER, HTML_HEADER_LOGO

@st.cache_data
def load_csv(uploaded_file) -> pd.DataFrame:
    """
    Load and pre-process the CSV file.
    
    Args:
        uploaded_file: File object from st.file_uploader
        
    Returns:
        Processed DataFrame
    """
    try:
        df = pd.read_csv(uploaded_file)
        # Convert any columns with "ID" in the name to numeric, ignoring errors
        for col in df.columns:
            if "ID" in col:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {str(e)}")
        return pd.DataFrame()

def filter_data(df: pd.DataFrame, program_coc: str, local_coc: str) -> pd.DataFrame:
    """
    Filter the DataFrame based on CoC selections.
    
    Args:
        df: Input DataFrame
        program_coc: Selected Program Setup CoC value ("None" if not filtering)
        local_coc: Selected Local CoC Code value ("None" if not filtering)
        
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    if program_coc != "None" and "Program Setup CoC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Program Setup CoC"] == program_coc]
    if local_coc != "None" and "Local CoC Code" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Local CoC Code"] == local_coc]
    return df_filtered

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

def create_metrics_summary_download(metrics_data: Dict[str, Any], reporting_period: Tuple[pd.Timestamp, pd.Timestamp]) -> None:
    """
    Create a download button for a consolidated CSV with all metrics.
    
    Args:
        metrics_data: Dictionary with all metrics data
        reporting_period: Tuple of (start_date, end_date)
    """
    # Create a DataFrame with all metrics
    metrics_df = pd.DataFrame({
        "Metric ID": [],
        "Metric Name": [],
        "Value": [],
        "Reporting Period Start": [],
        "Reporting Period End": []
    })
    
    # Add each metric to the DataFrame
    for metric_id, metric_info in metrics_data.items():
        new_row = pd.DataFrame({
            "Metric ID": [metric_id],
            "Metric Name": [metric_info["name"]],
            "Value": [metric_info["value"]],
            "Reporting Period Start": [reporting_period[0].strftime('%Y-%m-%d')],
            "Reporting Period End": [reporting_period[1].strftime('%Y-%m-%d')]
        })
        metrics_df = pd.concat([metrics_df, new_row], ignore_index=True)
    
    # Create the download button
    csv_data = metrics_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download All Metrics Summary",
        data=csv_data,
        file_name="veterans_metrics_summary.csv",
        mime="text/csv"
    )

def display_metric_card(
    title: str, 
    value: Any, 
    calculation_details: str, 
    download_data: pd.DataFrame, 
    download_filename: str
) -> None:
    """
    Create a standardized metric card with title, value, details, and download button.
    
    Args:
        title: Metric title
        value: Metric value to display
        calculation_details: Details to show in expander
        download_data: DataFrame to make available for download
        download_filename: Filename for downloaded data
    """
    c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
    
    with c1:
        st.write(f"**{title}**")
    
    with c2:
        st.metric(label="", value=value)
    
    with c3:
        with st.expander("Calculation Details", expanded=False):
            st.write(calculation_details)
    
    with c4:
        create_download_button("Download Data", download_data, download_filename)

def deduplicate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicates a DataFrame on ["Client ID", "Enrollment ID"] if both exist.
    Otherwise, deduplicates on ["Client ID"] only.
    
    Args:
        df: DataFrame to deduplicate
        
    Returns:
        Deduplicated DataFrame
    """
    subset_cols = []
    if "Client ID" in df.columns:
        subset_cols.append("Client ID")
    if "Enrollment ID" in df.columns:
        subset_cols.append("Enrollment ID")
    
    if subset_cols:
        return df.drop_duplicates(subset=subset_cols, keep="first")
    else:
        return df

def prepare_gpd_analysis(
    newly_identified_df: pd.DataFrame,
    gpd_sources: List[str]
) -> Tuple[pd.DataFrame, int]:
    """
    Analyzes newly identified veterans entering GPD TH.
    
    Args:
        newly_identified_df: DataFrame with newly identified veterans
        gpd_sources: List of GPD funding sources
        
    Returns:
        Tuple of (DataFrame with newly identified TH veterans, count)
    """
    # Filter for newly identified veterans in GPD TH
    newly_identified_th_df = newly_identified_df[
        (newly_identified_df["Project Type Code"] == "Transitional Housing") &
        (newly_identified_df["Funding Source"].isin(gpd_sources))
    ].copy()
    
    # Count unique clients
    newly_identified_th_count = newly_identified_th_df["Client ID"].nunique()
    
    return newly_identified_th_df, newly_identified_th_count

def main():
    """Main application function"""
    # Page setup
    st.set_page_config(page_title="Veteran Housing Dashboard", layout="wide")
    apply_custom_css()
    style_metric_cards()

    # Header & logo
    st.markdown(HTML_HEADER_LOGO, unsafe_allow_html=True)
    st.title("Veterans Benchmarks Supplemental Dashboard")
    st.write("This dashboard provides metrics on Veterans served in the past 90 days.")

    # -----------------------
    # CSV Upload
    # -----------------------
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    
    if uploaded_file is None:
        st.info("Please upload a CSV file to get started.")
        st.markdown(HTML_FOOTER, unsafe_allow_html=True)
        return
    
    # Load data if not already in session state
    if "original_df" not in st.session_state:
        st.session_state.original_df = load_csv(uploaded_file)
    original_df = st.session_state.original_df
    
    # Initialize filtered data if not exists
    if "df_filtered" not in st.session_state:
        st.session_state.df_filtered = original_df

    # -----------------------
    # Filter Form (Compact Layout)
    # -----------------------
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

    if submitted:
        st.session_state.df_filtered = filter_data(original_df, selected_program_coc, selected_local_coc)

    # Use the filtered DataFrame from session state
    df_filtered = st.session_state.df_filtered

    # -----------------------
    # Run Main Processing
    # -----------------------
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

        # -----------------------
        # Prepare Data for "Newly Identified" Metrics
        # -----------------------
        # Define reporting period DataFrame
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
            original_df,
            allowed_project_types,
            reporting_period_start
        )

        # Calculate chronic homelessness metrics
        chronic_metrics = calculate_chronic_metrics(
            df_filtered, 
            reporting_period_start, 
            reporting_period_end
        )
        
        # GPD Funding Sources
        gpd_sources = [
            "VA: Grant Per Diem – Low Demand",
            "VA: Grant Per Diem – Hospital to Housing",
            "VA: Grant Per Diem – Clinical Treatment",
            "VA: Grant Per Diem – Service Intensive Transitional Housing"
        ]
        
        # Get newly identified veterans in GPD TH
        newly_identified_th_df, newly_identified_th_count = prepare_gpd_analysis(
            newly_identified_df,
            gpd_sources
        )

        # -----------------------
        # Deduplicate DataFrames for Download
        # -----------------------
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

        # -----------------------
        # Display Reporting Period Banner
        # -----------------------
        reporting_period_banner = f"""
        <div style='background-color: #3E3E3E; padding: 15px; border-left: 5px solid #1f77b4; border-radius: 5px; margin-bottom: 2rem;'>
            <h3 style='margin-top: 0; color: white;'>📊 Reporting Period</h3>
            <p style='font-size: 1.2rem; margin-bottom: 0; color: #cccccc;'>{reporting_period_start.strftime('%B %d, %Y')} to {reporting_period_end.strftime('%B %d, %Y')}</p>
        </div>
        """
        st.markdown(reporting_period_banner, unsafe_allow_html=True)

        # -----------------------
        # Collect metrics data for consolidated download
        metrics_data = {}
        
        # Display Metric Cards
        # -----------------------
        
        # A1-A4: Chronic Homelessness Metrics
        # A1: Chronic Vets not in PH
        chronic_a1_details = """
        **Definition:**  
        Number of chronic & long-term Homeless Veterans who are not in permanent housing.

        **Detailed Logic:**  
        - Veterans must meet HUD's definition of chronically homeless.
        - They must be currently active in the system during the reporting period.
        - They must not be in permanent housing, which means either:
          1. They are enrolled in a non-PH project type, or
          2. They are enrolled in a PH project but do not have a Housing Move-in Date.
        """
        display_metric_card(
            "A1- Chronic & Long-Term Homeless Veterans Not in PH",
            f"{chronic_metrics['A1'][0]}",
            chronic_a1_details,
            chronic_a1_df,
            "chronic_vets_not_in_ph.csv"
        )
        metrics_data["A1"] = {
            "name": "Chronic & Long-Term Homeless Veterans Not in PH", 
            "value": chronic_metrics['A1'][0]
        }
        divider()
        
        # A2: Chronic Vets offered PH in last 2 weeks
        chronic_a2_details = """
        **Definition:**  
        Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted.

        **Detailed Logic:**  
        - Veterans must meet criteria for chronic homelessness.
        - They must have received a permanent housing offer within the last 14 days.
        - Their decision status must be "Decision Pending" (not yet accepted or declined).
        - They must not currently be in permanent housing.
        """
        display_metric_card(
            "A2- Chronic Veterans with Recent PH Offers (Decision Pending)",
            f"{chronic_metrics['A2'][0]}",
            chronic_a2_details,
            chronic_a2_df,
            "chronic_vets_ph_offer_pending.csv"
        )
        metrics_data["A2"] = {
            "name": "Chronic Veterans with Recent PH Offers (Decision Pending)", 
            "value": chronic_metrics['A2'][0]
        }
        divider()
        
        # A3: Chronic Vets in GPD TH
        chronic_a3_details = """
        **Definition:**  
        Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need.

        **Detailed Logic:**  
        - Veterans must meet criteria for chronic homelessness.
        - They must be currently enrolled in a Transitional Housing program.
        - The Transitional Housing program must be funded by one of the VA's Grant Per Diem funding sources:
          - VA: Grant Per Diem – Low Demand
          - VA: Grant Per Diem – Hospital to Housing
          - VA: Grant Per Diem – Clinical Treatment
          - VA: Grant Per Diem – Service Intensive Transitional Housing
        """
        display_metric_card(
            "A3- Chronic Veterans in GPD-Funded TH Programs",
            f"{chronic_metrics['A3'][0]}",
            chronic_a3_details,
            chronic_a3_df,
            "chronic_vets_in_gpd_th.csv"
        )
        metrics_data["A3"] = {
            "name": "Chronic Veterans in GPD-Funded TH Programs", 
            "value": chronic_metrics['A3'][0]
        }
        divider()
        
        # A4: Chronic Vets in PH < 90 days
        chronic_a4_details = """
        **Definition:**  
        Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for <90 Days Who Are Looking for Housing.

        **Detailed Logic:**  
        - Veterans must meet criteria for chronic homelessness.
        - They must be enrolled in a Permanent Housing program (PH project types).
        - Their enrollment must be less than 90 days old.
        - They must not have a Housing Move-in Date yet (still looking for housing).
        """
        display_metric_card(
            "A4- Chronic Veterans Recently Enrolled in PH, Not Yet Housed",
            f"{chronic_metrics['A4'][0]}",
            chronic_a4_details,
            chronic_a4_df,
            "chronic_vets_ph_not_housed.csv"
        )
        metrics_data["A4"] = {
            "name": "Chronic Veterans Recently Enrolled in PH, Not Yet Housed", 
            "value": chronic_metrics['A4'][0]
        }
        divider()
        
        # 1) Number of Veterans Served (Past 90 Days)
        vets_served_details = f"""
        **Definition:**  
        Counts all unique Veteran clients with an active enrollment in TH,PH,CE,SH,SO,ES and Other(Veterans By Name List) during the past 90 days.

        **Detailed Logic:**  
        - **Reporting Period:** The last 90 days (from {reporting_period_start.date()} to {reporting_period_end.date()}).  
        - A Veteran is marked as active if:  
          1. Their Project Start Date is on or before today (reporting_period_end), and  
          2. Their Project Exit Date is either missing or occurs on/after the start of the 90-day window.  
        - Final count is based on unique Client IDs.
        """
        display_metric_card(
            "Number of Veterans Served (Past 90 Days)",
            f"{total_veterans_served}",
            vets_served_details,
            veterans_served_df,
            "veterans_served.csv"
        )
        metrics_data["Vets_Served"] = {
            "name": "Veterans Served (Past 90 Days)", 
            "value": total_veterans_served
        }
        divider()
        
        # 2) Veterans Placed in Permanent Housing (All Pathways)
        ph_placement_details = """
        **Definition:**  
        Counts Veterans who secured permanent housing during the reporting period without excluding GPD-Funded Transitional Housing.

        **Detailed Logic:**  
        - **Eligibility:** Veteran's record must have either a valid Housing Move-in Date in a PH project OR an exit to Permanent Housing destination, within the 90-day period.  
        - **Final Count:** Each Veteran is counted only once, based on unique Client IDs.
        """
        display_metric_card(
            "Veterans Placed in Permanent Housing",
            f"{veterans_ph_placement_count}",
            ph_placement_details,
            measure1_df,
            "ph_placements_no_th_excl.csv"
        )
        metrics_data["PH_Placements"] = {
            "name": "Veterans Placed in Permanent Housing", 
            "value": veterans_ph_placement_count
        }
        divider()
        
        # 3) Veterans Placed in Permanent Housing (Excluding GPD-Funded TH)
        ph_excluding_th_details = """
        **Definition:**  
        Counts only those Veterans whose placement in permanent housing did not stem from a GPD-funded Transitional Housing program.

        **Detailed Logic:**  
        - **Step 1:** Start with the set of Veterans placed in PH (as defined above).  
        - **Step 2:** Exclude any enrollment where the Project Type is "Transitional Housing" with a Funding Source matching one of these GPD funds:  
          - VA: Grant Per Diem – Low Demand  
          - VA: Grant Per Diem – Hospital to Housing  
          - VA: Grant Per Diem – Clinical Treatment  
          - VA: Grant Per Diem – Service Intensive Transitional Housing  
        - **Step 3:** Count each remaining unique Veteran once.
        """
        display_metric_card(
            "B1/C1- Veterans Placed in Permanent Housing (Excluding GPD-Funded TH)",
            f"{filtered_veterans_count}",
            ph_excluding_th_details,
            measure2_df,
            "ph_placements_th_excluded.csv"
        )
        metrics_data["PH_Placements_Excl_TH"] = {
            "name": "Veterans Placed in PH (Excluding GPD-Funded TH)", 
            "value": filtered_veterans_count
        }
        divider()
        
        # 4) Average Days from Identification to Housing
        avg_days_details = """
        **Definition:**  
        Computes the average number of days between a Veteran's 'Date of Identification' and 
        their 'Last Housing Event' during the 90-day reporting period.

        **Detailed Logic:**  
        1. **Episode Formation:**  
        - For each Veteran, all enrollments are sorted in chronological order using the 'Project Start Date'.  
        - Consecutive enrollments are merged into a single episode if the gap between them is less than 90 days.
        2. **Date of Identification:**  
        - The 'Date of Identification' is defined as the 'Project Start Date' of the first enrollment in the current episode.
        3. **Determining the Last Housing Event:**  
        - Two potential dates are evaluated:  
            a. The 'Housing Move-in Date' (if available within the reporting period), and  
            b. The 'Project Exit Date' (if it represents a transition into permanent housing within the reporting window).  
        - The later of these two dates is selected as the 'Last Housing Event'.
        4. **Time Difference Calculation:**  
        - The difference in days is computed between the 'Last Housing Event' and the 'Date of Identification' for each Veteran.
        5. **Average Calculation:**  
        - Finally, the average is determined by taking the arithmetic mean of these day differences across all Veterans.
        """
        display_metric_card(
            "B2- Average Days from Identification to Housing",
            f"{average_days_deduped:.1f}",
            avg_days_details,
            summary_df,
            "veterans_summary_days_to_ph.csv"
        )
        metrics_data["Avg_Days_to_Housing"] = {
            "name": "Average Days from Identification to Housing", 
            "value": round(average_days_deduped, 1)
        }
        divider()
        
        # 5) Median Days from Identification to Housing
        median_days_details = """
        **Definition:**  
        Finds the median value of the durations (in days) from the Date of Identification 
        to the Last Housing Event for Veterans.

        **Detailed Logic:**  
        - Follow the same steps as in the average calculation to compute the number of days 
          for each Veteran.
        - Sort these day counts and select the middle value (or the average of the two middle values if even).
        - This measure minimizes the impact of extreme values to provide a central tendency.
        """
        display_metric_card(
            "B3- Median Days from Identification to Housing",
            f"{median_days_deduped:.1f}",
            median_days_details,
            final_df,
            "veteran_data_processed.csv"
        )
        metrics_data["Median_Days_to_Housing"] = {
            "name": "Median Days from Identification to Housing", 
            "value": round(median_days_deduped, 1)
        }
        divider()
        
        # 6) Newly Identified Veterans
        newly_id_details = """
        **Definition:**  
        Flags Veterans who are appearing for the first time (or after a gap of ≥90 days) 
        during the reporting period.

        **Detailed Logic:**  
        1. **Earliest Enrollment Date:** For each Veteran enrolled in the current 90-day window, determine the earliest enrollment date.  
        2. **Comparison with Prior Enrollments:** Compare this date against any historical enrollment for that Veteran:  
          - If no prior enrollment exists, then mark the Veteran as 'newly identified'.  
          - If no prior enrollment overlaps with 90-day window before earliest start, then mark the Veteran as 'newly identified'.  
          - Otherwise, the Veteran is not considered newly identified.  
        - Count each unique newly identified Veteran once.
        """
        display_metric_card(
            "C2/D2- Newly Identified Veterans",
            f"{newly_identified_count}",
            newly_id_details,
            newly_identified_earliest_df,
            "newly_identified_veterans.csv"
        )
        metrics_data["Newly_Identified_Veterans"] = {
            "name": "Newly Identified Veterans", 
            "value": newly_identified_count
        }
        divider()
        
        # 7) Newly Identified Vets Entering GPD-Funded Transitional Housing
        newly_id_th_details = """
        **Definition:**  
        Among the newly identified Veterans, counts those who enrolled in Transitional Housing 
        programs funded by GPD.

        **Detailed Logic:**  
        1. **Newly Identified Veterans:** Apply the same logic as in the 'Newly Identified Veterans' metric.  
        2. **Transitional Housing with GPD Funding:** Filter these newly identified Veterans to include only those who:  
          - Enrolled in Transitional Housing programs, and  
          - Have a Funding Source matching one of the GPD funds:  
            - VA: Grant Per Diem – Low Demand,  
            - VA: Grant Per Diem – Hospital to Housing,  
            - VA: Grant Per Diem – Clinical Treatment,  
            - VA: Grant Per Diem – Service Intensive Transitional Housing.
        """
        display_metric_card(
            "D1- Newly Identified Vets Entering GPD-Funded Transitional Housing",
            f"{newly_identified_th_count}",
            newly_id_th_details,
            newly_identified_th_df,
            "newly_identified_th_gpd_veterans.csv"
        )
    
    except Exception as e:
        st.error(f"An error occurred during data processing: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

    # Display footer
    st.markdown(HTML_FOOTER, unsafe_allow_html=True)

if __name__ == "__main__":
    main()