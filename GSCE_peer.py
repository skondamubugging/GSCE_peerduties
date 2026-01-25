import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from io import BytesIO
import os

# -------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Peer Duty Subject Assignment",
    layout="wide"
)

st.title("Peer Duty Subject Assignment System")

# -------------------------------------------------
# Week & Date Setup
# -------------------------------------------------
today = datetime.now()
week_seed = today.strftime("%Y-%U")

# Get Monday of the current week
week_monday = today - timedelta(days=today.weekday())

DAY_OFFSET = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

# -------------------------------------------------
# Excel File Path
# -------------------------------------------------
FILE_PATH = "Peer_Job_Fixedslots.xlsx"

if not os.path.exists(FILE_PATH):
    st.error("Required file `Peer_Job_Fixedslots.xlsx` not found.")
    st.stop()

st.markdown(
    f"""
    **Assignment Week:** {week_seed}  
    **Week Starting (Monday):** {week_monday.strftime("%d-%m-%Y")}
    """
)

# -------------------------------------------------
# Generate Assignment Button
# -------------------------------------------------
if st.button("Generate / Regenerate Weekly Assignment"):
    with st.spinner("Generating assignment..."):

        random.seed(week_seed)

        # -----------------------------
        # Load Excel Sheets
        # -----------------------------
        peerslots = pd.read_excel(FILE_PATH, sheet_name="Peerslots")
        busy_fac = pd.read_excel(FILE_PATH, sheet_name="Busy_fac")

        # -----------------------------
        # Filter FREE peer slots
        # -----------------------------
        peerslots = peerslots[
            peerslots["Status"].str.lower() == "free"
        ].copy()

        # -----------------------------
        # Assignment Logic
        # -----------------------------
        assigned_subjects = []
        assigned_faculty = []
        assignment_dates = []

        for _, peer in peerslots.iterrows():
            day = peer["Day"]
            time_slot = peer["Time Slot"]
            peer_emp_id = peer["Emp ID"]

            possible_subjects = busy_fac[
                (busy_fac["Day"] == day) &
                (busy_fac["Time Slot"] == time_slot) &
                (busy_fac["Emp ID"] != peer_emp_id)
            ]

            if not possible_subjects.empty:
                chosen = possible_subjects.sample(1).iloc[0]
                assigned_subjects.append(chosen["Subject"])
                assigned_faculty.append(chosen["Faculty Name"])
            else:
                assigned_subjects.append("No Subject Available")
                assigned_faculty.append("NA")

            # -----------------------------
            # Day → Date Mapping
            # -----------------------------
            day_key = str(day).strip().lower()
            if day_key in DAY_OFFSET:
                assignment_date = week_monday + timedelta(days=DAY_OFFSET[day_key])
                assignment_dates.append(assignment_date.strftime("%d-%m-%Y"))
            else:
                assignment_dates.append("Invalid Day")

        # -----------------------------
        # Update Result
        # -----------------------------
        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Observed Faculty"] = assigned_faculty
        peerslots["Assignment Date"] = assignment_dates
        peerslots["Assignment Week"] = week_seed

        # -----------------------------
        # Display Result
        # -----------------------------
        st.success("Assignment generated successfully.")
        st.dataframe(peerslots, use_container_width=True)

        # -----------------------------
        # Download
        # -----------------------------
        output = BytesIO()
        peerslots.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        filename = f"Peer_Duty_Assignment_Week_{week_seed}.xlsx"

        st.download_button(
            label="Download Assignment Excel",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
