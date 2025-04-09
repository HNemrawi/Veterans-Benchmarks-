import streamlit as st 
import pandas as pd
from styling import apply_custom_css, style_metric_cards, divider
from data_processing import process_data, calculate_newly_identified

@st.cache_data
def load_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    # Convert any columns with "ID" in the name to numeric, ignoring errors
    for col in df.columns:
        if "ID" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df

def filter_data(df, program_coc, local_coc):
    df_filtered = df.copy()
    if program_coc != "None" and "Program Setup CoC" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Program Setup CoC"] == program_coc]
    if local_coc != "None" and "Local CoC Code" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Local CoC Code"] == local_coc]
    return df_filtered

def main():
    st.set_page_config(page_title="Veteran Housing Dashboard", layout="wide")
    apply_custom_css()
    style_metric_cards()

    st.title("Veterans Benchmarks Supplemental Dashboard")
    st.write("This dashboard provides metrics on Veterans served in the past 90 days.")

    # -----------------------
    # CSV Upload
    # -----------------------
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        if "original_df" not in st.session_state:
            st.session_state.original_df = load_csv(uploaded_file)
        original_df = st.session_state.original_df

        # If filtered data does not exist yet, initialize it with the original data
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
        rp_df = df_filtered.copy()
        rp_df["Project Start Date"] = pd.to_datetime(rp_df["Project Start Date"], errors="coerce")
        rp_df["Project Exit Date"] = pd.to_datetime(rp_df["Project Exit Date"], errors="coerce")
        rp_df = rp_df[
            (rp_df["Project Start Date"] >= reporting_period_start)
            & (rp_df["Project Start Date"] <= reporting_period_end)
            & (rp_df["Project Type Code"].isin(allowed_project_types))
        ].copy()

        newly_identified_count, newly_identified_df = calculate_newly_identified(
            rp_df,
            original_df,
            allowed_project_types,
            reporting_period_start
        )

        # Newly Identified Vets Entering GPD TH (subset of newly identified)
        gpd_sources = [
            "VA: Grant Per Diem – Low Demand",
            "VA: Grant Per Diem – Hospital to Housing",
            "VA: Grant Per Diem – Clinical Treatment",
            "VA: Grant Per Diem – Service Intensive Transitional Housing"
        ]
        newly_identified_th_df = newly_identified_df[
            (newly_identified_df["Project Type Code"] == "Transitional Housing") &
            (newly_identified_df["Funding Source"].isin(gpd_sources))
        ].copy()
        newly_identified_th_count = newly_identified_th_df["Client ID"].nunique()

        # -----------------------
        # Deduplicate DataFrames for Download
        # -----------------------
        def deduplicate(df):
            """
            Deduplicates each DataFrame on ["Client ID", "Enrollment ID"] if both exist.
            Otherwise, deduplicates on ["Client ID"] only.
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

        veterans_served_df     = deduplicate(veterans_served_df)
        measure1_df            = deduplicate(measure1_df)
        measure2_df            = deduplicate(measure2_df)
        summary_df             = deduplicate(summary_df)
        final_df               = deduplicate(final_df)
        newly_identified_df    = deduplicate(newly_identified_df)
        newly_identified_th_df  = deduplicate(newly_identified_th_df)

        # For Newly Identified Veterans, only keep the enrollment with the earliest Project Start Date per Client
        newly_identified_earliest_df = newly_identified_df.sort_values("Project Start Date").drop_duplicates("Client ID", keep="first")

        # Create CSV strings for downloads
        csv_vets_served = veterans_served_df.to_csv(index=False)
        csv_measure1    = measure1_df.to_csv(index=False)
        csv_measure2    = measure2_df.to_csv(index=False)
        csv_summary     = summary_df.to_csv(index=False)
        csv_final       = final_df.to_csv(index=False)
        csv_new         = newly_identified_earliest_df.to_csv(index=False)
        csv_th_new      = newly_identified_th_df.to_csv(index=False)

        # ----------------------------------------------------------------------
        # Display Metrics & Detailed Calculation Explanations
        # ----------------------------------------------------------------------

        # 1) Number of Veterans Served (Past 90 Days)
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Number of Veterans Served (Past 90 Days)**")
        with c2:
            st.metric(label="", value=f"{total_veterans_served}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Counts all unique Veteran clients with an active enrollment in TH,PH,CE,SH,SO,ES and Other(Veterans By Name List) during the past 90 days.

                    **Detailed Logic:**  
                    - **Reporting Period:** The last 90 days (from {start} to {end}).  
                    - A Veteran is marked as active if:  
                      1. Their Project Start Date is on or before today (reporting_period_end), and  
                      2. Their Project Exit Date is either missing or occurs on/after the start of the 90-day window.  
                    - Final count is based on unique Client IDs.
                    """.format(start=reporting_period_start.date(), end=reporting_period_end.date())
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_vets_served,
                file_name="veterans_served.csv",
                mime="text/csv"
            )

        divider()

        # 2) Veterans Placed in Permanent Housing (All Pathways)
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Veterans Placed in Permanent Housing**")
        with c2:
            st.metric(label="", value=f"{veterans_ph_placement_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Counts Veterans who secured permanent housing during the reporting period without excluding GPD-Funded Transitional Housing.

                    **Detailed Logic:**  
                    - **Eligibility:** Veteran’s record must have either a valid Housing Move-in Date in a PH project OR an exit to Permanent Housing destination, within the 90-day period.  
                    - **Final Count:** Each Veteran is counted only once, based on unique Client IDs.
                    """
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_measure1,
                file_name="ph_placements_no_th_excl.csv",
                mime="text/csv"
            )

        divider()

        # 3) Veterans Placed in Permanent Housing (Excluding GPD-Funded TH)
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Veterans Placed in Permanent Housing (Excluding GPD-Funded TH)**")
        with c2:
            st.metric(label="", value=f"{filtered_veterans_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
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
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_measure2,
                file_name="ph_placements_th_excluded.csv",
                mime="text/csv"
            )

        divider()

        # 4) Average Days from Identification to Housing
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Average Days from Identification to Housing**")
        with c2:
            st.metric(label="", value=f"{average_days_deduped:.1f}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Computes the average number of days between a Veteran’s 'Date of Identification' and 
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
                )

        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_summary,
                file_name="veterans_summary_days_to_ph.csv",
                mime="text/csv"
            )

        divider()

        # 5) Median Days from Identification to Housing
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Median Days from Identification to Housing**")
        with c2:
            st.metric(label="", value=f"{median_days_deduped:.1f}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Finds the median value of the durations (in days) from the Date of Identification 
                    to the Last Housing Event for Veterans.

                    **Detailed Logic:**  
                    - Follow the same steps as in the average calculation to compute the number of days 
                      for each Veteran.
                    - Sort these day counts and select the middle value (or the average of the two middle values if even).
                    - This measure minimizes the impact of extreme values to provide a central tendency.
                    """
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_final,
                file_name="veteran_data_processed.csv",
                mime="text/csv"
            )

        divider()

        # 6) Newly Identified Veterans
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Newly Identified Veterans**")
        with c2:
            st.metric(label="", value=f"{newly_identified_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
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
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_new,
                file_name="newly_identified_veterans.csv",
                mime="text/csv"
            )

        divider()

        # 7) Newly Identified Vets Entering GPD-Funded Transitional Housing
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Newly Identified Vets Entering GPD-Funded Transitional Housing**")
        with c2:
            st.metric(label="", value=f"{newly_identified_th_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
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
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_th_new,
                file_name="newly_identified_th_gpd_veterans.csv",
                mime="text/csv"
            )
    else:
        st.info("Please upload a CSV file to get started.")

if __name__ == "__main__":
    main()
