import streamlit as st
import pandas as pd
import random
from datetime import datetime
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
# Date & Week Information
# -------------------------------------------------
generation_datetime = datetime.now()
generation_date_str = generation_datetime.strftime("%d-%m-%Y")
week_seed = generation_datetime.strftime("%Y-%U")

st.markdown(
    f"""
    **Generation Date:** {generation_date_str}  
    **Week ID:** {week_seed}
    """
)

# -------------------------------------------------
# Excel File Path (From GitHub Repo)
# -------------------------------------------------
FILE_PATH = "Peer_Job_Fixedslots.xlsx"

if not os.path.exists(FILE_PATH):
    st.error(
        "Required file `Peer_Job_Fixedslots.xlsx` not found in the repository."
    )
    st.stop()

st.success("Excel file loaded from repository.")

# -------------------------------------------------
# Generate Assignment Button
# -------------------------------------------------
if st.button("Generate / Regenerate Weekly Assignment"):
    with st.spinner("Generating assignment..."):

        # -----------------------------
        # Weekly Random Seed
        # -----------------------------
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
        # Update Result
        # -----------------------------
        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Observed Faculty"] = assigned_faculty

        # Add Date & Week Columns
        peerslots["Assignment Date"] = generation_date_str
        peerslots["Assignment Week"] = week_seed

        # -----------------------------
        # Display Result
        # -----------------------------
        st.success("Assignment generated successfully.")
        st.dataframe(peerslots, use_container_width=True)

        # -----------------------------
        # Prepare Download
        # -----------------------------
        output = BytesIO()
        peerslots.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        output_filename = (
            f"Peer_Duty_Assignment_{generation_date_str}_Week_{week_seed}.xlsx"
        )

        st.download_button(
            label="Download Assignment Excel",
            data=output,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
