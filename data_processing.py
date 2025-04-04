import pandas as pd
import numpy as np
from datetime import datetime  # removed unused "timedelta"
import streamlit as st

@st.cache_data
def process_data(df):
    """
    Core data transformations for the 90-day reporting window, focusing on Veterans
    in certain project types.

    Returns a tuple of:
      1) veterans_served_df         - All veterans served in last 90 days
      2) measure1_df                - Veterans placed in PH (no TH exclusion)
      3) measure2_df                - Veterans placed in PH (excluding GPD TH)
      4) summary_df                 - Summary of days from ID to housing (one row per client)
      5) df_doi                     - More detailed DataFrame used in calculations
      6) total_veterans_served      - Count of unique vets served in last 90 days
      7) veterans_ph_placement_count- Count placed in PH (no TH exclusion)
      8) filtered_veterans_count    - Count placed in PH (excluding GPD TH)
      9) avg_days                   - Average days from ID to housing
      10) med_days                  - Median days from ID to housing
      11) reporting_period_start    - 90 days prior to 'today'
      12) reporting_period_end      - 'today'
      13) allowed_project_types     - The recognized project types for filtering
    """

    # Convert date columns to datetime
    date_columns = [
        "Project Start Date",
        "Project Exit Date",
        "Housing Move-in Date",
        "Approximate Date this Episode of Homelessness Started Date"
    ]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Trim whitespace on Project Type Code if needed
    if "Project Type Code" in df.columns:
        df["Project Type Code"] = df["Project Type Code"].str.strip()

    # Define the 90-day reporting window
    reporting_period_end = pd.to_datetime("today").normalize()
    reporting_period_start = reporting_period_end - pd.Timedelta(days=89)

    # List allowed project types
    allowed_project_types = [
        "Transitional Housing",
        "Coordinated Entry",
        "PH – Rapid Re-Housing",
        "PH – Permanent Supportive Housing (disability required for entry)",
        "Emergency Shelter – Night-by-Night",
        "Emergency Shelter – Entry Exit",
        "Other",
        "Street Outreach",
        "PH – Housing Only",
        "PH – Housing with Services (no disability required for entry)",
        "Safe Haven"
    ]

    # Filter: clients "active" in last 90 days
    served_clients = df[
        (df["Project Exit Date"].isna() | (df["Project Exit Date"] >= reporting_period_start))
        & (df["Project Start Date"] <= reporting_period_end)
    ]
    served_clients_filtered = served_clients[
        served_clients["Project Type Code"].isin(allowed_project_types)
    ].copy()

    # Clean text columns
    if "Is Last Enrollment in System (Yes / No)" in served_clients_filtered.columns:
        served_clients_filtered["Is Last Enrollment in System (Yes / No)"] = (
            served_clients_filtered["Is Last Enrollment in System (Yes / No)"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # Keep only Veterans if "Veteran Status" is present
    if "Veteran Status" in served_clients_filtered.columns:
        served_clients_filtered = served_clients_filtered[
            served_clients_filtered["Veteran Status"].astype(str).str.lower() == "yes"
        ]

    # 1) All veterans served in last 90 days
    non_ph_projects = ~served_clients_filtered["Project Type Code"].str.startswith("PH –")
    ph_project_movein_condition = (
        served_clients_filtered["Project Type Code"].str.startswith("PH –")
        & (
            served_clients_filtered["Housing Move-in Date"].isna()
            | (served_clients_filtered["Housing Move-in Date"] >= reporting_period_end)
        )
    )
    other_or_veteran_list = (
        (served_clients_filtered["Project Type Code"] != "Other")
        | (served_clients_filtered.get("Name", "").eq("Veterans By Name List"))
    )
    veteran_served_filter = (non_ph_projects | ph_project_movein_condition) & other_or_veteran_list
    veterans_served_df = served_clients_filtered[veteran_served_filter].copy()
    total_veterans_served = veterans_served_df["Client ID"].nunique()

    # 2) PH placement measures
    ph_movein_condition = (
        served_clients_filtered["Project Type Code"].str.startswith("PH –")
        & (served_clients_filtered["Housing Move-in Date"].notna())
        & (served_clients_filtered["Housing Move-in Date"] >= reporting_period_start)
        & (served_clients_filtered["Housing Move-in Date"] <= reporting_period_end)
    )
    exit_to_ph_condition = (
        (served_clients_filtered.get("Is Last Enrollment in System (Yes / No)", "no") == "yes")
        & (served_clients_filtered.get("Destination Category", None) == "Permanent Housing Situations")
        & (served_clients_filtered["Project Exit Date"].notna())
        & (served_clients_filtered["Project Exit Date"] >= reporting_period_start)
        & (served_clients_filtered["Project Exit Date"] <= reporting_period_end)
    )
    valid_project_condition = (
        (served_clients_filtered["Project Type Code"] != "Other")
        | (served_clients_filtered.get("Name", "").eq("Veterans By Name List"))
    )
    excluded_funding_sources = [
        "VA: Grant Per Diem – Low Demand",
        "VA: Grant Per Diem – Hospital to Housing",
        "VA: Grant Per Diem – Clinical Treatment",
        "VA: Grant Per Diem – Service Intensive Transitional Housing"
    ]
    transitional_housing_exclusion = ~(
        (served_clients_filtered["Project Type Code"] == "Transitional Housing")
        & (served_clients_filtered.get("Funding Source", pd.Series([None]*len(served_clients_filtered))).isin(excluded_funding_sources))
    )

    measure1_filter = (ph_movein_condition | exit_to_ph_condition) & valid_project_condition
    measure1_df = served_clients_filtered[measure1_filter].copy()
    veterans_ph_placement_count = measure1_df["Client ID"].nunique()

    measure2_filter = measure1_filter & transitional_housing_exclusion
    filtered_veterans_df = served_clients_filtered[measure2_filter].copy()
    filtered_veterans_count = filtered_veterans_df["Client ID"].nunique()

    # Build final data for measure #2
    filtered_client_ids = filtered_veterans_df["Client ID"].unique()
    filtered_original_df = df[df["Client ID"].isin(filtered_client_ids)].copy()

    exit_within_reporting = filtered_original_df[
        (filtered_original_df["Project Exit Date"].notna())
        & (filtered_original_df["Project Exit Date"] >= reporting_period_start)
        & (filtered_original_df["Project Exit Date"] <= reporting_period_end)
        & (filtered_original_df["Project Type Code"].isin(allowed_project_types))
    ]
    last_exit_map = exit_within_reporting.groupby("Client ID")["Project Exit Date"].max()
    filtered_original_df["Last Exit"] = filtered_original_df["Client ID"].map(last_exit_map)

    movein_within_reporting = filtered_original_df[
        (filtered_original_df["Housing Move-in Date"].notna())
        & (filtered_original_df["Housing Move-in Date"] >= reporting_period_start)
        & (filtered_original_df["Housing Move-in Date"] <= reporting_period_end)
        & (filtered_original_df["Project Type Code"].isin(allowed_project_types))
    ]
    last_movein_map = movein_within_reporting.groupby("Client ID")["Housing Move-in Date"].max()
    filtered_original_df["Last Move-in"] = filtered_original_df["Client ID"].map(last_movein_map)

    # Deduplicate to avoid repeating the same enrollment
    filtered_original_df = filtered_original_df.drop_duplicates(subset=["Client ID", "Enrollment ID"], keep="first")

    df_doi = filtered_original_df.copy()
    df_doi["Project Start Date"] = pd.to_datetime(df_doi["Project Start Date"], errors="coerce")
    df_doi["Project Exit Date"] = pd.to_datetime(df_doi["Project Exit Date"], errors="coerce")
    df_doi = df_doi.sort_values(by=["Client ID", "Project Start Date"]).reset_index(drop=True)

    # Merge consecutive enrollments into episodes
    def merge_enrollments(enrollments):
        episodes = []
        if enrollments.empty:
            return episodes

        current_start = enrollments.iloc[0]["Project Start Date"]
        current_end = enrollments.iloc[0]["Project Exit Date"]
        if pd.isna(current_end):
            current_end = pd.Timestamp("2099-12-31")

        current_rows = [enrollments.index[0]]

        for i in range(1, len(enrollments)):
            row_idx = enrollments.index[i]
            start_i = enrollments.loc[row_idx, "Project Start Date"]
            end_i = enrollments.loc[row_idx, "Project Exit Date"]
            if pd.isna(end_i):
                end_i = pd.Timestamp("2099-12-31")

            # Overlap or touch => extend
            if start_i <= (current_end + pd.Timedelta(days=1)):
                if end_i > current_end:
                    current_end = end_i
                current_rows.append(row_idx)
            else:
                episodes.append({
                    "episode_start": current_start,
                    "episode_end": current_end,
                    "row_ids": current_rows
                })
                current_start = start_i
                current_end = end_i
                current_rows = [row_idx]

        episodes.append({
            "episode_start": current_start,
            "episode_end": current_end,
            "row_ids": current_rows
        })
        return episodes

    df_doi["Date of Identification"] = pd.NaT
    for cid, group in df_doi.groupby("Client ID", sort=False):
        group_sorted = group.sort_values("Project Start Date")
        episodes = merge_enrollments(group_sorted)

        date_of_identification = None
        previous_end = None

        for i, ep in enumerate(episodes):
            ep_start = ep["episode_start"]
            ep_end = ep["episode_end"]

            if i == 0:
                date_of_identification = ep_start
            else:
                # If there's a gap >= 90 days between episodes, that's a new "Date of Identification"
                gap_days = (ep_start - previous_end).days if previous_end else 9999
                if gap_days >= 90:
                    date_of_identification = ep_start

            previous_end = ep_end

        df_doi.loc[group_sorted.index, "Date of Identification"] = date_of_identification

    df_doi["Last Housing Event"] = np.where(
        (df_doi["Last Move-in"].isna()) | (df_doi["Last Move-in"] < df_doi["Last Exit"]),
        df_doi["Last Exit"],
        df_doi["Last Move-in"]
    )

    df_doi["Days Since Identification to Housing"] = (
        df_doi["Last Housing Event"] - df_doi["Date of Identification"]
    ).dt.days

    summary_df = df_doi[[
        "Client ID",
        "Last Exit",
        "Last Move-in",
        "Date of Identification",
        "Last Housing Event",
        "Days Since Identification to Housing"
    ]].drop_duplicates(subset=["Client ID"], keep="first")

    avg_days = summary_df["Days Since Identification to Housing"].mean()
    med_days = summary_df["Days Since Identification to Housing"].median()

    return (
        veterans_served_df,
        measure1_df,
        filtered_veterans_df,
        summary_df,
        df_doi,
        total_veterans_served,
        veterans_ph_placement_count,
        filtered_veterans_count,
        avg_days,
        med_days,
        reporting_period_start,
        reporting_period_end,
        allowed_project_types
    )

@st.cache_data
def calculate_newly_identified(
    rp_df,
    full_df,
    allowed_projects,
    reporting_period_start
):
    """
    Determines how many clients in 'rp_df' are 'newly identified' within the 90-day window.
    A client is 'newly identified' if:
      (a) They have no prior enrollments in allowed project types before their earliest
          new enrollment date in 'rp_df', OR
      (b) Any prior enrollment does not overlap the 90 days before that earliest new enrollment.
    """
    rp_df["Project Start Date"] = pd.to_datetime(rp_df["Project Start Date"], errors="coerce")

    earliest_starts = rp_df.groupby("Client ID")["Project Start Date"].min().rename("Earliest_RP_Start")
    if earliest_starts.empty:
        return 0, pd.DataFrame()

    clients_in_reporting_period = earliest_starts.index.unique()

    # Full dataset of "allowed" for checking prior enrollments
    full_allowed_df = full_df.copy()
    full_allowed_df["Project Start Date"] = pd.to_datetime(full_allowed_df["Project Start Date"], errors="coerce")
    full_allowed_df["Project Exit Date"] = pd.to_datetime(full_allowed_df["Project Exit Date"], errors="coerce")
    full_allowed_df = full_allowed_df[full_allowed_df["Project Type Code"].isin(allowed_projects)]

    # Also consider ANY project type for overlap checks
    full_any_df = full_df.copy()
    full_any_df["Project Start Date"] = pd.to_datetime(full_any_df["Project Start Date"], errors="coerce")
    full_any_df["Project Exit Date"] = pd.to_datetime(full_any_df["Project Exit Date"], errors="coerce")

    newly_identified_clients = []

    for client_id in clients_in_reporting_period:
        earliest_rp_start = earliest_starts.loc[client_id]

        # (a) No prior enrollments in allowed types
        prior_allowed = full_allowed_df[
            (full_allowed_df["Client ID"] == client_id)
            & (full_allowed_df["Project Start Date"] < earliest_rp_start)
        ]
        if prior_allowed.empty:
            newly_identified_clients.append(client_id)
            continue

        # (b) If prior allowed enrollments exist, see if ANY earlier enrollment
        #     overlaps with the 90 days before earliest_rp_start
        prior_any = full_any_df[
            (full_any_df["Client ID"] == client_id)
            & (full_any_df["Project Start Date"] < earliest_rp_start)
        ]
        window_start = earliest_rp_start - pd.Timedelta(days=90)

        def overlaps_90_days(row):
            eend = row["Project Exit Date"] if pd.notna(row["Project Exit Date"]) else pd.Timestamp("2099-12-31")
            estart = row["Project Start Date"]
            return (estart < earliest_rp_start) and (eend >= window_start)

        # If no overlap, they are newly identified
        if not any(overlaps_90_days(row) for _, row in prior_any.iterrows()):
            newly_identified_clients.append(client_id)

    newly_identified_df = rp_df[rp_df["Client ID"].isin(newly_identified_clients)].copy()
    newly_identified_count = len(pd.unique(newly_identified_clients))

    return newly_identified_count, newly_identified_df
