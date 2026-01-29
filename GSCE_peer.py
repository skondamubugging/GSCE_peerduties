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
    page_title="GSCE - Peer to Peer Duties Assignment for One Week",
    layout="wide"
)

st.image("gitm.png", width=150)

st.title("GSCE - Peer to Peer Duties Assignment")

st.markdown("""
This system generates **weekly peer duty subject assignments**
using a deterministic random seed.
Each subject is assigned **only once per week**.
""")

# -------------------------------------------------
# Excel File Path (From GitHub Repo)
# -------------------------------------------------
FILE_PATH = "Peer_Job_Fixedslots_withoutsecondperson.xlsx"

if not os.path.exists(FILE_PATH):
    st.error(
        "Required file `Peer_Job_Fixedslots_withoutsecondperson.xlsx` not found in the repository."
    )
    st.stop()

st.success("Excel file loaded from repository.")

# -------------------------------------------------
# Day Selection
# -------------------------------------------------
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
selected_day = st.selectbox("Select Day", days)

# -------------------------------------------------
# Generate Assignment Button
# -------------------------------------------------
if st.button("Generate / Regenerate Day-wise Assignment"):
    with st.spinner("Generating assignment..."):

        # -----------------------------
        # Load Excel Sheets
        # -----------------------------
        peerslots = pd.read_excel(FILE_PATH, sheet_name="Peerslots")
        busy_fac = pd.read_excel(FILE_PATH, sheet_name="Busy_fac")

        # -----------------------------
        # Filter FREE peer slots (Day-wise)
        # -----------------------------
        peerslots = peerslots[
            (peerslots["Status"].str.lower() == "free") &
            (peerslots["Day"] == selected_day)
        ].copy()

        if peerslots.empty:
            st.warning(f"No free peer slots found for {selected_day}")
            st.stop()

        # -----------------------------
        # Weekly + Day Seed (Deterministic)
        # -----------------------------
        week_seed = datetime.now().strftime("%Y-%U")
        random.seed(f"{week_seed}-{selected_day}")

        # -----------------------------
        # Assignment Logic
        # Subject assigned only once per week
        # -----------------------------
        assigned_subjects = []
        assigned_faculty = []
        assigned_building = []
        assigned_room = []

        weekly_assigned_subjects = set()

        for _, peer in peerslots.iterrows():
            time_slot = peer["Time Slot"]
            peer_emp_id = peer["Emp ID"]

            possible_subjects = busy_fac[
                (busy_fac["Day"] == selected_day) &
                (busy_fac["Time Slot"] == time_slot) &
                (busy_fac["Emp ID"] != peer_emp_id) &
                (busy_fac["Status"].str.lower() == "busy") &
                (~busy_fac["Subject"].isin(weekly_assigned_subjects))
            ]

            if not possible_subjects.empty:
                chosen = possible_subjects.sample(1).iloc[0]

                assigned_subjects.append(chosen["Subject"])
                assigned_faculty.append(chosen["Faculty Name"])
                assigned_building.append(chosen["Building"])
                assigned_room.append(chosen["Room No."])

                weekly_assigned_subjects.add(chosen["Subject"])
            else:
                assigned_subjects.append("No Subject Available")
                assigned_faculty.append("NA")
                assigned_building.append("NA")
                assigned_room.append("NA")


        # -----------------------------
        # Update Result
        # -----------------------------
        peerslots["Assigned Subject"] = assigned_subjects
        peerslots["Teaching Faculty"] = assigned_faculty
        peerslots["Building"] = assigned_building
        peerslots["Room No."] = assigned_room

        # -----------------------------
        # Display Result
        # -----------------------------
        st.success(f"{selected_day} Assignment generated for Week: {week_seed}")
        st.dataframe(peerslots, use_container_width=True)

        # -----------------------------
        # Prepare Download
        # -----------------------------
        output = BytesIO()
        peerslots.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        output_filename = f"Peer_Duty_Assignment_{selected_day}_Week_{week_seed}.xlsx"

        st.download_button(
            label="Download Day-wise Assignment Excel",
            data=output,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
