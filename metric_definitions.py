"""
Module containing metric definitions and calculation descriptions.

This module centralizes all the textual information about metrics used in the dashboard, 
including their descriptions, calculation details, and naming.
"""

def get_metric_definitions():
    """
    Returns a dictionary of all metric definitions used in the dashboard.
    
    Each metric has:
    - id: Unique identifier for the metric
    - title: Display title for the metric card
    - details: Detailed calculation explanation for the "Calculation Details" expansion
    - filename: Default filename for downloading the metric data
    """
    return {
        "A1": {
            "id": "A1",
            "title": "A1: Number of chronic & long-term Homeless Veterans who are not in permanent housing",
            "details": """
            **Definition:**  
            Number of chronic & long-term Homeless Veterans who are not in permanent housing.

            **Detailed Logic:**  
            - Veterans must meet HUD's definition of chronically homeless, which includes:
              * Having a disabling condition, AND
              * Either having been continuously homeless for 12+ months, OR
              * Having experienced 4+ episodes of homelessness in the last 3 years with a total duration of 12+ months
            - They must be currently active in the system during the reporting period.
            - They must not be in permanent housing, which means either:
              1. They are enrolled in a non-PH project type (Emergency Shelter, Transitional Housing, etc.), or
              2. They are enrolled in a PH project but do not have a Housing Move-in Date.
            - The calculation uses enrollment data with valid project start dates and examines the chronic homelessness determination flags.
            """,
            "filename": "chronic_vets_not_in_ph.csv"
        },
        
        "A2": {
            "id": "A2",
            "title": "A2: Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted",
            "details": """
            **Definition:**  
            Number of Chronic & Long-Term Homeless Veterans Offered a PH Intervention in the Last 2 Weeks Who Have Not Yet Accepted.

            **Detailed Logic:**  
            - Veterans must meet criteria for chronic homelessness (as defined in A1).
            - They must have received a permanent housing offer within the last 14 days from the reporting end date.
            - Their decision status must be "Decision Pending" (not yet accepted or declined).
            - They must not currently be in permanent housing.
            - The calculation examines the "Permanent Housing Offer", "Date of PH Offer", and "Did the Veteran accept or decline the offer?" fields to determine eligibility.
            """,
            "filename": "chronic_vets_ph_offer_pending.csv"
        },
        
        "A3": {
            "id": "A3",
            "title": "A3: Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need",
            "details": """
            **Definition:**  
            Number of Chronic & Long-Term Homeless Veterans that Entered a TH Program to Address a Clinical Need.

            **Detailed Logic:**  
            - Veterans must meet criteria for chronic homelessness (as defined in A1).
            - They must be currently enrolled in a Transitional Housing program.
            - The Transitional Housing program must be funded by one of the VA's Grant Per Diem funding sources:
              - VA: Grant Per Diem – Low Demand
              - VA: Grant Per Diem – Hospital to Housing
              - VA: Grant Per Diem – Clinical Treatment
              - VA: Grant Per Diem – Service Intensive Transitional Housing
            - The calculation examines the "Project Type Code" and "Funding Source" fields to determine eligibility.
            """,
            "filename": "chronic_vets_in_gpd_th.csv"
        },
        
        "A4": {
            "id": "A4",
            "title": "A4: Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for <90 Days Who Are Looking for Housing",
            "details": """
            **Definition:**  
            Number of Chronic & Long-Term Homeless Veterans Enrolled in a PH Program for <90 Days Who Are Looking for Housing.

            **Detailed Logic:**  
            - Veterans must meet criteria for chronic homelessness (as defined in A1).
            - They must be enrolled in a Permanent Housing program (PH project types).
            - Their enrollment must be less than 90 days old, calculated from the Project Start Date to the report end date.
            - They must not have a Housing Move-in Date yet (still looking for housing).
            - The calculation uses the "Project Start Date", "Project Type Code", and "Housing Move-in Date" fields.
            """,
            "filename": "chronic_vets_ph_not_housed.csv"
        },
        
        "Vets_Served": {
            "id": "Vets_Served",
            "title": "Total Number of Veterans Served",
            "details": """
            **Definition:**  
            Counts all unique Veteran clients with an active enrollment in TH, PH, CE, SH, SO, ES and Other(Veterans By Name List) during the past 90 days.

            **Detailed Logic:**  
            - **Reporting Period:** The last 90 days.
            - A Veteran is marked as active if:  
              1. Their Project Start Date is on or before today (reporting_period_end), and  
              2. Their Project Exit Date is either missing or occurs on/after the start of the 90-day window.  
            - Veterans are identified based on their "Veteran Status" = "Yes"
            - The calculation filters for valid project types including Transitional Housing, Coordinated Entry, PH types, Emergency Shelter, Street Outreach, Safe Haven, and the Veterans By Name List.
            - Final count is based on unique Client IDs.
            """,
            "filename": "veterans_served.csv"
        },
        
        "B1": {
            "id": "B1",
            "title": "B1: Number of Veterans Exited to or Moved Into Permanent Housing",
            "details": """
            **Definition:**  
            Counts Veterans who secured permanent housing during the reporting period, excluding those from GPD-Funded Transitional Housing.

            **Detailed Logic:**  
            - **Eligibility:** Veteran's record must have either:
              1. A valid Housing Move-in Date in a PH project within the 90-day reporting period, OR
              2. An exit to Permanent Housing destination within the 90-day reporting period.
            - Excludes enrollments where the Project Type is "Transitional Housing" with a Funding Source matching one of these GPD funds:  
              - VA: Grant Per Diem – Low Demand  
              - VA: Grant Per Diem – Hospital to Housing  
              - VA: Grant Per Diem – Clinical Treatment  
              - VA: Grant Per Diem – Service Intensive Transitional Housing  
            - **Final Count:** Each Veteran is counted only once, based on unique Client IDs.
            """,
            "filename": "ph_placements_th_excluded.csv"
        },
        
        "B2": {
            "id": "B2",
            "title": "B2: Average Days to Permanent Housing for Veterans (Goal 90 Days)",
            "details": """
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
            - Finally, the average is determined by taking the arithmetic mean of these day differences across all Veterans who were placed in permanent housing (excluding those from GPD-funded TH).
            """,
            "filename": "veterans_summary_days_to_ph.csv"
        },
        
        "B3": {
            "id": "B3",
            "title": "B3: Median Days to Permanent Housing for Veterans (Goal 90 Days)",
            "details": """
            **Definition:**  
            Finds the median value of the durations (in days) from the Date of Identification 
            to the Last Housing Event for Veterans.

            **Detailed Logic:**  
            - Follows the same steps as in the average calculation (B2) to compute the number of days 
              for each Veteran.
            - Veterans are only included if they were placed in permanent housing during the reporting period
              (excluding those from GPD-funded TH).
            - The days are sorted in ascending order, and the middle value is selected.
            - If there is an even number of Veterans, the median is calculated as the average of the two middle values.
            - This measure minimizes the impact of extreme values to provide a more representative central tendency.
            """,
            "filename": "veteran_data_processed.csv"
        },
        
        "C1": {
            "id": "C1",
            "title": "C1: Number of Veterans Exited to or Moved Into Permanent Housing",
            "details": """
            **Definition:**  
            Counts Veterans who secured permanent housing during the reporting period, excluding those from GPD-Funded Transitional Housing.

            **Detailed Logic:**  
            - This metric uses the same calculation as B1.
            - **Eligibility:** Veteran's record must have either:
              1. A valid Housing Move-in Date in a PH project within the 90-day reporting period, OR
              2. An exit to Permanent Housing destination within the 90-day reporting period.
            - Excludes enrollments where the Project Type is "Transitional Housing" with a Funding Source matching one of these GPD funds:  
              - VA: Grant Per Diem – Low Demand  
              - VA: Grant Per Diem – Hospital to Housing  
              - VA: Grant Per Diem – Clinical Treatment  
              - VA: Grant Per Diem – Service Intensive Transitional Housing  
            - **Final Count:** Each Veteran is counted only once, based on unique Client IDs.
            """,
            "filename": "ph_placements_th_excluded.csv"
        },
        
        "C2": {
            "id": "C2",
            "title": "C2: Number of Newly Identified Homeless Veterans",
            "details": """
            **Definition:**  
            Counts Veterans who are appearing for the first time (or after a gap of ≥90 days) 
            during the reporting period.

            **Detailed Logic:**  
            1. **Earliest Enrollment Date:** For each Veteran enrolled in the current 90-day window, determine the earliest enrollment date.  
            2. **Comparison with Prior Enrollments:** Compare this date against any historical enrollment for that Veteran:  
              - If no prior enrollment exists, then mark the Veteran as 'newly identified'.  
              - If no prior enrollment overlaps with the 90-day window before the earliest start date, then mark the Veteran as 'newly identified'.  
              - Otherwise, the Veteran is not considered newly identified.  
            3. The calculation examines the entire historical dataset to accurately identify Veterans who are truly new to the system or returning after a significant gap.
            4. Count each unique newly identified Veteran once.
            """,
            "filename": "newly_identified_veterans.csv"
        },
        
        "D1": {
            "id": "D1",
            "title": "D1: Number of Newly Identified Homeless Veterans Entering Transitional Housing",
            "details": """
            **Definition:**  
            Among the newly identified Veterans, counts those who enrolled in Transitional Housing 
            programs funded by GPD.

            **Detailed Logic:**  
            1. **Newly Identified Veterans:** Apply the same logic as in the 'C2: Number of Newly Identified Homeless Veterans' metric.  
            2. **Transitional Housing with GPD Funding:** Filter these newly identified Veterans to include only those who:  
              - Enrolled in Transitional Housing programs, and  
              - Have a Funding Source matching one of the GPD funds:  
                - VA: Grant Per Diem – Low Demand,  
                - VA: Grant Per Diem – Hospital to Housing,  
                - VA: Grant Per Diem – Clinical Treatment,  
                - VA: Grant Per Diem – Service Intensive Transitional Housing.
            3. The calculation examines the "Project Type Code" and "Funding Source" fields.
            4. Count each unique Veteran entering GPD-funded TH once.
            """,
            "filename": "newly_identified_th_gpd_veterans.csv"
        },
        
        "D2": {
            "id": "D2",
            "title": "D2: Number of Newly Identified Homeless Veterans",
            "details": """
            **Definition:**  
            Counts Veterans who are appearing for the first time (or after a gap of ≥90 days) 
            during the reporting period.

            **Detailed Logic:**  
            - This metric uses the same calculation as C2.
            1. **Earliest Enrollment Date:** For each Veteran enrolled in the current 90-day window, determine the earliest enrollment date.  
            2. **Comparison with Prior Enrollments:** Compare this date against any historical enrollment for that Veteran:  
              - If no prior enrollment exists, then mark the Veteran as 'newly identified'.  
              - If no prior enrollment overlaps with the 90-day window before the earliest start date, then mark the Veteran as 'newly identified'.  
              - Otherwise, the Veteran is not considered newly identified.  
            3. The calculation examines the entire historical dataset to accurately identify Veterans who are truly new to the system or returning after a significant gap.
            4. Count each unique newly identified Veteran once.
            """,
            "filename": "newly_identified_veterans.csv"
        }
    }