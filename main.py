import streamlit as st 
import pandas as pd
from styling import apply_custom_css, style_metric_cards, divider
from data_processing import process_data, calculate_newly_identified

@st.cache_data
def load_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    # Convert ID columns to numeric, ignoring errors
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

    # CSV Upload
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        if "original_df" not in st.session_state:
            st.session_state.original_df = load_csv(uploaded_file)
        original_df = st.session_state.original_df

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
            df_filtered = filter_data(original_df, selected_program_coc, selected_local_coc)
        else:
            df_filtered = original_df

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
            Deduplicates each DataFrame on ["Client ID","Enrollment ID"] if both exist.
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
        # Display Metrics & Download Buttons
        # ----------------------------------------------------------------------

        # 1) Number of Veterans Served
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
                    This measure counts all unique Veteran clients who are ‘active’ at any
                    point within the past 90 days.

                    **Logic:**  
                    1. The reporting window is from 90 days ago up to today.  
                    2. A client is considered active if their exit date is not before
                       the start of the 90-day window, or if they started a project
                       during this window.  
                    3. Only Veteran clients (where “Veteran Status = Yes”) in allowed
                       project types are included.  
                    4. Each unique Client ID is counted once.
                    """
                )
        with c4:
            st.download_button(
                label="⬇️ Download Data",
                data=csv_vets_served,
                file_name="veterans_served.csv",
                mime="text/csv"
            )

        divider()

        # 2) Veterans Placed in PH (No TH Exclusion)
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Veterans Placed in PH (No TH Exclusion)**")
        with c2:
            st.metric(label="", value=f"{veterans_ph_placement_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Counts Veterans who obtained permanent housing (PH)
                    within the 90-day window, without excluding any TH origin.

                    **Logic:**  
                    1. Includes Veterans who had a Housing Move-in Date in a PH project
                       during the last 90 days, **or** exited a project to a
                       Permanent Housing destination during the same period.  
                    2. We do **not** exclude placements that originated in GPD
                       Transitional Housing.  
                    3. Each unique Client ID is counted once.
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

        # 3) Veterans Placed in PH (Excluding GPD TH)
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Veterans Placed in PH (Excluding GPD TH)**")
        with c2:
            st.metric(label="", value=f"{filtered_veterans_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    Similar to “Veterans Placed in PH (No TH Exclusion)”
                    but excludes Veterans who originated in GPD-funded TH.

                    **Logic:**  
                    1. Start with Veterans who meet the PH placement conditions.  
                    2. Remove those with a relevant GPD TH enrollment.  
                    3. Ensures the PH placement was not from a GPD TH path.
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
                    How many days, on average, from the “Date of Identification”
                    (start of homeless episode) to the latest housing event (move-in or exit).

                    **Logic:**  
                    1. A new “episode” starts if there’s a 90+ day gap between enrollments.  
                    2. “Last Housing Event” is the maximum of Housing Move-in or Exit Date.  
                    3. Calculate (Last Housing Event - Date of Identification) for each Veteran,
                       then average these values across all Veterans.
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
                    The middle value (median) for how many days from the Date of Identification
                    to the Last Housing Event.

                    **Logic:**  
                    1. Uses the same “Date of Identification” and “Last Housing Event”
                       as the Average Days metric.  
                    2. Instead of averaging, we sort all day counts and pick the middle one.  
                    3. This can be less influenced by extremely high or low outliers.
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
                    Veterans who had no overlapping or ongoing enrollments in the 90 days prior to their earliest new enrollment
                    (i.e., the enrollment with the earliest Project Start Date within the 90-day window is kept).

                    **Logic:**  
                    1. We identify the earliest Project Start Date within the 90-day window for each Veteran.
                    2. That enrollment is used for the measure and included in the download.
                    3. All such Veterans are counted once.
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

        # 7) Newly Identified Vets Entering GPD TH
        c1, c2, c3, c4 = st.columns([1.2, 0.6, 2, 1])
        with c1:
            st.write("**Newly Identified Vets Entering GPD TH**")
        with c2:
            st.metric(label="", value=f"{newly_identified_th_count}")
        with c3:
            with st.expander("Calculation Details", expanded=False):
                st.write(
                    """
                    **Definition:**  
                    This metric represents a subset of Newly Identified Veterans. It includes those Veterans who, in addition to being newly identified (i.e., having no overlapping or ongoing enrollments in the 90 days prior to their earliest new enrollment), have an enrollment where the project type is "Transitional Housing" and the funding source is one of the following:
                    - VA: Grant Per Diem – Low Demand
                    - VA: Grant Per Diem – Hospital to Housing
                    - VA: Grant Per Diem – Clinical Treatment
                    - VA: Grant Per Diem – Service Intensive Transitional Housing

                    **Logic:**  
                    1. Start with the pool of Newly Identified Veterans.  
                    2. From this pool, select only those enrollments that are for Transitional Housing and have a funding source matching one of the specified GPD funding sources.  
                    3. The count of these records represents the metric.
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
