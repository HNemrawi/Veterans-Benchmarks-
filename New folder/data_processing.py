import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional, Union, Callable
import streamlit as st

@st.cache_data
def process_data(df: pd.DataFrame) -> Tuple[
    pd.DataFrame,  # veterans_served_df
    pd.DataFrame,  # measure1_df
    pd.DataFrame,  # measure2_df
    pd.DataFrame,  # summary_df
    pd.DataFrame,  # df_doi
    int,           # total_veterans_served
    int,           # veterans_ph_placement_count
    int,           # filtered_veterans_count
    float,         # avg_days
    float,         # med_days
    pd.Timestamp,  # reporting_period_start
    pd.Timestamp,  # reporting_period_end
    List[str]      # allowed_project_types
]:
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
    # Constants
    DATE_COLUMNS = [
        "Project Start Date",
        "Project Exit Date",
        "Housing Move-in Date",
        "Approximate Date this Episode of Homelessness Started Date"
    ]
    ALLOWED_PROJECT_TYPES = [
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
    GPD_FUNDING_SOURCES = [
        "VA: Grant Per Diem – Low Demand",
        "VA: Grant Per Diem – Hospital to Housing",
        "VA: Grant Per Diem – Clinical Treatment",
        "VA: Grant Per Diem – Service Intensive Transitional Housing"
    ]
    FUTURE_DATE = pd.Timestamp("2099-12-31")  # Used for null exit dates

    # Create a copy to avoid modifying the original
    df_copy = df.copy()

    # Convert date columns to datetime
    for col in DATE_COLUMNS:
        if col in df_copy.columns:
            df_copy[col] = pd.to_datetime(df_copy[col], errors="coerce")

    # Trim whitespace on Project Type Code if needed
    if "Project Type Code" in df_copy.columns:
        df_copy["Project Type Code"] = df_copy["Project Type Code"].str.strip()

    # Define the 90-day reporting window
    reporting_period_end = pd.to_datetime("today").normalize()
    reporting_period_start = reporting_period_end - pd.Timedelta(days=89)

    # Step 1: Filter for "active" clients in the reporting period
    active_clients_mask = (
        (df_copy["Project Exit Date"].isna() | (df_copy["Project Exit Date"] >= reporting_period_start))
        & (df_copy["Project Start Date"] <= reporting_period_end)
    )
    served_clients = df_copy[active_clients_mask].copy()
    
    # Step 2: Filter for allowed project types
    project_type_mask = served_clients["Project Type Code"].isin(ALLOWED_PROJECT_TYPES)
    served_clients_filtered = served_clients[project_type_mask].copy()

    # Step 3: Clean text columns
    if "Is Last Enrollment in System (Yes / No)" in served_clients_filtered.columns:
        served_clients_filtered["Is Last Enrollment in System (Yes / No)"] = (
            served_clients_filtered["Is Last Enrollment in System (Yes / No)"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # Step 4: Keep only Veterans if "Veteran Status" is present
    if "Veteran Status" in served_clients_filtered.columns:
        veteran_mask = served_clients_filtered["Veteran Status"].astype(str).str.lower() == "yes"
        served_clients_filtered = served_clients_filtered[veteran_mask]

    # Calculate Metric 1: All veterans served in last 90 days
    veterans_served_df = _get_veterans_served(served_clients_filtered, reporting_period_end)
    total_veterans_served = veterans_served_df["Client ID"].nunique()

    # Calculate Metric 2: PH placement measures (no exclusion)
    measure1_df = _get_ph_placements(
        served_clients_filtered, 
        reporting_period_start, 
        reporting_period_end, 
        exclude_th=False,
        gpd_funding_sources=GPD_FUNDING_SOURCES
    )
    veterans_ph_placement_count = measure1_df["Client ID"].nunique()

    # Calculate Metric 3: PH placement measures (with TH exclusion)
    measure2_df = _get_ph_placements(
        served_clients_filtered, 
        reporting_period_start, 
        reporting_period_end, 
        exclude_th=True,
        gpd_funding_sources=GPD_FUNDING_SOURCES
    )
    filtered_veterans_count = measure2_df["Client ID"].nunique()

    # Calculate days to housing metrics
    filtered_client_ids = measure2_df["Client ID"].unique()
    filtered_original_df = df_copy[df_copy["Client ID"].isin(filtered_client_ids)].copy()
    
    # Process housing dates for filtered clients
    df_doi, summary_df = _process_housing_dates(
        filtered_original_df,
        reporting_period_start,
        reporting_period_end,
        ALLOWED_PROJECT_TYPES,
        FUTURE_DATE
    )
    
    # Calculate average and median days metrics
    avg_days = summary_df["Days Since Identification to Housing"].mean()
    med_days = summary_df["Days Since Identification to Housing"].median()

    return (
        veterans_served_df,
        measure1_df,
        measure2_df,
        summary_df,
        df_doi,
        total_veterans_served,
        veterans_ph_placement_count,
        filtered_veterans_count,
        avg_days,
        med_days,
        reporting_period_start,
        reporting_period_end,
        ALLOWED_PROJECT_TYPES
    )


def _get_veterans_served(df: pd.DataFrame, reporting_period_end: pd.Timestamp) -> pd.DataFrame:
    """
    Identifies veterans served in the reporting period.
    
    Args:
        df: DataFrame with veteran data
        reporting_period_end: End date of reporting period
        
    Returns:
        DataFrame with veterans served
    """
    # Non-PH projects are included by default
    non_ph_projects = ~df["Project Type Code"].str.startswith("PH –")
    
    # PH projects are included only if they don't have a move-in date or it's after the reporting period
    ph_project_condition = (
        df["Project Type Code"].str.startswith("PH –")
        & (
            df["Housing Move-in Date"].isna()
            | (df["Housing Move-in Date"] >= reporting_period_end)
        )
    )
    
    # Filter for "Other" project type (must be Veterans By Name List)
    other_or_veteran_list = (
        (df["Project Type Code"] != "Other")
        | (df.get("Name", "").eq("Veterans By Name List"))
    )
    
    # Combine all conditions
    veteran_served_filter = (non_ph_projects | ph_project_condition) & other_or_veteran_list
    
    return df[veteran_served_filter].copy()


def _get_ph_placements(
    df: pd.DataFrame, 
    start_date: pd.Timestamp, 
    end_date: pd.Timestamp, 
    exclude_th: bool = False,
    gpd_funding_sources: List[str] = None
) -> pd.DataFrame:
    """
    Identifies veterans placed in permanent housing.
    
    Args:
        df: DataFrame with veteran data
        start_date: Start date of reporting period
        end_date: End date of reporting period
        exclude_th: Whether to exclude GPD Transitional Housing
        gpd_funding_sources: List of GPD funding sources to exclude
        
    Returns:
        DataFrame with veterans placed in PH
    """
    # Condition 1: PH placement via Housing Move-in Date
    ph_movein_condition = (
        df["Project Type Code"].str.startswith("PH –")
        & (df["Housing Move-in Date"].notna())
        & (df["Housing Move-in Date"] >= start_date)
        & (df["Housing Move-in Date"] <= end_date)
    )
    
    # Condition 2: PH placement via exit to PH destination
    exit_to_ph_condition = (
        (df.get("Is Last Enrollment in System (Yes / No)", "no") == "yes")
        & (df.get("Destination Category", None) == "Permanent Housing Situations")
        & (df["Project Exit Date"].notna())
        & (df["Project Exit Date"] >= start_date)
        & (df["Project Exit Date"] <= end_date)
    )
    
    # Condition 3: Valid project type
    valid_project_condition = (
        (df["Project Type Code"] != "Other")
        | (df.get("Name", "").eq("Veterans By Name List"))
    )
    
    # Base filter for measure 1
    measure_filter = (ph_movein_condition | exit_to_ph_condition) & valid_project_condition
    
    # If excluding TH, add the exclusion condition
    if exclude_th and gpd_funding_sources:
        transitional_housing_exclusion = ~(
            (df["Project Type Code"] == "Transitional Housing")
            & (df.get("Funding Source", pd.Series([None]*len(df))).isin(gpd_funding_sources))
        )
        measure_filter = measure_filter & transitional_housing_exclusion
    
    return df[measure_filter].copy()


def _process_housing_dates(
    df: pd.DataFrame,
    reporting_period_start: pd.Timestamp,
    reporting_period_end: pd.Timestamp,
    allowed_project_types: List[str],
    future_date: pd.Timestamp
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Processes housing dates to calculate days from identification to housing.
    
    Args:
        df: DataFrame with veteran data
        reporting_period_start: Start date of reporting period
        reporting_period_end: End date of reporting period
        allowed_project_types: List of allowed project types
        future_date: Date to use for null exit dates
        
    Returns:
        Tuple of (detailed_df, summary_df)
    """
    # Find latest exit dates within reporting period
    exit_within_reporting = df[
        (df["Project Exit Date"].notna())
        & (df["Project Exit Date"] >= reporting_period_start)
        & (df["Project Exit Date"] <= reporting_period_end)
        & (df["Project Type Code"].isin(allowed_project_types))
    ]
    last_exit_map = exit_within_reporting.groupby("Client ID")["Project Exit Date"].max()
    df["Last Exit"] = df["Client ID"].map(last_exit_map)

    # Find latest move-in dates within reporting period
    movein_within_reporting = df[
        (df["Housing Move-in Date"].notna())
        & (df["Housing Move-in Date"] >= reporting_period_start)
        & (df["Housing Move-in Date"] <= reporting_period_end)
        & (df["Project Type Code"].isin(allowed_project_types))
    ]
    last_movein_map = movein_within_reporting.groupby("Client ID")["Housing Move-in Date"].max()
    df["Last Move-in"] = df["Client ID"].map(last_movein_map)

    # Deduplicate to avoid repeating the same enrollment
    df_deduped = df.drop_duplicates(subset=["Client ID", "Enrollment ID"], keep="first")

    df_doi = df_deduped.copy()
    df_doi["Project Start Date"] = pd.to_datetime(df_doi["Project Start Date"], errors="coerce")
    df_doi["Project Exit Date"] = pd.to_datetime(df_doi["Project Exit Date"], errors="coerce")
    df_doi = df_doi.sort_values(by=["Client ID", "Project Start Date"]).reset_index(drop=True)

    # Process episodes and identification dates
    df_doi = _identify_client_episodes(df_doi, future_date)

    # Calculate final housing event and days metrics
    df_doi["Last Housing Event"] = np.where(
        (df_doi["Last Move-in"].isna()) | (df_doi["Last Move-in"] < df_doi["Last Exit"]),
        df_doi["Last Exit"],
        df_doi["Last Move-in"]
    )

    df_doi["Days Since Identification to Housing"] = (
        df_doi["Last Housing Event"] - df_doi["Date of Identification"]
    ).dt.days

    # Create summary dataframe (one row per client)
    summary_df = df_doi[
        ["Client ID", "Last Exit", "Last Move-in", "Date of Identification", 
         "Last Housing Event", "Days Since Identification to Housing"]
    ].drop_duplicates(subset=["Client ID"], keep="first")

    return df_doi, summary_df


def _identify_client_episodes(df: pd.DataFrame, future_date: pd.Timestamp) -> pd.DataFrame:
    """
    Identifies client episodes and calculates Date of Identification.
    
    Args:
        df: DataFrame with client data
        future_date: Date to use for null exit dates
        
    Returns:
        DataFrame with Date of Identification calculated
    """
    # Initialize Date of Identification column
    df["Date of Identification"] = pd.NaT
    
    # Define function to merge enrollments into episodes
    def merge_enrollments(enrollments: pd.DataFrame) -> List[Dict[str, Any]]:
        episodes = []
        if enrollments.empty:
            return episodes

        current_start = enrollments.iloc[0]["Project Start Date"]
        current_end = enrollments.iloc[0]["Project Exit Date"]
        if pd.isna(current_end):
            current_end = future_date

        current_rows = [enrollments.index[0]]

        for i in range(1, len(enrollments)):
            row_idx = enrollments.index[i]
            start_i = enrollments.loc[row_idx, "Project Start Date"]
            end_i = enrollments.loc[row_idx, "Project Exit Date"]
            if pd.isna(end_i):
                end_i = future_date

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

    # Process each client to determine Date of Identification
    for cid, group in df.groupby("Client ID", sort=False):
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

        df.loc[group_sorted.index, "Date of Identification"] = date_of_identification

    return df


@st.cache_data
def calculate_newly_identified(
    rp_df: pd.DataFrame,
    full_df: pd.DataFrame,
    allowed_projects: List[str],
    reporting_period_start: pd.Timestamp
) -> Tuple[int, pd.DataFrame]:
    """
    Determines Veterans who are 'newly identified' within the 90-day reporting period.
    
    A Veteran is considered 'newly identified' if either:
    1. They have no prior enrollments in allowed project types before their earliest
       enrollment date in the reporting period, OR
    2. Any prior enrollments do not overlap with the 90-day period before their 
       earliest new enrollment.
    
    Parameters:
    -----------
    rp_df : DataFrame
        DataFrame containing enrollments within the reporting period
    full_df : DataFrame
        Complete DataFrame with all historical enrollments
    allowed_projects : list
        List of project types to consider for the analysis
    reporting_period_start : datetime
        Start date of the 90-day reporting period
        
    Returns:
    --------
    tuple: (int, DataFrame)
        Count of newly identified Veterans and their enrollment data
    """
    # Ensure date columns are datetime
    rp_df = rp_df.copy()
    rp_df["Project Start Date"] = pd.to_datetime(rp_df["Project Start Date"], errors="coerce")
    
    # Get earliest start date for each client in reporting period
    earliest_starts = rp_df.groupby("Client ID")["Project Start Date"].min().rename("Earliest_RP_Start")
    if earliest_starts.empty:
        return 0, pd.DataFrame()
        
    # Process full dataset for comparison
    clients_in_reporting_period = earliest_starts.index.tolist()
    full_df = full_df.copy()
    full_df["Project Start Date"] = pd.to_datetime(full_df["Project Start Date"], errors="coerce")
    full_df["Project Exit Date"] = pd.to_datetime(full_df["Project Exit Date"], errors="coerce")
    
    # Filter for allowed project types
    full_allowed_df = full_df[full_df["Project Type Code"].isin(allowed_projects)].copy()
    
    # Keep all project types for overlap check
    full_any_df = full_df.copy()
    
    newly_identified_clients = []
    
    for client_id in clients_in_reporting_period:
        earliest_rp_start = earliest_starts.loc[client_id]
        
        # Check if client has any prior enrollments in allowed project types
        prior_allowed = full_allowed_df[
            (full_allowed_df["Client ID"] == client_id) &
            (full_allowed_df["Project Start Date"] < earliest_rp_start)
        ]
        
        # If no prior enrollments, they're newly identified
        if prior_allowed.empty:
            newly_identified_clients.append(client_id)
            continue
            
        # Check if any prior enrollment overlaps with 90-day window before earliest start
        prior_any = full_any_df[
            (full_any_df["Client ID"] == client_id) &
            (full_any_df["Project Start Date"] < earliest_rp_start)
        ]
        
        # Define 90-day window before earliest start
        window_start = earliest_rp_start - pd.Timedelta(days=90)
        
        # Check for overlap with 90-day window
        has_overlap = False
        for _, row in prior_any.iterrows():
            end_date = row["Project Exit Date"] if pd.notna(row["Project Exit Date"]) else pd.Timestamp("2099-12-31")
            if end_date >= window_start:
                has_overlap = True
                break
                
        # If no overlap found, client is newly identified
        if not has_overlap:
            newly_identified_clients.append(client_id)
    
    # Create final dataframe with only newly identified clients
    newly_identified_df = rp_df[rp_df["Client ID"].isin(newly_identified_clients)].copy()
    
    return len(newly_identified_clients), newly_identified_df
    
    
def fallback_column(primary_col: pd.Series, backup_col: pd.Series) -> pd.Series:
    """
    Returns values from primary column if available, otherwise from backup column.
    
    Args:
        primary_col: Primary data source column
        backup_col: Backup data source column to use when primary has missing values
        
    Returns:
        Combined series with primary values where available, backup values elsewhere
    """
    if primary_col is None and backup_col is None:
        return pd.Series([None])
    
    if primary_col is None:
        return backup_col
    
    if backup_col is None:
        return primary_col
    
    # Use primary where available, otherwise use backup
    result = primary_col.copy()
    mask = result.isna() | (result == '')
    result.loc[mask] = backup_col.loc[mask]
    return result


def is_chronically_homeless(df: pd.DataFrame, rpend: pd.Timestamp) -> pd.Series:
    """
    Determine chronic homelessness using PIT flag or historical patterns.
    
    Args:
        df: DataFrame with veteran data
        rpend: End date of reporting period (usually today)
        
    Returns:
        Boolean Series indicating chronic homelessness status for each record
    """
    # Get primary and fallback columns for chronic homelessness determination
    prior_residence = fallback_column(
        df.get("Residence Prior to Project Entry.1", None), 
        df.get("Residence Prior to Project Entry", None)
    )
    
    duration_text = fallback_column(
        df.get("Length of Stay in Prior Living Situation.1", None), 
        df.get("Length of Stay in Prior Living Situation", None)
    )
    
    chronic_2 = fallback_column(
        df.get("Times Homeless in the Past Three Years.1", None), 
        df.get("Times Homeless in the Past Three Years", None)
    )
    
    chronic_3 = fallback_column(
        df.get("Total Months Homeless in Past Three Years.1", None), 
        df.get("Total Months Homeless in Past Three Years", None)
    )
    
    chronic_7_cols = [
        df.get("Approximate Date this Episode of Homelessness Started Date.1", None), 
        df.get("Approximate Date this Episode of Homelessness Started Date", None)
    ]
    chronic_7 = pd.to_datetime(
        fallback_column(*[col for col in chronic_7_cols if col is not None]),
        errors="coerce"
    )
    
    # Calculate exit date or use reporting period end
    exit_or_end = df["Project Exit Date"].fillna(rpend)
    
    # Define chronic homelessness conditions
    homeless_prior = prior_residence.isin([
        "Place not meant for habitation (e.g., a vehicle, an abandoned building, bus/train/subway station/airport or anywhere outside)",
        "Emergency shelter, including hotel or motel paid for with emergency shelter voucher, Host Home shelter",
        "Safe Haven", "Transitional housing for homeless persons (including homeless youth)"
    ])
    
    duration_long = duration_text == "One year or longer"
    duration_365 = (exit_or_end - chronic_7).dt.days > 365
    episodic_chronic = (chronic_2 == "Four or more times") & (chronic_3 == "More than 12 Months")
    
    # Combine conditions for chronic homelessness determination
    chronic_logic = homeless_prior & (duration_long | duration_365 | episodic_chronic)
    
    # Use either PIT flag or calculated chronic status
    return (df.get("Chronically Homeless at PIT/Current Date - Household", pd.Series([None] * len(df))) == "Yes") | chronic_logic


def calculate_chronic_metrics(
    df: pd.DataFrame, 
    reporting_period_start: pd.Timestamp, 
    reporting_period_end: pd.Timestamp
) -> Dict[str, Tuple[int, pd.DataFrame]]:
    """
    Calculate A1 to A4 metrics related to chronically homeless veterans.
    
    Args:
        df: DataFrame with veteran data
        reporting_period_start: Start date of reporting period
        reporting_period_end: End date of reporting period
        
    Returns:
        Dictionary with A1-A4 metrics and their corresponding DataFrames
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Allowed project types
    allowed_project_types = [
        "Transitional Housing", "Coordinated Entry", "PH – Rapid Re-Housing",
        "PH – Permanent Supportive Housing (disability required for entry)",
        "Emergency Shelter – Night-by-Night", "Emergency Shelter – Entry Exit",
        "Other", "Street Outreach", "PH – Housing Only",
        "PH – Housing with Services (no disability required for entry)", "Safe Haven"
    ]

    # GPD-funded TH projects
    gpd_funding_sources = [
        "VA: Grant Per Diem – Low Demand",
        "VA: Grant Per Diem – Hospital to Housing",
        "VA: Grant Per Diem – Clinical Treatment",
        "VA: Grant Per Diem – Service Intensive Transitional Housing"
    ]

    # Normalize dates
    for date_col in ["Project Start Date", "Project Exit Date", "Housing Move-in Date"]:
        if date_col in df_copy.columns:
            df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")

    # Chronic flag determination
    chronic_flag = is_chronically_homeless(df_copy, reporting_period_end)

    # Common conditions
    is_ph = df_copy["Project Type Code"].str.startswith("PH –")
    no_movein = df_copy["Housing Move-in Date"].isna() | (df_copy["Housing Move-in Date"] >= reporting_period_end)
    in_non_ph_or_unhoused = ~is_ph | (is_ph & no_movein)
    allowed_projects = df_copy["Project Type Code"].isin(allowed_project_types)
    active_reporting = (
        (df_copy["Project Exit Date"].isna() | (df_copy["Project Exit Date"] >= reporting_period_start)) &
        (df_copy["Project Start Date"] <= reporting_period_end)
    )
    valid_projects = (df_copy["Project Type Code"] != "Other") | (df_copy.get("Name", "") == "Veterans By Name List")

    # A1: Chronic Vets not in PH
    a1_filter = in_non_ph_or_unhoused & allowed_projects & active_reporting & valid_projects & chronic_flag
    a1_df = df_copy[a1_filter].copy()

    # A2: PH Offer in last 2 weeks and pending
    offer_col = df_copy.get("Permanent Housing Offer", pd.Series([None] * len(df_copy)))
    offer_date = pd.to_datetime(df_copy.get("Date of PH Offer", pd.Series([None] * len(df_copy))), errors="coerce")
    offer_status = df_copy.get("Did the Veteran accept or decline the offer?", pd.Series([None] * len(df_copy)))
    
    offered_recently_pending = (
        offer_col.notna() &
        (offer_col != "Permanent Housing Not Offered Yet") &
        (offer_date >= reporting_period_end - pd.Timedelta(days=13)) &
        (offer_status == "Decision Pending")
    )
    a2_filter = allowed_projects & active_reporting & valid_projects & in_non_ph_or_unhoused & chronic_flag & offered_recently_pending
    a2_df = df_copy[a2_filter].copy()

    # A3: Chronic vets active in GPD-funded TH
    is_th = df_copy["Project Type Code"] == "Transitional Housing"
    has_gpd_funding = df_copy.get("Funding Source", pd.Series([None] * len(df_copy))).isin(gpd_funding_sources)
    a3_filter = is_th & has_gpd_funding & active_reporting & chronic_flag
    a3_df = df_copy[a3_filter].copy()

    # A4: Chronic Vets in PH < 90 days, not yet moved in
    enrolled_days = (reporting_period_end - df_copy["Project Start Date"]).dt.days
    a4_filter = (
        is_ph & (enrolled_days < 90) &
        no_movein & chronic_flag & active_reporting
    )
    a4_df = df_copy[a4_filter].copy()

    return {
        "A1": (a1_df["Client ID"].nunique(), a1_df),
        "A2": (a2_df["Client ID"].nunique(), a2_df),
        "A3": (a3_df["Client ID"].nunique(), a3_df),
        "A4": (a4_df["Client ID"].nunique(), a4_df),
    }