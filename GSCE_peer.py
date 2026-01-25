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
# Generation Date (Anchor)
# -------------------------------------------------
generation_datetime = datetime.now()
base_date = generation_datetime.date()
week_seed = generation_datetime.strftime("%Y-%U")

st.markdown(
    f"""
    **Generation Date (Start Date):** {base_date.strftime("%d-%m-%Y")}  
    **Assignment ID (Week Seed):** {week_seed}
    """
)

# -------------------------------------------------
# Day Order Definition
# -------------------------------------------------
DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday",
             "friday", "saturday", "sunday"]

# -------------------------------------------------
# Excel File Path
# -------------------------------------------------
FILE_PATH = "Peer_Job_Fixedslots.xlsx"

if not os.path.exists(FILE_PATH):
    st.error("Required file `Peer_Job_Fixedslots.xlsx` not found.")
    st.stop()

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
        # Determine First Day in Data
        # -----------------------------
        first_day_value = str(peerslots.iloc[0]["Day"]).strip().lower()

        if first_day_value not in DAY_ORDER:
            st.error("Invalid Day value found in Peerslots sheet.")
            st.stop()

        first_day_index = DAY_ORDER.index(first_day_value)

        # -----------------------------
        # Assignment Logic
        # -----------------------------
        assigned_subjects = []
        assigned_faculty = []
        assignment_dates = []

        for _, peer in peerslots.iterrows():
            day = str(peer["Day"]).strip().lower()
            time_slot = peer["Time Slot"]
            peer_emp_id = peer["Emp ID"]

            possible_subjects = busy_fac[
                (busy_fac["Day"].str.lower() == day) &
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
            # Rolling Date Assignment
            # -----------------------------
            current_day_index = DAY_ORDER.index(day)
            day_offset = current_day_index - first_day_index
            assignment_date = base_date + timedelta(days=day_offset)
            assignment_dates.append(assignment_date.strftime("%d-%m-%Y"))

        # -----------------------------
        # Update Result
        # -----------------------------
        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Observed Faculty"] = assigned_faculty
        peerslots["Assignment Date"] = assignment_dates
        peerslots["Assignment ID"] = week_seed

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

        filename = f"Peer_Duty_Assignment_{base_date.strftime('%d-%m-%Y')}.xlsx"

        st.download_button(
            label="Download Assignment Excel",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
